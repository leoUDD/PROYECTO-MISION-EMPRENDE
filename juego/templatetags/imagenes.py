"""Resuelve la imagen de una temática sin romper la pantalla.

La ruta de la imagen vive en la base de datos, así que puede apuntar a un
archivo que ya no existe. Con el manifiesto de producción, {% static %} lanza
ValueError en ese caso y la página entera responde 500; por eso las temáticas
pasan por este filtro en vez de usar {% static %} directamente.
"""

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.exceptions import SuspiciousFileOperation
from django.templatetags.static import static

register = template.Library()

IMAGEN_GENERICA = "images/logo_registro.webp"


def _url_estatica(ruta):
    """URL del archivo estático, o None si no existe."""
    if not ruta:
        return None

    try:
        if not finders.find(ruta):
            return None
        return static(ruta)
    except (ValueError, SuspiciousFileOperation):
        return None


def _campo(tematica, nombre):
    """Las vistas entregan modelos (juego) o diccionarios (panel admin)."""
    if isinstance(tematica, dict):
        return tematica.get(nombre)
    return getattr(tematica, nombre, None)


@register.filter
def imagen_tematica(tematica):
    imagen = (_campo(tematica, "image") or "").strip()
    slug = _campo(tematica, "slug") or ""

    if imagen.startswith(settings.MEDIA_URL):
        return imagen

    return (
        _url_estatica(imagen)
        or _url_estatica(f"images/{slug}.webp" if slug else "")
        or static(IMAGEN_GENERICA)
    )
