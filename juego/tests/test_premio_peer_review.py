"""El premio de evaluación debe depender de la nota, no del turno de presentación."""

import threading
from unittest.mock import patch

from django.db import connections
from django.test import TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse

from juego.models import Evaluacion, Grupo, Sesion
from juego.views import (
    COMENTARIO_EVALUACION_AUTOMATICA,
    avanzar_al_siguiente_pitch_o_ranking,
    entregar_premios_peer_review,
    otorgar_tokens_peer_review,
)

from .base import BaseJuegoTestCase, crear_grupos, crear_sesion
from .test_peer_review_ranking import evaluar


def tokens(grupo):
    return Grupo.objects.get(pk=grupo.pk).tokensgrupo


class PremioPeerReviewTests(BaseJuegoTestCase):
    NUM_GRUPOS = 3

    def setUp(self):
        super().setUp()
        self.a, self.b, self.c = self.grupos
        for orden, grupo in enumerate(self.grupos, start=1):
            Grupo.objects.filter(pk=grupo.pk).update(orden_presentacion=orden)
        self.set_fase("f5_evaluacion_pitch", grupo_presentando=self.c)

    def test_premia_al_mejor_evaluado_aunque_presente_ultimo(self):
        evaluar(self.sesion, self.a, self.b, puntaje=2)
        evaluar(self.sesion, self.a, self.c, puntaje=5)

        avanzar_al_siguiente_pitch_o_ranking(self.sesion)

        self.assertEqual(tokens(self.b), 10)
        self.assertEqual(tokens(self.c), 12)

    def test_no_paga_mientras_quedan_pitches(self):
        self.set_fase("f5_evaluacion_pitch", grupo_presentando=self.a)
        self.login_alumno(self.b)
        datos = {
            f"score_{clave}": 5
            for clave in ("claridad", "creatividad", "viabilidad", "equipo", "presentacion")
        }
        datos["comment"] = "bien"

        respuesta = self.client.post(reverse("peer_review"), datos)

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(tokens(self.a), 10)

    def test_empate_se_sortea_y_entrega_solo_dos_tokens(self):
        evaluar(self.sesion, self.a, self.b, puntaje=5)
        evaluar(self.sesion, self.a, self.c, puntaje=5)

        with patch("juego.views.random.choice", side_effect=lambda opciones: opciones[-1]) as sorteo:
            otorgar_tokens_peer_review(self.a)

        self.assertCountEqual(sorteo.call_args.args[0], [self.b.pk, self.c.pk])
        self.assertEqual(tokens(self.b) + tokens(self.c), 22)

    def test_evaluaciones_automaticas_no_cuentan(self):
        evaluar(self.sesion, self.a, self.b, puntaje=3)
        automatica = evaluar(self.sesion, self.a, self.c, puntaje=5)
        Evaluacion.objects.filter(pk=automatica.pk).update(
            comentario=COMENTARIO_EVALUACION_AUTOMATICA
        )

        otorgar_tokens_peer_review(self.a)

        self.assertEqual(tokens(self.b), 12)
        self.assertEqual(tokens(self.c), 10)

    def test_grupo_sin_evaluaciones_propias_no_premia(self):
        automatica = evaluar(self.sesion, self.a, self.b, puntaje=5)
        Evaluacion.objects.filter(pk=automatica.pk).update(
            comentario=COMENTARIO_EVALUACION_AUTOMATICA
        )

        otorgar_tokens_peer_review(self.a)

        self.assertEqual(tokens(self.b), 10)

    def test_entregar_dos_veces_no_paga_doble(self):
        evaluar(self.sesion, self.a, self.b, puntaje=5)

        entregar_premios_peer_review(self.sesion)
        entregar_premios_peer_review(self.sesion)

        self.assertEqual(tokens(self.b), 12)

    def test_volver_a_evaluacion_desde_el_panel_no_habilita_otro_pago(self):
        evaluar(self.sesion, self.a, self.b, puntaje=5)
        entregar_premios_peer_review(self.sesion)

        self.set_fase("f6_ranking")
        self.login_admin()
        self.post_json(
            reverse("profesor_actualizar_estado", args=[self.sesion.pk]),
            {"faseActual": "f5_evaluacion_pitch"},
        )
        entregar_premios_peer_review(self.sesion)

        self.assertEqual(tokens(self.b), 12)


@skipUnlessDBFeature("has_select_for_update")
class PremioConcurrenteTests(TransactionTestCase):
    """SQLite no tiene bloqueo de filas: esta prueba corre solo en MySQL."""

    HILOS = 8

    def test_consultas_simultaneas_pagan_una_sola_vez(self):
        for _ in range(10):
            sesion = crear_sesion(fase_actual="f5_evaluacion_pitch")
            grupos = crear_grupos(sesion, 4)
            for evaluador in grupos:
                for evaluado in grupos:
                    if evaluador.pk != evaluado.pk:
                        evaluar(sesion, evaluador, evaluado, puntaje=4)

            barrera = threading.Barrier(self.HILOS)

            def entregar():
                try:
                    copia = Sesion.objects.get(pk=sesion.pk)
                    barrera.wait()
                    entregar_premios_peer_review(copia)
                finally:
                    connections.close_all()

            hilos = [threading.Thread(target=entregar) for _ in range(self.HILOS)]
            for hilo in hilos:
                hilo.start()
            for hilo in hilos:
                hilo.join()

            total = sum(tokens(g) for g in grupos)
            self.assertEqual(total, 4 * 10 + 4 * 2)
