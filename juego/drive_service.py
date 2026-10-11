from __future__ import annotations

import io
import re

from django.conf import settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"

FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


def construir_servicio_drive():
    """
    Construye un cliente autenticado para Google Drive
    usando el refresh token almacenado en .env.
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


def nombre_seguro(nombre: str) -> str:
    """
    Limpia caracteres problemáticos para nombres de carpetas
    y archivos.
    """

    nombre = str(nombre or "").strip()

    nombre = re.sub(
        r'[\\/:*?"<>|]+',
        "-",
        nombre,
    )

    nombre = re.sub(
        r"\s+",
        " ",
        nombre,
    ).strip(" .")

    return nombre or "Sin nombre"


def escapar_consulta_drive(valor: str) -> str:
    """
    Escapa caracteres para búsquedas mediante el parámetro q.
    """

    return (
        str(valor)
        .replace("\\", "\\\\")
        .replace("'", "\\'")
    )


def buscar_o_crear_carpeta(
    servicio,
    nombre: str,
    carpeta_padre_id: str,
) -> str:
    """
    Busca una carpeta por nombre dentro de una carpeta padre.
    Si no existe, la crea.
    """

    nombre = nombre_seguro(nombre)

    nombre_consulta = escapar_consulta_drive(nombre)
    padre_consulta = escapar_consulta_drive(carpeta_padre_id)

    consulta = (
        f"name = '{nombre_consulta}' and "
        f"mimeType = '{FOLDER_MIME_TYPE}' and "
        f"'{padre_consulta}' in parents and "
        "trashed = false"
    )

    resultado = servicio.files().list(
        q=consulta,
        spaces="drive",
        fields="files(id, name)",
        pageSize=10,
    ).execute()

    carpetas = resultado.get("files", [])

    if carpetas:
        return carpetas[0]["id"]

    carpeta = servicio.files().create(
        body={
            "name": nombre,
            "mimeType": FOLDER_MIME_TYPE,
            "parents": [carpeta_padre_id],
        },
        fields="id, name",
    ).execute()

    return carpeta["id"]


def subir_o_reemplazar_archivo(
    servicio,
    *,
    nombre: str,
    contenido: bytes,
    mime_type: str,
    carpeta_id: str,
) -> dict:
    """
    Sube un archivo a Drive.

    Si existe un archivo con el mismo nombre dentro de la misma
    carpeta, reemplaza su contenido en vez de crear un duplicado.
    """

    nombre = nombre_seguro(nombre)

    nombre_consulta = escapar_consulta_drive(nombre)
    carpeta_consulta = escapar_consulta_drive(carpeta_id)

    consulta = (
        f"name = '{nombre_consulta}' and "
        f"'{carpeta_consulta}' in parents and "
        "trashed = false"
    )

    resultado = servicio.files().list(
        q=consulta,
        spaces="drive",
        fields="files(id, name)",
        pageSize=1,
    ).execute()

    existentes = resultado.get("files", [])

    media = MediaIoBaseUpload(
        io.BytesIO(contenido),
        mimetype=mime_type,
        resumable=False,
    )

    campos = "id, name, webViewLink"

    if existentes:
        return servicio.files().update(
            fileId=existentes[0]["id"],
            media_body=media,
            fields=campos,
        ).execute()

    return servicio.files().create(
        body={
            "name": nombre,
            "parents": [carpeta_id],
        },
        media_body=media,
        fields=campos,
    ).execute()