#!/usr/bin/env python3
"""Organiza archivos sueltos en la raíz de Google Drive."""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Usar el cliente del MCP
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from drive_mcp.auth import build_drive_service  # noqa: E402

FOLDER_MIME = "application/vnd.google-apps.folder"
ROOT = "root"

# Carpetas existentes en raíz (IDs conocidos)
EXISTING = {
    "Jala University": "1yAevGqBzSUnzW7Vxrjggqz6h0stSCBWe",
    "Vídeos de programacion": "1Bx8476PopuNt3C-8XVbdfjKiE8dnu-sh",
    "Colab Notebooks": "1Lprafx3M-qs1s2mvvg0uYhOvwayh9VmE",
    "Diagramas": "1nBd8ULm5DV6QOIGohFQhgIyNipF3DoPx",
    "Edits Valo": "1VObd5gs-Z2J9kP2D6_D5IKeb5YsgEm0z",
    "Ig fotos": "1ZIBWk8YPI2fI_T0lLVjQXzUU8EmRx77L",
    "Jala": "1G2g2f_w6ZmYsNGwsmbotVj2uOosqk-gZ",
    "Mentorias": "1Atj5hDOpuCRqFuKnEAXlfP2ToP7sMdEH",
    "ProyectoAlgebraLineal": "1Q62bjT79YW78hiPFUcJySIvmNfAEnHCK",
    "Seguridad Informatica Taller": "1NwQR2-0fW-8DSu7YlZCXEC7bk_a4n06-",
    "Tarea4.4": "1EyWNk6Z2LJQBFcr6ib_6paG_PwSoDNCH",
    "Software V": "1DS7d6WJaIJciUXC7Gbbof0Ec-u9LsvQk",
}


def list_all_in_folder(service, folder_id: str) -> list[dict]:
    items: list[dict] = []
    page_token = None
    while True:
        result = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, parents)",
                orderBy="folder,name",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageToken=page_token,
            )
            .execute()
        )
        items.extend(result.get("files", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    return items


def ensure_folder(service, name: str, parent_id: str, cache: dict) -> str:
    key = f"{parent_id}:{name}"
    if key in cache:
        return cache[key]
    for item in list_all_in_folder(service, parent_id):
        if item["mimeType"] == FOLDER_MIME and item["name"] == name:
            cache[key] = item["id"]
            return item["id"]
    created = (
        service.files()
        .create(
            body={"name": name, "mimeType": FOLDER_MIME, "parents": [parent_id]},
            fields="id, name",
            supportsAllDrives=True,
        )
        .execute()
    )
    cache[key] = created["id"]
    print(f"  + Carpeta creada: {name}")
    return created["id"]


def move_item(service, file_id: str, dest_folder_id: str, current_parents: list[str]) -> None:
    service.files().update(
        fileId=file_id,
        addParents=dest_folder_id,
        removeParents=",".join(current_parents),
        supportsAllDrives=True,
        fields="id",
    ).execute()


def classify(name: str, mime: str) -> str | None:
    """Devuelve la ruta destino relativa: 'Jala University/Laboratorios' etc."""
    lower = name.lower()

    if mime == FOLDER_MIME:
        uni_folders = {
            "tarea4.4",
            "proyectoalgebralineal",
            "seguridad informatica taller",
            "software v",
        }
        if lower in uni_folders:
            if lower == "software v":
                return "Jala University/Software V"
            if lower == "tarea4.4":
                return "Jala University/Tareas"
            if lower == "proyectoalgebralineal":
                return "Jala University/Proyectos"
            if lower == "seguridad informatica taller":
                return "Jala University/Cursos"
        return None  # mantener carpetas personales en raíz

    if "sin título" in lower or "sin titulo" in lower:
        return "Borradores"

    if mime == "application/vnd.google-apps.presentation":
        return "Presentaciones"

    if lower.endswith(".zip") or "backup" in lower:
        return "Backups"

    if re.search(r"ticket|cotizacion|cotización|ach ", lower):
        return "Trabajo"

    if re.search(r"\bcv\b|curriculum|pintomoravictorangelcv|ci pinto|fotografia estudiante", lower):
        return "Personal"

    if re.search(r"margot|angel_molle", lower):
        return "Familia"

    if re.search(r"monografia|monografía|ddl yss|ddl-yss|introducción de monografía|introduccion de monografia", lower):
        return "Jala University/Monografías"

    if re.search(r"debate|defensa", lower):
        return "Jala University/Debates"

    if re.search(r"laboratorio|lab#|lab semana|labsemana|laboratorio-|laboratorio#", lower):
        return "Jala University/Laboratorios"

    if re.search(r"tarea|actividad|pintomoravictorangel", lower):
        return "Jala University/Tareas"

    if re.search(r"capstone|base de datos|modelorelacional|scrum|integración|integracion|objetivos|dailys|expo quality|guion|guión|cartas?$", lower):
        return "Jala University/Proyectos"

    if mime.startswith("video/"):
        return "Vídeos de programacion"

    if mime == "application/vnd.google-apps.form":
        return "Borradores"

    if re.search(r"pinto_mora_victor_angel|^pintomoravictorangel$", lower):
        return "Personal"

    return "Jala University/Otros"


def resolve_path(service, path: str, cache: dict) -> str:
    parts = path.split("/")
    parent = ROOT
    for part in parts:
        if part in EXISTING and parent == ROOT:
            parent = EXISTING[part]
            continue
        parent = ensure_folder(service, part, parent, cache)
    return parent


def main() -> None:
    service = build_drive_service()
    cache: dict[str, str] = {}
    root_items = list_all_in_folder(service, ROOT)

    folders_at_root = [i for i in root_items if i["mimeType"] == FOLDER_MIME]
    files_at_root = [i for i in root_items if i["mimeType"] != FOLDER_MIME]

    print(f"Raíz: {len(folders_at_root)} carpetas, {len(files_at_root)} archivos sueltos\n")

    moved = 0
    skipped = 0

    for item in root_items:
        name = item["name"]
        mime = item["mimeType"]
        item_id = item["id"]
        parents = item.get("parents", [ROOT])

        dest_path = classify(name, mime)
        if dest_path is None:
            skipped += 1
            continue

        dest_id = resolve_path(service, dest_path, cache)
        move_item(service, item_id, dest_id, parents)
        moved += 1
        print(f"  → {name}  ==>  {dest_path}")

    print(f"\nListo: {moved} elementos movidos, {skipped} carpetas de organización en raíz.")

    remaining = list_all_in_folder(service, ROOT)
    loose_files = [f for f in remaining if f["mimeType"] != FOLDER_MIME]
    print(f"Archivos sueltos restantes en raíz: {len(loose_files)}")
    for f in loose_files:
        print(f"  - {f['name']}")


if __name__ == "__main__":
    main()
