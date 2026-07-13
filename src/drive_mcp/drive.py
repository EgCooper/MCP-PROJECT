"""Cliente de Google Drive API."""

from __future__ import annotations

import io
import json
from typing import Any

from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from drive_mcp.auth import build_drive_service

# Tipos de Google Docs exportables a texto / formatos útiles
_EXPORT_MIME: dict[str, str] = {
    "application/vnd.google-apps.document": "text/plain",
    "application/vnd.google-apps.spreadsheet": "text/csv",
    "application/vnd.google-apps.presentation": "text/plain",
}

_FOLDER_MIME = "application/vnd.google-apps.folder"
_MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024  # 2 MiB para respuestas MCP


class DriveClient:
    def __init__(self) -> None:
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = build_drive_service()
        return self._service

    def list_files(
        self,
        folder_id: str | None = None,
        page_size: int = 25,
        query: str | None = None,
    ) -> str:
        """Lista archivos. Por defecto usa 'root' (Mi unidad)."""
        page_size = max(1, min(page_size, 100))
        parts = ["trashed = false"]
        parent = folder_id or "root"
        parts.append(f"'{parent}' in parents")
        if query:
            safe = query.replace("\\", "\\\\").replace("'", "\\'")
            parts.append(f"name contains '{safe}'")

        q = " and ".join(parts)
        result = (
            self.service.files()
            .list(
                q=q,
                pageSize=page_size,
                fields="files(id, name, mimeType, modifiedTime, size, parents)",
                orderBy="folder,name",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        files = result.get("files", [])
        return json.dumps({"count": len(files), "files": files}, indent=2)

    def search_files(self, query: str, page_size: int = 25) -> str:
        """Busca por nombre en todo el Drive (no solo una carpeta)."""
        page_size = max(1, min(page_size, 100))
        safe = query.replace("\\", "\\\\").replace("'", "\\'")
        q = f"trashed = false and name contains '{safe}'"
        result = (
            self.service.files()
            .list(
                q=q,
                pageSize=page_size,
                fields="files(id, name, mimeType, modifiedTime, size, parents)",
                orderBy="modifiedTime desc",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        files = result.get("files", [])
        return json.dumps({"count": len(files), "files": files}, indent=2)

    def get_file_metadata(self, file_id: str) -> str:
        meta = (
            self.service.files()
            .get(
                fileId=file_id,
                fields="id, name, mimeType, modifiedTime, size, parents, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )
        return json.dumps(meta, indent=2)

    def download_file(self, file_id: str) -> str:
        """Descarga contenido de texto o exporta Docs/Sheets/Slides."""
        meta = (
            self.service.files()
            .get(
                fileId=file_id,
                fields="id, name, mimeType, size",
                supportsAllDrives=True,
            )
            .execute()
        )
        mime = meta.get("mimeType", "")
        name = meta.get("name", file_id)

        if mime == _FOLDER_MIME:
            return json.dumps({"error": "Es una carpeta, no un archivo.", "id": file_id})

        buffer = io.BytesIO()
        if mime in _EXPORT_MIME:
            request = self.service.files().export_media(
                fileId=file_id, mimeType=_EXPORT_MIME[mime]
            )
        else:
            request = self.service.files().get_media(fileId=file_id)

        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        data = buffer.getvalue()
        if len(data) > _MAX_DOWNLOAD_BYTES:
            return json.dumps(
                {
                    "error": "Archivo demasiado grande para devolverlo por MCP.",
                    "id": file_id,
                    "name": name,
                    "size": len(data),
                    "max_bytes": _MAX_DOWNLOAD_BYTES,
                }
            )

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return json.dumps(
                {
                    "error": "Contenido binario; no se puede devolver como texto.",
                    "id": file_id,
                    "name": name,
                    "mimeType": mime,
                    "size": len(data),
                }
            )

        return json.dumps(
            {"id": file_id, "name": name, "mimeType": mime, "content": text},
            indent=2,
        )

    def upload_text_file(
        self,
        name: str,
        content: str,
        folder_id: str | None = None,
        mime_type: str = "text/plain",
    ) -> str:
        """Crea un archivo de texto. Si ya existe uno con el mismo nombre
        en la carpeta, crea otro (Drive permite duplicados)."""
        metadata: dict[str, Any] = {"name": name}
        if folder_id:
            metadata["parents"] = [folder_id]

        media = MediaIoBaseUpload(
            io.BytesIO(content.encode("utf-8")),
            mimetype=mime_type,
            resumable=False,
        )
        created = (
            self.service.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id, name, mimeType, parents, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )
        return json.dumps({"status": "created", "file": created}, indent=2)

    def update_text_file(self, file_id: str, content: str) -> str:
        """Sobrescribe el contenido de un archivo existente."""
        media = MediaIoBaseUpload(
            io.BytesIO(content.encode("utf-8")),
            mimetype="text/plain",
            resumable=False,
        )
        updated = (
            self.service.files()
            .update(
                fileId=file_id,
                media_body=media,
                fields="id, name, mimeType, modifiedTime",
                supportsAllDrives=True,
            )
            .execute()
        )
        return json.dumps({"status": "updated", "file": updated}, indent=2)

    def create_folder(self, name: str, parent_id: str | None = None) -> str:
        metadata: dict[str, Any] = {
            "name": name,
            "mimeType": _FOLDER_MIME,
        }
        if parent_id:
            metadata["parents"] = [parent_id]

        created = (
            self.service.files()
            .create(
                body=metadata,
                fields="id, name, mimeType, parents, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )
        return json.dumps({"status": "created", "folder": created}, indent=2)

    def move_file(self, file_id: str, folder_id: str) -> str:
        """Mueve un archivo o carpeta a otra carpeta."""
        meta = (
            self.service.files()
            .get(
                fileId=file_id,
                fields="id, name, parents, mimeType",
                supportsAllDrives=True,
            )
            .execute()
        )
        previous_parents = ",".join(meta.get("parents", []))
        updated = (
            self.service.files()
            .update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields="id, name, parents, mimeType, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )
        return json.dumps({"status": "moved", "file": updated}, indent=2)

    def delete_file(self, file_id: str) -> str:
        """Mueve a la papelera (no elimina de forma permanente)."""
        self.service.files().update(
            fileId=file_id,
            body={"trashed": True},
            supportsAllDrives=True,
        ).execute()
        return json.dumps({"status": "trashed", "id": file_id})
