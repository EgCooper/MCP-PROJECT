# Google Drive MCP

Servidor MCP en Python para gestionar documentos de **Google Drive** (cuenta Gmail / Google Workspace) desde Cursor.

## Tools

| Tool | Descripción |
|------|-------------|
| `list_files` | Lista archivos/carpetas (raíz o por `folder_id`) |
| `search_files` | Busca por nombre en todo Drive |
| `get_file_info` | Metadatos y enlace web |
| `download_file` | Descarga texto o exporta Docs/Sheets/Slides |
| `upload_text_file` | Sube un archivo de texto |
| `update_text_file` | Actualiza contenido de un archivo |
| `create_folder` | Crea una carpeta |
| `delete_file` | Mueve a la papelera |

Permiso por defecto: lectura **y** escritura (`drive`). Para solo lectura, cambia el scope en `src/drive_mcp/auth.py` a `drive.readonly` y elimina el `token.json` para volver a autorizar.

## 1. Google Cloud

1. Abre [Google Cloud Console](https://console.cloud.google.com/).
2. Crea un proyecto (o usa uno existente).
3. Activa **Google Drive API** (APIs & Services → Library).
4. Configura la pantalla de consentimiento OAuth (External o Internal).
5. Crea credenciales: **APIs & Services → Credentials → Create credentials → OAuth client ID**.
   - Application type: **Desktop app**
6. Descarga el JSON y guárdalo en la raíz del proyecto como `credentials.json`.

Si la app está en modo *Testing*, añade tu Gmail en **Test users**.

## 2. Instalación

```bash
cd MCP-PROJECT
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 3. Primer login (opcional, recomendado)

```bash
python -c "from drive_mcp.auth import get_credentials; get_credentials()"
```

Se abre el navegador, autorizas con tu Gmail y se crea `token.json`.

## 4. Cursor (`mcp.json`)

```json
{
  "mcpServers": {
    "google-drive": {
      "command": "/home/vpinto/Documents/Cooper/Repo2/MCP-PROJECT/.venv/bin/python",
      "args": ["-m", "drive_mcp.server"],
      "cwd": "/home/vpinto/Documents/Cooper/Repo2/MCP-PROJECT",
      "env": {
        "GOOGLE_CREDENTIALS_PATH": "/home/vpinto/Documents/Cooper/Repo2/MCP-PROJECT/credentials.json",
        "GOOGLE_TOKEN_PATH": "/home/vpinto/Documents/Cooper/Repo2/MCP-PROJECT/token.json"
      }
    }
  }
}
```

Ajusta las rutas si tu proyecto está en otra ubicación.

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `GOOGLE_CREDENTIALS_PATH` | Ruta a `credentials.json` (OAuth client) |
| `GOOGLE_TOKEN_PATH` | Ruta donde se guarda `token.json` |

## Notas

- `credentials.json` y `token.json` **no** se suben a git.
- La descarga por MCP está limitada a ~2 MiB y a contenido texto (o export de Docs).
- El borrado envía a papelera; no elimina de forma permanente.
