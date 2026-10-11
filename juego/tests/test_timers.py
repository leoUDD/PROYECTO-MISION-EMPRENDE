# juego/tests/test_timers.py
"""Transiciones de fase disparadas por expiración del cronómetro."""

from datetime import timedelta

from django.utils import timezone

from juego.models import Desafio, Evaluacion, Grupo, Tematica
from juego.views import calcular_segundos_restantes

from .base import BaseJuegoTestCase


class TimerTests(BaseJuegoTestCase):
    NUM_GRUPOS = 3

    def _vencer_timer(self, fase, segundos_originales=60):
        """Deja la sesión con el timer expirado hace 5 segundos."""
        ahora = timezone.now()
        self.set_fase(
            fase,
            timer_corriendo=True,
            segundos_restantes=segundos_originales,
            timer_inicio_at=ahora - timedelta(seconds=segundos_originales + 5),
            timer_fin_at=ahora - timedelta(seconds=5),
        )

    def test_timer_vigente_no_cambia_fase(self):
        ahora = timezone.now()
        self.set_fase(
            "f3_lego",
            timer_corriendo=True,
            segundos_restantes=120,
            timer_inicio_at=ahora,
            timer_fin_at=ahora + timedelta(seconds=120),
        )

        restantes = calcular_segundos_restantes(self.sesion)

        self.assertGreater(restantes, 100)
        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "f3_lego")
        self.assertTrue(self.sesion.timer_corriendo)

    def test_sin_timer_devuelve_segundos_guardados(self):
        self.set_fase("f3_lego", timer_corriendo=False, segundos_restantes=45)
        self.assertEqual(calcular_segundos_restantes(self.sesion), 45)

    def test_expira_presentacion_pitch_pasa_a_evaluacion(self):
        self._vencer_timer("f4_presentacion_pitch")

        restantes = calcular_segundos_restantes(self.sesion)

        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "f5_evaluacion_pitch")
        self.assertEqual(restantes, 90)
        self.assertTrue(self.sesion.timer_corriendo)
        self.assertIsNotNone(self.sesion.timer_fin_at)

    def test_expira_tematicas_asigna_desafio_aleatorio(self):
        tematica = Tematica.objects.create(slug="salud", title="Salud", activa=True)
        desafio = Desafio.objects.create(
            tematica=tematica,
            nombredesafio="Desafío salud",
            activo=True,
        )

        self._vencer_timer("f2_tematicas")
        calcular_segundos_restantes(self.sesion)

        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "f2_transicion_empatia")

        for grupo in Grupo.objects.filter(sesion=self.sesion):
            self.assertTrue(grupo.listo_f2_desafio)
            self.assertEqual(grupo.desafio_elegido_id, desafio.iddesafio)
            self.assertEqual(grupo.tema_elegido, "salud")

    def test_expira_conocidos_autoavanza_a_pre_sopa(self):
        self._vencer_timer("f1_conocidos")
        calcular_segundos_restantes(self.sesion)

        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "f1_pre_sopa")
        self.assertFalse(self.sesion.timer_corriendo)

    def test_expira_evaluacion_penaliza_premia_y_avanza(self):
        presentador, evaluador_a, evaluador_b = self.grupos

        presentador.orden_presentacion = 1
        presentador.save(update_fields=["orden_presentacion"])
        evaluador_a.orden_presentacion = 2
        evaluador_a.save(update_fields=["orden_presentacion"])
        evaluador_b.orden_presentacion = 3
        evaluador_b.save(update_fields=["orden_presentacion"])

        self.sesion.grupo_presentando = presentador
        self.sesion.save(update_fields=["grupo_presentando"])

        # Solo evaluador_a alcanzó a evaluar; evaluador_b será penalizado.
        Evaluacion.objects.create(
            sesion=self.sesion,
            grupo_evaluador=evaluador_a,
            grupo_evaluado=presentador,
            claridad=4, creatividad=4, viabilidad=4, equipo=4, presentacion=4,
            comentario="ok",
        )

        self._vencer_timer("f5_evaluacion_pitch")
        calcular_segundos_restantes(self.sesion)

        self.sesion.refresh_from_db()
        presentador.refresh_from_db()
        evaluador_a.refresh_from_db()
        evaluador_b.refresh_from_db()

        # Se creó la evaluación faltante de evaluador_b (todas en 5).
        self.assertEqual(
            Evaluacion.objects.filter(sesion=self.sesion, grupo_evaluado=presentador).count(),
            2,
        )
        # evaluador_b pierde 2 tokens por no evaluar a tiempo.
        self.assertEqual(evaluador_b.tokensgrupo, 8)
        # evaluador_a no fue penalizado.
        self.assertEqual(evaluador_a.tokensgrupo, 10)
        # El presentador es el mejor (único) evaluado: recibe +3.
        self.assertEqual(presentador.tokensgrupo, 13)
        # Hay más grupos por presentar: vuelve a f4 con el siguiente.
        self.assertEqual(self.sesion.fase_actual, "f4_presentacion_pitch")
        self.assertEqual(self.sesion.grupo_presentando_id, evaluador_a.idgrupo)

    def test_expira_evaluacion_del_ultimo_grupo_va_a_ranking(self):
        a, b, c = self.grupos
        for i, g in enumerate([a, b, c], start=1):
            g.orden_presentacion = i
            g.save(update_fields=["orden_presentacion"])

        # Presenta el último del orden.
        self.sesion.grupo_presentando = c
        self.sesion.save(update_fields=["grupo_presentando"])

        self._vencer_timer("f5_evaluacion_pitch")
        calcular_segundos_restantes(self.sesion)

        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "f6_ranking")
        self.assertIsNone(self.sesion.grupo_presentando)
