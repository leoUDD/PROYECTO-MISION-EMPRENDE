# juego/tests/test_flujos_finales.py
"""Flujos funcionales: guardar pitch, market, reflexión y fin de misión."""

from unittest.mock import patch

from django.urls import reverse

from juego.models import Desafio, Reto, Retogrupo, Tematica

from .base import BaseJuegoTestCase


class GuardarPitchTests(BaseJuegoTestCase):
    def test_guarda_el_texto_del_pitch(self):
        self.login_alumno(self.grupo)

        datos = self.post_json(reverse("guardar_pitch"), {
            "pitch": "  Somos la solución al problema X  ",
        }).json()

        self.assertTrue(datos["ok"])
        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.pitch_texto, "Somos la solución al problema X")

    def test_reenvio_sobrescribe_el_anterior(self):
        self.login_alumno(self.grupo)
        self.post_json(reverse("guardar_pitch"), {"pitch": "Versión 1"})
        self.post_json(reverse("guardar_pitch"), {"pitch": "Versión 2"})

        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.pitch_texto, "Versión 2")

    def test_payload_corrupto_no_rompe(self):
        self.login_alumno(self.grupo)
        respuesta = self.client.post(
            reverse("guardar_pitch"),
            data="esto no es json",
            content_type="application/json",
        )
        self.assertEqual(respuesta.status_code, 200)
        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.pitch_texto or "", "")

    def test_sin_sesion_devuelve_403(self):
        respuesta = self.post_json(reverse("guardar_pitch"), {"pitch": "x"})
        self.assertEqual(respuesta.status_code, 403)


class MarketTests(BaseJuegoTestCase):
    def _reto(self, costo=4, recompensa=0):
        desafio = None
        if recompensa:
            tematica = Tematica.objects.create(slug="t", title="T", activa=True)
            desafio = Desafio.objects.create(
                tematica=tematica, nombredesafio="D", tokensdesafio=recompensa, activo=True
            )
        return Reto.objects.create(
            nombrereto="Reto", costoreto=costo, desafio_iddesafio=desafio
        )

    def test_sin_tokens_suficientes_no_crea_el_reto(self):
        reto = self._reto(costo=99)
        self.login_alumno(self.grupo)

        respuesta = self.client.post(
            reverse("issue_challenge", args=[reto.idreto]),
            {"target_team_id": self.grupos[1].idgrupo},
        )

        self.assertRedirects(respuesta, reverse("market"), fetch_redirect_response=False)
        self.assertEqual(Retogrupo.objects.count(), 0)
        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.tokensgrupo, 10)

    def test_sin_equipo_objetivo_no_crea_el_reto(self):
        reto = self._reto()
        self.login_alumno(self.grupo)

        self.client.post(reverse("issue_challenge", args=[reto.idreto]), {})
        self.assertEqual(Retogrupo.objects.count(), 0)

    def test_reto_registra_costo_recompensa_y_penalizacion(self):
        reto = self._reto(costo=3, recompensa=7)
        self.login_alumno(self.grupo)

        self.client.post(
            reverse("issue_challenge", args=[reto.idreto]),
            {"target_team_id": self.grupos[1].idgrupo},
        )

        rg = Retogrupo.objects.get()
        self.assertEqual(rg.tokens_costo, 3)
        self.assertEqual(rg.tokens_recompensa, 7)
        self.assertEqual(rg.tokens_penalizacion, 7)
        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.tokensgrupo, 7)

    def test_reto_inexistente_devuelve_404(self):
        self.login_alumno(self.grupo)
        respuesta = self.client.post(
            reverse("issue_challenge", args=[99999]),
            {"target_team_id": self.grupos[1].idgrupo},
        )
        self.assertEqual(respuesta.status_code, 404)


class ReflexionTests(BaseJuegoTestCase):
    def test_fuera_de_fase_no_borra_fotos_lego(self):
        """Regresión: el borrado de fotos corría ANTES de validar la fase."""
        self.set_fase("f3_lego")
        self.login_alumno(self.grupo)

        with patch("juego.views.borrar_fotos_lego_sesion") as mock_borrar:
            respuesta = self.client.get(reverse("reflexion"))

        self.assertRedirects(respuesta, reverse("pantalla_espera"), fetch_redirect_response=False)
        mock_borrar.assert_not_called()

    def test_en_fase_correcta_si_borra_fotos(self):
        self.set_fase("reflexion")
        self.login_alumno(self.grupo)

        with patch("juego.views.borrar_fotos_lego_sesion") as mock_borrar:
            respuesta = self.client.get(reverse("reflexion"))

        self.assertEqual(respuesta.status_code, 200)
        mock_borrar.assert_called_once_with(self.sesion)

    def test_sin_sesion_redirige_a_registro(self):
        respuesta = self.client.get(reverse("reflexion"))
        self.assertRedirects(respuesta, reverse("registro"), fetch_redirect_response=False)


class FinalizarMisionTests(BaseJuegoTestCase):
    def test_limpia_toda_la_sesion_del_juego(self):
        self.login_alumno(self.grupo)

        respuesta = self.client.get(reverse("finalizar_mision"))

        self.assertRedirects(respuesta, reverse("perfiles"), fetch_redirect_response=False)
        self.assertIsNone(self.client.session.get("grupo_id"))
        self.assertIsNone(self.client.session.get("sesion_id"))

    def test_despues_de_finalizar_no_accede_al_juego(self):
        self.login_alumno(self.grupo)
        self.client.get(reverse("finalizar_mision"))

        respuesta = self.client.get(reverse("ranking"))
        self.assertRedirects(respuesta, reverse("registro"), fetch_redirect_response=False)
