"""Autenticación OAuth2 con Google (cuenta Gmail / Google Workspace)."""

from __future__ import annotations

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

# Lectura/escritura. Para solo lectura usa:
# SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
SCOPES = ["https://www.googleapis.com/auth/drive"]

_DEFAULT_DIR = Path(__file__).resolve().parents[2]


def _resolve_path(env_var: str, default_name: str) -> Path:
    value = os.getenv(env_var)
    if value:
        return Path(value).expanduser().resolve()
    return (_DEFAULT_DIR / default_name).resolve()


def get_credentials() -> Credentials:
    """Obtiene credenciales OAuth; abre el navegador en el primer login."""
    credentials_path = _resolve_path("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    token_path = _resolve_path("GOOGLE_TOKEN_PATH", "token.json")

    if not credentials_path.exists():
        raise FileNotFoundError(
            f"No se encontró {credentials_path}. "
            "Descarga credentials.json desde Google Cloud Console "
            "(APIs & Services → Credentials → OAuth client → Desktop app)."
        )

    creds: Credentials | None = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            # local_server abre el navegador; útil en el primer arranque del MCP
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds


def build_drive_service() -> Resource:
    """Construye el cliente de Google Drive API v3."""
    return build("drive", "v3", credentials=get_credentials(), cache_discovery=False)
