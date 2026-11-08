"""Las rutas de OneDrive pueden reemplazar la cuenta conectada: solo para admin."""

from unittest.mock import patch

from django.urls import reverse

from .base import BaseJuegoTestCase

RUTAS = ("onedrive_conectar", "onedrive_callback", "onedrive_probar")


class OneDriveAccesoTests(BaseJuegoTestCase):
    def setUp(self):
        super().setUp()
        servicio = "juego.onedrive_service."
        self.iniciar = patch(
            servicio + "iniciar_autorizacion",
            return_value={"auth_uri": "https://login.microsoftonline.com/x"},
        ).start()
        self.completar = patch(servicio + "completar_autorizacion").start()
        self.usuario = patch(
            servicio + "obtener_usuario_onedrive",
            return_value={"userPrincipalName": "cuenta@udd.cl", "displayName": "Cuenta"},
        ).start()
        self.addCleanup(patch.stopall)

    def assert_sin_acceso(self):
        for ruta in RUTAS:
            respuesta = self.client.get(reverse(ruta))
            self.assertEqual(respuesta.status_code, 302, ruta)
            self.assertIn(reverse("login_acceso"), respuesta["Location"], ruta)

        self.iniciar.assert_not_called()
        self.completar.assert_not_called()
        self.usuario.assert_not_called()

    def test_anonimo_no_entra(self):
        self.assert_sin_acceso()

    def test_alumno_no_entra(self):
        self.login_alumno()
        self.assert_sin_acceso()

    def test_profesor_no_entra(self):
        self.login_profesor()
        self.assert_sin_acceso()

    def test_callback_anonimo_no_guarda_aunque_haya_flujo(self):
        session = self.client.session
        session["onedrive_auth_flow"] = {"state": "x"}
        session.save()

        self.client.get(reverse("onedrive_callback"), {"code": "c", "state": "x"})

        self.completar.assert_not_called()

    def test_admin_inicia_la_autorizacion(self):
        self.login_admin()
        respuesta = self.client.get(reverse("onedrive_conectar"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta["Location"], "https://login.microsoftonline.com/x")

    def test_admin_completa_la_autorizacion(self):
        self.login_admin()
        session = self.client.session
        session["onedrive_auth_flow"] = {"state": "x"}
        session.save()

        respuesta = self.client.get(reverse("onedrive_callback"), {"code": "c", "state": "x"})

        self.assertEqual(respuesta.status_code, 200)
        self.completar.assert_called_once()

    def test_admin_prueba_la_conexion(self):
        self.login_admin()
        respuesta = self.client.get(reverse("onedrive_probar"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["cuenta"], "cuenta@udd.cl")
