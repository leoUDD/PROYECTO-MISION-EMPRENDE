from __future__ import annotations

from django.conf import settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"

FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


def construir_servicio_drive():
    """
    Construye un cliente autenticado para Google Drive.

    Usa el refresh token para obtener automáticamente
    un access token válido.
    """

    configuracion = {
        "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
        "GOOGLE_CLIENT_SECRET": settings.GOOGLE_CLIENT_SECRET,
        "GOOGLE_REFRESH_TOKEN": settings.GOOGLE_REFRESH_TOKEN,
    }

    faltantes = [
        nombre
        for nombre, valor in configuracion.items()
        if not valor
    ]

    if faltantes:
        raise RuntimeError(
            "Faltan variables de Google Drive: "
            + ", ".join(faltantes)
        )

    credenciales = Credentials(
        token=None,
        refresh_token=settings.GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=[DRIVE_SCOPE],
    )

    credenciales.refresh(Request())

    return build(
        "drive",
        "v3",
        credentials=credenciales,
        cache_discovery=False,
    )