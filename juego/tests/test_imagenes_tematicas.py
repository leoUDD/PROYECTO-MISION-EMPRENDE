"""Una imagen de temática faltante no debe tumbar la pantalla.

La suite corre sin manifiesto, donde {% static %} nunca falla. El ValueError
del manifiesto de producción se simula para cubrir ese camino.
"""

from unittest.mock import patch

from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.urls import reverse

from juego.models import Tematica
from juego.tematicas_data import THEMES
from juego.templatetags.imagenes import IMAGEN_GENERICA, imagen_tematica

from .base import BaseJuegoTestCase


class FiltroImagenTematicaTests(BaseJuegoTestCase):
    def test_imagen_de_media_se_usa_tal_cual(self):
        ruta = "/media/tematicas/propia.webp"
        self.assertEqual(imagen_tematica({"slug": "salud", "image": ruta}), ruta)

    def test_ruta_estatica_existente_se_respeta(self):
        tema = {"slug": "otra", "image": "images/educacion.webp"}
        self.assertEqual(imagen_tematica(tema), static("images/educacion.webp"))

    def test_ruta_borrada_usa_la_imagen_del_slug(self):
        tema = {"slug": "salud", "image": "images/tematicas/salud.png"}
        self.assertEqual(imagen_tematica(tema), static("images/salud.webp"))

    def test_imagen_vacia_usa_la_imagen_del_slug(self):
        for vacia in ("", None):
            tema = {"slug": "salud", "image": vacia}
            self.assertEqual(imagen_tematica(tema), static("images/salud.webp"))

    def test_slug_sin_imagen_usa_la_generica(self):
        tema = {"slug": "tema-nuevo", "image": "images/no-existe.png"}
        self.assertEqual(imagen_tematica(tema), static(IMAGEN_GENERICA))

    def test_ruta_fuera_de_estaticos_usa_la_generica(self):
        tema = {"slug": "", "image": "../../settings.py"}
        self.assertEqual(imagen_tematica(tema), static(IMAGEN_GENERICA))

    def test_acepta_modelos_ademas_de_diccionarios(self):
        tema = Tematica(slug="salud", title="Salud", image="")
        self.assertEqual(imagen_tematica(tema), static("images/salud.webp"))

    def test_error_del_manifiesto_no_se_propaga(self):
        reales = static

        def manifiesto(ruta):
            if ruta == "images/educacion.webp":
                raise ValueError("Missing staticfiles manifest entry")
            return reales(ruta)

        tema = {"slug": "salud", "image": "images/educacion.webp"}
        with patch("juego.templatetags.imagenes.static", side_effect=manifiesto):
            self.assertEqual(imagen_tematica(tema), reales("images/salud.webp"))


class PantallasTematicasTests(BaseJuegoTestCase):
    def setUp(self):
        super().setUp()
        Tematica.objects.create(slug="salud", title="Salud", hero="h", image="images/tematicas/salud.png")
        Tematica.objects.create(slug="tema-nuevo", title="Nuevo", hero="h", image="")

    def test_pantalla_del_juego_con_imagenes_rotas(self):
        self.set_fase("f2_tematicas")
        self.login_alumno()
        respuesta = self.client.get(reverse("tematicas"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, static("images/salud.webp"))
        self.assertContains(respuesta, static(IMAGEN_GENERICA))

    def test_panel_admin_con_imagenes_rotas(self):
        self.login_admin()
        respuesta = self.client.get(reverse("admin_tematicas"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, static("images/salud.webp"))


class DatosTematicasTests(BaseJuegoTestCase):
    def test_las_imagenes_de_tematicas_data_existen(self):
        for slug, datos in THEMES.items():
            self.assertTrue(finders.find(datos["image"]), f"{slug}: falta {datos['image']}")
