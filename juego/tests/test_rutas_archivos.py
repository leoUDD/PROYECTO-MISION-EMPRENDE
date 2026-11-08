# juego/tests/test_rutas_archivos.py
"""STATIC_ROOT y MEDIA_ROOT se pueden mover desde el .env sin cambiar el default."""

import importlib.util
import os
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase

RUTA_SETTINGS = Path(__file__).resolve().parents[2] / "config" / "settings.py"


def cargar_settings(**variables):
    """Carga una copia aislada de config/settings.py con estas variables."""
    entorno = {"DJANGO_DEBUG": "True", **variables}
    with mock.patch.dict(os.environ, entorno):
        for nombre in ("DJANGO_STATIC_ROOT", "DJANGO_MEDIA_ROOT"):
            if nombre not in variables:
                os.environ.pop(nombre, None)
        with mock.patch("dotenv.load_dotenv"):
            spec = importlib.util.spec_from_file_location("settings_prueba_rutas", RUTA_SETTINGS)
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
    return modulo


class RutasDeArchivosTests(SimpleTestCase):
    def test_sin_variables_quedan_dentro_del_proyecto(self):
        s = cargar_settings()
        self.assertEqual(s.STATIC_ROOT, s.BASE_DIR / "staticfiles")
        self.assertEqual(s.MEDIA_ROOT, s.BASE_DIR / "media")

    def test_variables_del_servidor(self):
        s = cargar_settings(
            DJANGO_STATIC_ROOT="/srv/app/staticfiles/static",
            DJANGO_MEDIA_ROOT="/home/misionemprende/media",
        )
        self.assertEqual(s.STATIC_ROOT, Path("/srv/app/staticfiles/static"))
        self.assertEqual(s.MEDIA_ROOT, Path("/home/misionemprende/media"))
        self.assertEqual(s.MEDIA_URL, "/media/")

    def test_variable_vacia_usa_el_default(self):
        s = cargar_settings(DJANGO_STATIC_ROOT="  ", DJANGO_MEDIA_ROOT="")
        self.assertEqual(s.STATIC_ROOT, s.BASE_DIR / "staticfiles")
        self.assertEqual(s.MEDIA_ROOT, s.BASE_DIR / "media")
