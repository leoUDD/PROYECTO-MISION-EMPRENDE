# juego/tests/test_peer_review_ranking.py
"""Evaluaciones, recompensas de peer review y ranking."""

from django.db import IntegrityError
from django.urls import reverse

from juego.models import Evaluacion, Grupo
from juego.views import otorgar_tokens_peer_review

from .base import BaseJuegoTestCase


def evaluar(sesion, evaluador, evaluado, puntaje=4, **extra):
    return Evaluacion.objects.create(
        sesion=sesion,
        grupo_evaluador=evaluador,
        grupo_evaluado=evaluado,
        claridad=puntaje,
        creatividad=puntaje,
        viabilidad=puntaje,
        equipo=puntaje,
        presentacion=puntaje,
        comentario="c",
        **extra,
    )


class EvaluacionModelTests(BaseJuegoTestCase):
    NUM_GRUPOS = 3

    def test_no_permite_evaluar_dos_veces_al_mismo_grupo(self):
        a, b, _ = self.grupos
        evaluar(self.sesion, a, b)

        with self.assertRaises(IntegrityError):
            evaluar(self.sesion, a, b)

    def test_puntaje_total(self):
        a, b, _ = self.grupos
        e = evaluar(self.sesion, a, b, puntaje=3)
        self.assertEqual(e.puntaje_total(), 15)


class PeerReviewTokensTests(BaseJuegoTestCase):
    NUM_GRUPOS = 3

    def test_premia_al_mejor_evaluado_por_el_evaluador(self):
        a, b, c = self.grupos
        evaluar(self.sesion, a, b, puntaje=5)
        evaluar(self.sesion, a, c, puntaje=2)

        otorgar_tokens_peer_review(a)

        b.refresh_from_db()
        c.refresh_from_db()
        a.refresh_from_db()
        self.assertEqual(b.tokensgrupo, 12)
        self.assertEqual(c.tokensgrupo, 10)
        self.assertTrue(a.recompensa_peer_otorgada)

    def test_es_idempotente(self):
        a, b, _ = self.grupos
        evaluar(self.sesion, a, b, puntaje=5)

        otorgar_tokens_peer_review(a)
        a.refresh_from_db()
        otorgar_tokens_peer_review(a)

        b.refresh_from_db()
        self.assertEqual(b.tokensgrupo, 12)

    def test_sin_evaluaciones_no_hace_nada(self):
        a = self.grupos[0]
        otorgar_tokens_peer_review(a)
        a.refresh_from_db()
        self.assertFalse(a.recompensa_peer_otorgada)


class RankingViewTests(BaseJuegoTestCase):
    NUM_GRUPOS = 3

    def test_empates_comparten_posicion(self):
        a, b, c = self.grupos
        Grupo.objects.filter(pk=a.pk).update(tokensgrupo=10)
        Grupo.objects.filter(pk=b.pk).update(tokensgrupo=10)
        Grupo.objects.filter(pk=c.pk).update(tokensgrupo=5)

        self.login_alumno(a)
        respuesta = self.client.get(reverse("ranking"))

        rankings = respuesta.context["rankings"]
        posiciones = [(r["tokens"], r["rank"]) for r in rankings]
        self.assertEqual(posiciones, [(10, 1), (10, 1), (5, 3)])

    def test_marca_al_grupo_propio(self):
        self.login_alumno(self.grupo)
        respuesta = self.client.get(reverse("ranking"))
        mios = [r for r in respuesta.context["rankings"] if r["is_me"]]
        self.assertEqual(len(mios), 1)
        self.assertEqual(mios[0]["team_name"], self.grupo.nombregrupo)

    def test_sin_sesion_redirige_a_registro(self):
        respuesta = self.client.get(reverse("ranking"))
        self.assertRedirects(respuesta, reverse("registro"), fetch_redirect_response=False)


class TokensGrupoTests(BaseJuegoTestCase):
    def test_ajustar_tokens_no_baja_de_cero(self):
        self.grupo.ajustar_tokens(-99)
        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.tokensgrupo, 0)

    def test_ajustar_tokens_desde_null(self):
        Grupo.objects.filter(pk=self.grupo.pk).update(tokensgrupo=None)
        self.grupo.refresh_from_db()
        self.grupo.ajustar_tokens(4)
        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.tokensgrupo, 4)
