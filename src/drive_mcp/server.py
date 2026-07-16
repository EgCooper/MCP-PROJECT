"""Servidor MCP para Google Drive."""

from __future__ import annotations

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from drive_mcp.drive import DriveClient
    
load_dotenv()

mcp = FastMCP("google-drive")
client = DriveClient()


@mcp.tool()
def list_files(
    folder_id: str = "",
    page_size: int = 25,
    name_contains: str = "",
) -> str:
    """Lista archivos y carpetas en Google Drive.

    Args:
        folder_id: ID de carpeta. Vacío = raíz (Mi unidad).
        page_size: Máximo de resultados (1-100).
        name_contains: Filtro opcional por nombre.
    """
    return client.list_files(
        folder_id=folder_id or None,
        page_size=page_size,
        query=name_contains or None,
    )


@mcp.tool()
def search_files(query: str, page_size: int = 25) -> str:
    """Busca archivos por nombre en todo Google Drive.

    Args:
        query: Texto a buscar en el nombre.
        page_size: Máximo de resultados (1-100).
    """
    return client.search_files(query=query, page_size=page_size)


@mcp.tool()
def get_file_info(file_id: str) -> str:
    """Obtiene metadatos de un archivo o carpeta (nombre, tipo, enlace).

    Args:
        file_id: ID del archivo en Google Drive.
    """
    return client.get_file_metadata(file_id)


@mcp.tool()
def download_file(file_id: str) -> str:
    """Descarga el contenido de un archivo de texto, o exporta Docs/Sheets/Slides.

    Args:
        file_id: ID del archivo a descargar.
    """
    return client.download_file(file_id)


@mcp.tool()
def upload_text_file(
    name: str,
    content: str,
    folder_id: str = "",
) -> str:
    """Sube un archivo de texto nuevo a Google Drive.

    Args:
        name: Nombre del archivo (ej. notas.txt).
        content: Contenido en texto.
        folder_id: Carpeta destino. Vacío = raíz.
    """
    return client.upload_text_file(
        name=name,
        content=content,
        folder_id=folder_id or None,
    )


@mcp.tool()
def update_text_file(file_id: str, content: str) -> str:
    """Actualiza el contenido de un archivo de texto existente.

    Args:
        file_id: ID del archivo a actualizar.
        content: Nuevo contenido.
    """
    return client.update_text_file(file_id=file_id, content=content)


@mcp.tool()
def create_folder(name: str, parent_id: str = "") -> str:
    """Crea una carpeta en Google Drive.

    Args:
        name: Nombre de la carpeta.
        parent_id: Carpeta padre. Vacío = raíz.
    """
    return client.create_folder(name=name, parent_id=parent_id or None)


@mcp.tool()
def move_file(file_id: str, folder_id: str) -> str:
    """Mueve un archivo o carpeta a otra carpeta.

    Args:
        file_id: ID del archivo o carpeta a mover.
        folder_id: ID de la carpeta destino.
    """
    return client.move_file(file_id=file_id, folder_id=folder_id)


@mcp.tool()
def delete_file(file_id: str) -> str:
    """Mueve un archivo o carpeta a la papelera de Google Drive.

    Args:
        file_id: ID del elemento a eliminar.
    """
    return client.delete_file(file_id)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
