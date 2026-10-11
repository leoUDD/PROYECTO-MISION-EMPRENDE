from celery import shared_task


@shared_task
def prueba_celery():
    print(
        "======================================"
    )
    print(
        "CELERY FUNCIONANDO EN SEGUNDO PLANO"
    )
    print(
        "======================================"
    )

    return "OK"

import logging
import requests

from django.utils import timezone

from .models import FotoEquipo, Sesion
from .onedrive_service import (
    obtener_o_crear_carpeta_sesion,
    subir_archivo_onedrive,
)


logger = logging.getLogger(__name__)


def _crear_txt_foto_equipo(registro):
    grupo = registro.grupo

    fecha = timezone.localtime(
        registro.fecha_captura
    )

    integrantes = (
        registro.integrantes_snapshot or []
    )

    lineas = [
        "MISIÓN EMPRENDE",
        "",
        f"Sesión: {registro.sesion.nombre}",
        (
            "Fecha de sesión: "
            f"{fecha.strftime('%d-%m-%Y')}"
        ),
        f"Grupo: {grupo.nombregrupo or 'Sin nombre'}",
        f"ID interno del grupo: {grupo.idgrupo}",
        "",
        "Integrantes:",
    ]

    if integrantes:
        for posicion, integrante in enumerate(
            integrantes,
            start=1,
        ):
            lineas.append(
                f"{posicion}. "
                f"{integrante.get('nombre', '')}"
            )
    else:
        lineas.append(
            "No se encontraron integrantes registrados."
        )

    lineas.extend(
        [
            "",
            (
                "Fotografía tomada: "
                f"{fecha.strftime('%d-%m-%Y %H:%M:%S')}"
            ),
        ]
    )

    return "\n".join(lineas).encode("utf-8")


def _borrar_foto_temporal(registro):
    if not registro.foto_temporal:
        return

    try:
        registro.foto_temporal.delete(
            save=False
        )

        registro.foto_temporal = None

        registro.save(
            update_fields=[
                "foto_temporal",
                "actualizada_en",
            ]
        )

    except Exception:
        logger.exception(
            "No se pudo borrar la foto temporal %s",
            registro.pk,
        )


@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={
        "max_retries": 5,
    },
)
def subir_foto_equipo_onedrive(
    self,
    foto_equipo_id,
):
    registro = (
        FotoEquipo.objects
        .select_related(
            "grupo",
            "sesion",
        )
        .get(pk=foto_equipo_id)
    )

    # La tarea es idempotente.
    if registro.subida_onedrive:
        return {
            "ok": True,
            "ya_subida": True,
        }

    if not registro.foto_temporal:
        raise RuntimeError(
            "La fotografía temporal no existe."
        )

    try:
        fecha = timezone.localtime(
            registro.fecha_captura
        )

        carpeta = obtener_o_crear_carpeta_sesion(
            registro.sesion,
            fecha,
        )

        with registro.foto_temporal.open(
            "rb"
        ) as archivo:
            contenido_foto = archivo.read()

        archivo_foto = subir_archivo_onedrive(
            carpeta_id=carpeta["id"],
            nombre=registro.nombre_archivo,
            contenido=contenido_foto,
            mime_type="image/jpeg",
        )

        nombre_base = (
            registro.nombre_archivo.rsplit(
                ".",
                1,
            )[0]
        )

        nombre_txt = (
            f"{nombre_base} - integrantes.txt"
        )

        contenido_txt = (
            _crear_txt_foto_equipo(registro)
        )

        archivo_txt = subir_archivo_onedrive(
            carpeta_id=carpeta["id"],
            nombre=nombre_txt,
            contenido=contenido_txt,
            mime_type="text/plain",
        )

        registro.onedrive_carpeta_id = (
            carpeta["id"]
        )

        registro.onedrive_foto_id = (
            archivo_foto["id"]
        )

        registro.onedrive_txt_id = (
            archivo_txt["id"]
        )

        registro.subida_onedrive = True
        registro.error_onedrive = ""

        registro.save(
            update_fields=[
                "onedrive_carpeta_id",
                "onedrive_foto_id",
                "onedrive_txt_id",
                "subida_onedrive",
                "error_onedrive",
                "actualizada_en",
            ]
        )

        Sesion.objects.filter(
            pk=registro.sesion_id
        ).update(
            onedrive_carpeta_id=carpeta["id"]
        )

        # Si mientras la tarea trabajaba la sesión
        # llegó a Reflexión, ya podemos borrar local.
        registro.sesion.refresh_from_db(
            fields=["fase_actual"]
        )

        if (
            registro.sesion.fase_actual
            == "reflexion"
        ):
            _borrar_foto_temporal(registro)

        return {
            "ok": True,
            "foto": archivo_foto["name"],
            "txt": archivo_txt["name"],
        }

    except Exception as exc:
        registro.error_onedrive = str(exc)[:2000]
        registro.subida_onedrive = False

        registro.save(
            update_fields=[
                "error_onedrive",
                "subida_onedrive",
                "actualizada_en",
            ]
        )

        raise