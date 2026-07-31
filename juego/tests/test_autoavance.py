# juego/tests/test_autoavance.py
"""autoavanzar_si_todos_listos: gates por fase y efectos secundarios."""

from juego.models import Grupo
from juego.views import autoavanzar_si_todos_listos

from .base import BaseJuegoTestCase


class AutoavanceTests(BaseJuegoTestCase):
    NUM_GRUPOS = 3

    def _marcar_todos(self, campo):
        Grupo.objects.filter(sesion=self.sesion).update(**{campo: True})

    def test_no_avanza_si_falta_un_grupo(self):
        self.set_fase("f1_bienvenida")
        self.grupos[0].listo_lobby = True
        self.grupos[0].save(update_fields=["listo_lobby"])

        self.assertFalse(autoavanzar_si_todos_listos(self.sesion))
        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "f1_bienvenida")

    def test_sin_grupos_no_avanza(self):
        Grupo.objects.filter(sesion=self.sesion).delete()
        self.set_fase("f1_bienvenida")
        self.assertFalse(autoavanzar_si_todos_listos(self.sesion))

    def test_bienvenida_a_conocidos_resetea_gate(self):
        self.set_fase("f1_bienvenida")
        self._marcar_todos("listo_lobby")

        self.assertTrue(autoavanzar_si_todos_listos(self.sesion))

        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "f1_conocidos")
        # f1_conocidos tiene gate propio: el timer no debe estar habilitado aún
        # y los flags del lobby se limpian para el nuevo gate.
        self.assertFalse(self.sesion.inicio_fase_habilitado)
        self.assertEqual(
            Grupo.objects.filter(sesion=self.sesion, listo_lobby=True).count(), 0
        )

    def test_empatia_a_bubblemap_arranca_timer_y_limpia_flags(self):
        self.set_fase("f2_transicion_empatia")
        Grupo.objects.filter(sesion=self.sesion).update(
            listo_f2_empatia=True,
            listo_f2=True,
            bubble_tokens_otorgados=True,
        )

        self.assertTrue(autoavanzar_si_todos_listos(self.sesion))

        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "f2_bubblemap")
        # El timer arranca solo: no hay segundo gate dentro del bubble map.
        self.assertTrue(self.sesion.timer_corriendo)
        self.assertIsNotNone(self.sesion.timer_fin_at)
        # bubble_tokens_otorgados se limpia al entrar (si no, la vista de tokens
        # trataría la fase como ya completada).
        self.assertEqual(
            Grupo.objects.filter(sesion=self.sesion, bubble_tokens_otorgados=True).count(),
            0,
        )

    def test_creatividad_a_lego_limpia_flags_y_arranca_timer(self):
        self.set_fase("f3_transicion_creatividad")
        Grupo.objects.filter(sesion=self.sesion).update(
            listo_f3=True,
            listo_inicio_f3=True,
        )

        self.assertTrue(autoavanzar_si_todos_listos(self.sesion))

        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "f3_lego")
        self.assertTrue(self.sesion.timer_corriendo)
        self.assertEqual(
            Grupo.objects.filter(sesion=self.sesion, listo_f3=True).count(), 0
        )

    def test_orden_pitch_primero_sortea_luego_avanza(self):
        self.set_fase("f4_orden_pitch")
        self._marcar_todos("listo_f4_orden")

        # Etapa 1: sorteo del orden.
        self.assertTrue(autoavanzar_si_todos_listos(self.sesion))
        self.sesion.refresh_from_db()

        self.assertTrue(self.sesion.orden_sorteado)
        self.assertEqual(self.sesion.fase_actual, "f4_orden_pitch")

        ordenes = sorted(
            Grupo.objects.filter(sesion=self.sesion).values_list(
                "orden_presentacion", flat=True
            )
        )
        self.assertEqual(ordenes, [1, 2, 3])
        self.assertEqual(self.sesion.grupo_presentando.orden_presentacion, 1)
        # El gate se limpia para la confirmación de la etapa 2.
        self.assertEqual(
            Grupo.objects.filter(sesion=self.sesion, listo_f4_orden=True).count(), 0
        )

        # Etapa 2: todos confirman el orden y se pasa a la presentación.
        self._marcar_todos("listo_f4_orden")
        self.assertTrue(autoavanzar_si_todos_listos(self.sesion))

        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "f4_presentacion_pitch")
        self.assertEqual(self.sesion.grupo_presentando.orden_presentacion, 1)

    def test_ranking_final_a_reflexion(self):
        self.set_fase("f6_ranking")
        self._marcar_todos("listo_f6")

        self.assertTrue(autoavanzar_si_todos_listos(self.sesion))
        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "reflexion")

    def test_salir_de_ranking_avanza_a_creatividad(self):
        self.set_fase("f2_ranking")
        self._marcar_todos("listo_f6")

        self.assertTrue(autoavanzar_si_todos_listos(self.sesion))
        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "f3_transicion_creatividad")

    def test_entrar_a_ranking_limpia_flags_de_ranking(self):
        """Los flags listo_f6/listo_ranking se limpian al ENTRAR a una fase de ranking."""
        self.set_fase("f3_lego")
        Grupo.objects.filter(sesion=self.sesion).update(
            listo_f3_lego=True, listo_f6=True, listo_ranking=True
        )

        self.assertTrue(autoavanzar_si_todos_listos(self.sesion))
        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.fase_actual, "f3_ranking")
        self.assertEqual(
            Grupo.objects.filter(sesion=self.sesion, listo_f6=True).count(), 0
        )
        self.assertEqual(
            Grupo.objects.filter(sesion=self.sesion, listo_ranking=True).count(), 0
        )
