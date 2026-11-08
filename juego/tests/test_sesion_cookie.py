# juego/tests/test_sesion_cookie.py
"""Una consulta que llega con la cookie anterior no debe borrar la cookie nueva."""

from django.conf import settings
from django.urls import reverse

from .base import BaseJuegoTestCase


class CookieDeSesionTests(BaseJuegoTestCase):
    def registrar(self):
        self.client.post(reverse("registro"), {
            "id_grupo": self.grupo.codigoacceso,
            "nombre_grupo": "Los Cracks",
        })
        return self.client.cookies[settings.SESSION_COOKIE_NAME].value

    def test_consulta_con_cookie_anterior_no_borra_la_cookie(self):
        # El registro elimina la sesión anterior: su clave ya no existe.
        anterior = self.client.session.session_key or "clave-que-ya-no-existe"
        self.registrar()

        consulta_tardia = self.client_class()
        consulta_tardia.cookies[settings.SESSION_COOKIE_NAME] = anterior
        respuesta = consulta_tardia.get(reverse("pantalla_inicio"))

        self.assertNotIn(settings.SESSION_COOKIE_NAME, respuesta.cookies)

    def test_el_grupo_sigue_registrado_tras_la_consulta_tardia(self):
        self.registrar()
        consulta_tardia = self.client_class()
        consulta_tardia.cookies[settings.SESSION_COOKIE_NAME] = "clave-que-ya-no-existe"
        consulta_tardia.get(reverse("pantalla_inicio"))

        respuesta = self.client.get(reverse("pantalla_inicio"))
        self.assertNotEqual(respuesta.get("Location"), reverse("registro"))
        self.assertEqual(self.client.session.get("grupo_id"), self.grupo.idgrupo)

    def test_salir_sigue_cerrando_la_sesion_del_grupo(self):
        self.registrar()
        self.client.get(reverse("salir_grupo"))

        respuesta = self.client.get(reverse("pantalla_inicio"))
        self.assertRedirects(respuesta, reverse("registro"), fetch_redirect_response=False)
