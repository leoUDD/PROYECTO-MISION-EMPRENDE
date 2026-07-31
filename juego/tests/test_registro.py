# juego/tests/test_registro.py
"""Flujo de ingreso de alumnos por código de escuadrón."""

from django.urls import reverse

from .base import BaseJuegoTestCase


class RegistroTests(BaseJuegoTestCase):
    def test_codigo_valido_crea_sesion_de_grupo(self):
        respuesta = self.client.post(reverse("registro"), {
            "id_grupo": self.grupo.codigoacceso,
            "nombre_grupo": "Los Cracks",
        })

        self.assertRedirects(respuesta, reverse("bienvenida"), fetch_redirect_response=False)
        self.assertEqual(self.client.session.get("grupo_id"), self.grupo.idgrupo)
        self.assertEqual(self.client.session.get("sesion_id"), self.sesion.idsesion)

        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.nombregrupo, "Los Cracks")

    def test_codigo_es_case_insensitive(self):
        respuesta = self.client.post(reverse("registro"), {
            "id_grupo": self.grupo.codigoacceso.lower(),
            "nombre_grupo": "Equipo",
        })
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(self.client.session.get("grupo_id"), self.grupo.idgrupo)

    def test_codigo_invalido_muestra_error(self):
        respuesta = self.client.post(reverse("registro"), {
            "id_grupo": "NOEXISTE",
            "nombre_grupo": "Equipo",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Código de grupo inválido")
        self.assertIsNone(self.client.session.get("grupo_id"))

    def test_codigo_vacio_muestra_error(self):
        respuesta = self.client.post(reverse("registro"), {"id_grupo": ""})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Debes ingresar el código")

    def test_sin_nombre_asigna_uno_aleatorio(self):
        self.client.post(reverse("registro"), {
            "id_grupo": self.grupo.codigoacceso,
            "nombre_grupo": "",
        })
        self.grupo.refresh_from_db()
        self.assertTrue(self.grupo.nombregrupo)
        self.assertNotEqual(self.grupo.nombregrupo.strip(), "")

    def test_reingreso_reemplaza_sesion_anterior(self):
        otro = self.grupos[1]
        self.login_alumno(self.grupo)

        self.client.post(reverse("registro"), {
            "id_grupo": otro.codigoacceso,
            "nombre_grupo": "Nuevo",
        })
        self.assertEqual(self.client.session.get("grupo_id"), otro.idgrupo)
