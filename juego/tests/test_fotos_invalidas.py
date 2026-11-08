"""Un archivo que no se puede leer debe dar un mensaje claro, no un error 500."""

import io
import shutil
import tempfile

from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image

from juego.models import Desafio, Grupo, Tematica
from juego.views import MENSAJE_FOTO_LEGO_INVALIDA, MENSAJE_IMAGEN_INVALIDA

from .base import BaseJuegoTestCase

AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
MEDIA_TEMPORAL = tempfile.mkdtemp()


def jpeg_bytes():
    salida = io.BytesIO()
    Image.effect_noise((200, 200), 80).convert("RGB").save(salida, "JPEG")
    return salida.getvalue()


def archivo(contenido, nombre="foto.jpg", tipo="image/jpeg"):
    return SimpleUploadedFile(nombre, contenido, content_type=tipo)


def archivos_invalidos():
    return {
        "no es imagen": archivo(b"esto no es una imagen"),
        "heic": archivo(b"\x00\x00\x00\x18ftypheic" + b"\x00" * 100, "IMG.HEIC", "image/heic"),
        "truncado": archivo(jpeg_bytes()[:300]),
    }


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class FotosBase(BaseJuegoTestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)


class FotoLegoInvalidaTests(FotosBase):
    def setUp(self):
        super().setUp()
        self.set_fase("f3_lego")
        self.login_alumno()

    def test_archivos_invalidos_dan_mensaje_y_no_marcan_listo(self):
        for caso, invalido in archivos_invalidos().items():
            with self.subTest(caso):
                respuesta = self.client.post(reverse("lego"), {"foto_lego": invalido}, **AJAX)

                self.assertEqual(respuesta.status_code, 400)
                self.assertEqual(respuesta.json()["error"], MENSAJE_FOTO_LEGO_INVALIDA)

                grupo = Grupo.objects.get(pk=self.grupo.pk)
                self.assertFalse(grupo.listo_f3_lego)
                self.assertFalse(grupo.foto_lego)

    def test_sin_ajax_vuelve_a_la_pantalla_con_el_mensaje(self):
        respuesta = self.client.post(reverse("lego"), {"foto_lego": archivo(b"nada")})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(MENSAJE_FOTO_LEGO_INVALIDA, [str(m) for m in get_messages(respuesta.wsgi_request)])

    def test_puede_reintentar_con_una_foto_valida(self):
        self.client.post(reverse("lego"), {"foto_lego": archivo(b"nada")}, **AJAX)

        respuesta = self.client.post(reverse("lego"), {"foto_lego": archivo(jpeg_bytes())}, **AJAX)

        self.assertEqual(respuesta.status_code, 200)
        grupo = Grupo.objects.get(pk=self.grupo.pk)
        self.assertTrue(grupo.listo_f3_lego)
        self.assertTrue(grupo.foto_lego.name.endswith(".webp"))


class ImagenAdminInvalidaTests(FotosBase):
    def setUp(self):
        super().setUp()
        self.login_admin()
        self.tematica = Tematica.objects.create(slug="salud", title="Salud", hero="h", image="")
        self.desafio = Desafio.objects.create(nombredesafio="Original", tematica=self.tematica)

    def mensajes(self, respuesta):
        return " ".join(str(m) for m in get_messages(respuesta.wsgi_request))

    def test_editar_desafio_no_guarda_cambios(self):
        respuesta = self.client.post(reverse("admin_desafios"), {
            "accion": "editar_desafio",
            "desafio_id": self.desafio.pk,
            "nombre": "Cambiado",
            "imagen_desafio": archivo(b"nada"),
        })

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(MENSAJE_IMAGEN_INVALIDA, self.mensajes(respuesta))
        self.assertEqual(Desafio.objects.get(pk=self.desafio.pk).nombredesafio, "Original")

    def test_crear_desafio_queda_sin_imagen_y_avisa(self):
        respuesta = self.client.post(reverse("admin_desafios"), {
            "accion": "crear_desafio",
            "nombre": "Nuevo",
            "tematica_id": self.tematica.pk,
            "imagen_desafio": archivo(b"nada"),
        })

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("sin imagen", self.mensajes(respuesta))
        self.assertFalse(Desafio.objects.get(nombredesafio="Nuevo").imagen_desafio)

    def test_crear_tematica_no_la_crea(self):
        respuesta = self.client.post(reverse("admin_tematicas"), {
            "accion": "crear_tematica",
            "title": "Nueva",
            "hero": "h",
            "image_file": archivo(b"nada"),
        })

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(MENSAJE_IMAGEN_INVALIDA, self.mensajes(respuesta))
        self.assertFalse(Tematica.objects.filter(title="Nueva").exists())

    def test_editar_tematica_no_guarda_cambios(self):
        respuesta = self.client.post(reverse("admin_tematicas"), {
            "accion": "editar_tematica",
            "tematica_id": self.tematica.pk,
            "title": "Cambiada",
            "hero": "h",
            "image_file": archivo(b"nada"),
        })

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(MENSAJE_IMAGEN_INVALIDA, self.mensajes(respuesta))
        self.assertEqual(Tematica.objects.get(pk=self.tematica.pk).title, "Salud")
