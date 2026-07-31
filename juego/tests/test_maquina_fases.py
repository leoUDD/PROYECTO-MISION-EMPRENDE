# juego/tests/test_maquina_fases.py
"""Consistencia interna de la máquina de fases."""

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from juego.views import (
    ETIQUETA_FASE,
    FASES_CON_INICIO_POR_ALUMNOS,
    FASES_ORDEN,
    RUTA_POR_FASE,
    fase_anterior_automatica,
    siguiente_fase_automatica,
    tiempo_por_fase,
)

from .base import crear_sesion


class ConsistenciaFasesTests(TestCase):
    def test_toda_fase_tiene_ruta(self):
        for fase in FASES_ORDEN:
            self.assertIn(fase, RUTA_POR_FASE, f"Falta ruta para {fase}")

    def test_toda_fase_tiene_etiqueta(self):
        for fase in FASES_ORDEN:
            self.assertIn(fase, ETIQUETA_FASE, f"Falta etiqueta para {fase}")

    def test_rutas_resuelven_a_urls_reales(self):
        for fase in FASES_ORDEN:
            nombre_vista = RUTA_POR_FASE[fase]
            try:
                reverse(nombre_vista)
            except Exception as exc:
                self.fail(f"La ruta {nombre_vista!r} de {fase} no resuelve: {exc}")

    def test_tiempo_por_fase_definido_para_todas(self):
        sesion = crear_sesion()
        for fase in FASES_ORDEN:
            segundos = tiempo_por_fase(sesion, fase)
            self.assertIsInstance(segundos, int)
            self.assertGreaterEqual(segundos, 0, f"Tiempo negativo en {fase}")

    def test_fases_con_gate_pertenecen_al_flujo(self):
        for fase in FASES_CON_INICIO_POR_ALUMNOS:
            self.assertIn(fase, FASES_ORDEN)

    def test_apoyo_fue_eliminada_del_flujo(self):
        """f5_transicion_apoyo salió del flujo intencionalmente: no debe quedar en los diccionarios."""
        self.assertNotIn("f5_transicion_apoyo", FASES_ORDEN)
        self.assertNotIn("f5_transicion_apoyo", RUTA_POR_FASE)
        self.assertNotIn("f5_transicion_apoyo", ETIQUETA_FASE)


class NavegacionFasesTests(SimpleTestCase):
    def test_siguiente_recorre_toda_la_lista(self):
        for i, fase in enumerate(FASES_ORDEN[:-1]):
            self.assertEqual(siguiente_fase_automatica(fase), FASES_ORDEN[i + 1])

    def test_ultima_fase_no_avanza(self):
        ultima = FASES_ORDEN[-1]
        self.assertEqual(siguiente_fase_automatica(ultima), ultima)

    def test_anterior_recorre_toda_la_lista(self):
        for i, fase in enumerate(FASES_ORDEN[1:], start=1):
            self.assertEqual(fase_anterior_automatica(fase), FASES_ORDEN[i - 1])

    def test_primera_fase_no_retrocede(self):
        primera = FASES_ORDEN[0]
        self.assertEqual(fase_anterior_automatica(primera), primera)

    def test_fase_desconocida_no_rompe(self):
        self.assertEqual(siguiente_fase_automatica("fase_inexistente"), "fase_inexistente")
        self.assertEqual(fase_anterior_automatica("fase_inexistente"), "fase_inexistente")
