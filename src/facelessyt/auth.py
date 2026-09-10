"""OAuth con la cuenta de Google del canal.

La clave de API sirve para leer datos publicos. Todo lo demas —subir un video,
cambiar la marca del canal, leer CTR y retencion— requiere autorizacion del
dueno del canal, y eso es OAuth.

El consentimiento se da UNA vez en el navegador. A partir de ahi queda un
token.json con un refresh token que se renueva solo.
"""

from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import ROOT

CREDENTIALS = ROOT / "credentials.json"
TOKEN = ROOT / "token.json"

# Se piden juntos porque cambiar de scopes obliga a repetir el consentimiento.
# Mejor pedir de una vez todo lo que el proyecto va a necesitar.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",       # subir videos
    "https://www.googleapis.com/auth/youtube",              # miniatura, marca del canal
    "https://www.googleapis.com/auth/yt-analytics.readonly",  # CTR y retencion
]


class AuthError(RuntimeError):
    pass


def credentials(*, interactive: bool = True) -> Credentials:
    """Devuelve credenciales validas, renovando o pidiendo consentimiento."""
    if not CREDENTIALS.exists():
        raise AuthError(
            f"Falta {CREDENTIALS}.\n"
            "Google Cloud -> Credenciales -> ID de cliente de OAuth -> "
            "Aplicacion de escritorio -> descargar JSON."
        )

    creds: Credentials | None = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json(), encoding="utf-8")
        return creds

    if not interactive:
        raise AuthError(
            "No hay token valido y no se puede pedir consentimiento en modo no interactivo.\n"
            "Ejecuta: python -m facelessyt auth"
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS), SCOPES)
    # port=0 deja que el sistema elija un puerto libre para el callback.
    creds = flow.run_local_server(
        port=0,
        prompt="consent",
        authorization_prompt_message="Abre esta URL para autorizar:\n{url}\n",
        success_message="Listo. Puedes cerrar esta pestana y volver a la terminal.",
    )
    TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return creds


def youtube(*, interactive: bool = True):
    """Cliente de la YouTube Data API autenticado como el dueno del canal."""
    return build("youtube", "v3", credentials=credentials(interactive=interactive))


def analytics(*, interactive: bool = True):
    """Cliente de la YouTube Analytics API (CTR, retencion, fuentes de trafico)."""
    return build("youtubeAnalytics", "v2", credentials=credentials(interactive=interactive))
