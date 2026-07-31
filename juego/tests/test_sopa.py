# juego/tests/test_sopa.py
"""Sopa de letras: bonus, idempotencia y registro de palabras."""

from django.urls import reverse
from django.utils import timezone

from juego.models import Grupo, PalabraSopaEncontrada

from .base import BaseJuegoTestCase


class SopaCompletadaTests(BaseJuegoTestCase):
    def setUp(self):
        super().setUp()
        self.set_fase(
            "f1_sopa",
            timer_corriendo=True,
            timer_inicio_at=timezone.now(),
        )

    def test_primer_equipo_recibe_bonus_5(self):
        self.login_alumno(self.grupo)
        respuesta = self.post_json(reverse("sopa_completada"))

        datos = respuesta.json()
        self.assertTrue(datos["ok"])
        self.assertTrue(datos["primer_equipo"])
        self.assertEqual(datos["bonus_otorgado"], 5)

        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.tokensgrupo, 15)
        self.assertTrue(self.grupo.sopa_ganada)
        self.assertIsNotNone(self.grupo.sopa_completada_en)

    def test_segundo_equipo_recibe_bonus_3(self):
        otro = self.grupos[1]
        otro.sopa_ganada = True
        otro.save(update_fields=["sopa_ganada"])

        self.login_alumno(self.grupo)
        datos = self.post_json(reverse("sopa_completada")).json()

        self.assertFalse(datos["primer_equipo"])
        self.assertEqual(datos["bonus_otorgado"], 3)

    def test_doble_envio_no_duplica_tokens(self):
        self.login_alumno(self.grupo)
        self.post_json(reverse("sopa_completada"))
        datos = self.post_json(reverse("sopa_completada")).json()

        self.assertTrue(datos["ya_completada"])
        self.assertEqual(datos["bonus_otorgado"], 0)

        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.tokensgrupo, 15)

    def test_fuera_de_fase_devuelve_409(self):
        self.set_fase("f2_tematicas")
        self.login_alumno(self.grupo)
        respuesta = self.post_json(reverse("sopa_completada"))
        self.assertEqual(respuesta.status_code, 409)

    def test_sin_sesion_devuelve_403(self):
        respuesta = self.post_json(reverse("sopa_completada"))
        self.assertEqual(respuesta.status_code, 403)


class RegistrarPalabraTests(BaseJuegoTestCase):
    def setUp(self):
        super().setUp()
        self.set_fase("f1_sopa")
        self.login_alumno(self.grupo)

    def test_palabra_nueva_suma_un_token(self):
        datos = self.post_json(reverse("registrar_palabra_sopa"), {"palabra": "equipo"}).json()

        self.assertTrue(datos["ok"])
        self.assertTrue(datos["nueva"])

        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.tokensgrupo, 11)
        self.assertTrue(
            PalabraSopaEncontrada.objects.filter(
                grupo=self.grupo, palabra="EQUIPO"
            ).exists()
        )

    def test_palabra_repetida_no_suma(self):
        self.post_json(reverse("registrar_palabra_sopa"), {"palabra": "equipo"})
        datos = self.post_json(reverse("registrar_palabra_sopa"), {"palabra": "EQUIPO"}).json()

        self.assertFalse(datos["nueva"])
        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.tokensgrupo, 11)

    def test_palabra_vacia_es_rechazada(self):
        respuesta = self.post_json(reverse("registrar_palabra_sopa"), {"palabra": "  "})
        self.assertEqual(respuesta.status_code, 400)

    def test_tokens_null_no_se_pierde_la_suma(self):
        """Regresión: F("tokensgrupo") + 1 con NULL dejaba NULL. El fix usa Coalesce."""
        Grupo.objects.filter(pk=self.grupo.pk).update(tokensgrupo=None)

        self.post_json(reverse("registrar_palabra_sopa"), {"palabra": "mision"})

        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.tokensgrupo, 1)
