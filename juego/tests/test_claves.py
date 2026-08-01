# juego/tests/test_claves.py
"""Robustez, generación y restablecimiento de claves de profesor."""

import re

from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse

from juego.auth import errores_de_clave, generar_clave_legible, verificar_clave_profesor
from juego.models import Profesor

from .base import BaseJuegoTestCase, crear_profesor


class GeneradorDeClavesTests(BaseJuegoTestCase):
    FORMATO = re.compile(r"^[a-zA-Záéíóúñü]+-[a-zA-Záéíóúñü]+-\d{3}$")

    def test_formato_palabra_palabra_numero(self):
        for _ in range(20):
            clave = generar_clave_legible()
            self.assertRegex(clave, self.FORMATO)

    def test_las_generadas_pasan_la_validacion_de_robustez(self):
        for _ in range(20):
            self.assertEqual(errores_de_clave(generar_clave_legible()), [])

    def test_no_se_repiten_en_lotes_chicos(self):
        claves = {generar_clave_legible() for _ in range(50)}
        # Con ~1M de combinaciones, 50 seguidas repetidas serían señal de bug.
        self.assertGreater(len(claves), 45)


class ValidacionRobustezTests(BaseJuegoTestCase):
    def test_rechaza_claves_debiles(self):
        for debil in ["corta", "12345678", "password"]:
            self.assertNotEqual(errores_de_clave(debil), [], f"aceptó {debil!r}")

    def test_acepta_clave_razonable(self):
        self.assertEqual(errores_de_clave("condor-austral-742"), [])

    def test_registrarprofesor_rechaza_clave_debil(self):
        self.login_admin()
        self.client.post(reverse("registrarprofesor"), {
            "email": "debil@udd.cl",
            "facultad": "Derecho",
            "clave": "123",
        })
        self.assertFalse(
            Profesor.objects.filter(emailprofesor="debil@udd.cl").exists()
        )

    def test_comando_rechaza_clave_debil(self):
        with self.assertRaises(CommandError):
            call_command("crear_profesor", "cmd@udd.cl", "123")
        self.assertFalse(Profesor.objects.filter(emailprofesor="cmd@udd.cl").exists())

    def test_comando_con_forzar_permite_clave_debil(self):
        call_command("crear_profesor", "cmd@udd.cl", "123", "--forzar")
        self.assertTrue(Profesor.objects.filter(emailprofesor="cmd@udd.cl").exists())


class RestablecerClaveTests(BaseJuegoTestCase):
    def test_solo_admin_puede_restablecer(self):
        url = reverse("restablecer_clave_profesor", args=[self.profesor.idprofesor])

        respuesta = self.client.post(url)
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("login_acceso"), respuesta.url)

        # El profesor tampoco puede (es acción de admin).
        self.login_profesor()
        respuesta = self.client.post(url)
        self.assertIn(reverse("login_acceso"), respuesta.url)

    def test_restablece_y_la_clave_anterior_deja_de_servir(self):
        self.login_admin()
        url = reverse("restablecer_clave_profesor", args=[self.profesor.idprofesor])

        respuesta = self.client.post(url, follow=True)

        # Instancia fresca: la del setUp cachea el Usuario con el hash viejo.
        profesor = Profesor.objects.get(pk=self.profesor.pk)

        # La clave original ya no sirve.
        self.assertFalse(verificar_clave_profesor(profesor, "clave-segura-123"))

        # La nueva aparece una vez en el mensaje y sí sirve.
        mensajes = [str(m) for m in respuesta.context["messages"]]
        texto = next(m for m in mensajes if "Nueva clave" in m)
        clave_nueva = re.search(r": (\S+) —", texto).group(1)

        self.assertTrue(verificar_clave_profesor(profesor, clave_nueva))

    def test_profesor_inexistente_404(self):
        self.login_admin()
        respuesta = self.client.post(
            reverse("restablecer_clave_profesor", args=[99999])
        )
        self.assertEqual(respuesta.status_code, 404)


class ClaveSugeridaTests(BaseJuegoTestCase):
    def test_endpoint_devuelve_clave_valida(self):
        self.login_admin()
        datos = self.client.get(
            reverse("generar_clave_sugerida"),
            HTTP_ACCEPT="application/json",
        ).json()
        self.assertEqual(errores_de_clave(datos["clave"]), [])

    def test_requiere_admin(self):
        respuesta = self.client.get(
            reverse("generar_clave_sugerida"),
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(respuesta.status_code, 403)
