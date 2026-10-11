# juego/tests/test_claves.py
"""Robustez y restablecimiento de claves de profesor."""

from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse

from juego.auth import errores_de_clave, verificar_clave_profesor
from juego.models import Profesor

from .base import BaseJuegoTestCase, crear_profesor


class ValidacionRobustezTests(BaseJuegoTestCase):
    def test_rechaza_claves_debiles(self):
        for debil in ["corta", "12345678", "password"]:
            self.assertNotEqual(errores_de_clave(debil), [], f"aceptó {debil!r}")

    def test_exige_letras_numeros_y_simbolos(self):
        # Sin símbolo.
        self.assertNotEqual(errores_de_clave("solamente1letras2"), [])
        # Sin número.
        self.assertNotEqual(errores_de_clave("sin-numeros-aqui"), [])
        # Sin letra.
        self.assertNotEqual(errores_de_clave("1234-5678-90"), [])

    def test_acepta_clave_que_cumple_todo(self):
        self.assertEqual(errores_de_clave("condor-austral-742"), [])
        self.assertEqual(errores_de_clave("MisionUdd2026!"), [])

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

    def test_registrarprofesor_rechaza_clave_sin_simbolos(self):
        self.login_admin()
        self.client.post(reverse("registrarprofesor"), {
            "email": "sinsimbolo@udd.cl",
            "facultad": "Derecho",
            "clave": "letras1y2numeros",
        })
        self.assertFalse(
            Profesor.objects.filter(emailprofesor="sinsimbolo@udd.cl").exists()
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

        respuesta = self.client.post(url, {"clave_nueva": "nueva-clave-99!"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("login_acceso"), respuesta.url)

        # El profesor tampoco puede (es acción de admin).
        self.login_profesor()
        respuesta = self.client.post(url, {"clave_nueva": "nueva-clave-99!"})
        self.assertIn(reverse("login_acceso"), respuesta.url)

    def test_restablece_con_la_clave_ingresada(self):
        self.login_admin()
        url = reverse("restablecer_clave_profesor", args=[self.profesor.idprofesor])

        self.client.post(url, {"clave_nueva": "nueva-clave-99!"})

        # Instancia fresca: la del setUp cachea el Usuario con el hash viejo.
        profesor = Profesor.objects.get(pk=self.profesor.pk)

        # La clave original ya no sirve; la ingresada sí.
        self.assertFalse(verificar_clave_profesor(profesor, "clave-segura-123"))
        self.assertTrue(verificar_clave_profesor(profesor, "nueva-clave-99!"))

    def test_rechaza_clave_nueva_debil(self):
        self.login_admin()
        url = reverse("restablecer_clave_profesor", args=[self.profesor.idprofesor])

        self.client.post(url, {"clave_nueva": "corta"})

        profesor = Profesor.objects.get(pk=self.profesor.pk)
        # La clave original sigue funcionando: no se cambió nada.
        self.assertTrue(verificar_clave_profesor(profesor, "clave-segura-123"))

    def test_rechaza_sin_clave_nueva(self):
        self.login_admin()
        url = reverse("restablecer_clave_profesor", args=[self.profesor.idprofesor])

        self.client.post(url, {})

        profesor = Profesor.objects.get(pk=self.profesor.pk)
        self.assertTrue(verificar_clave_profesor(profesor, "clave-segura-123"))

    def test_profesor_inexistente_404(self):
        self.login_admin()
        respuesta = self.client.post(
            reverse("restablecer_clave_profesor", args=[99999]),
            {"clave_nueva": "nueva-clave-99!"},
        )
        self.assertEqual(respuesta.status_code, 404)
