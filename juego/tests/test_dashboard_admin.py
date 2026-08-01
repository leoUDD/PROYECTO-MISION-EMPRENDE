# juego/tests/test_dashboard_admin.py
"""Métricas del dashboard de administración: valores correctos y actualizados."""

from django.urls import reverse

from juego.models import Alumno, Grupo
from juego.views import FASES_ORDEN

from .base import BaseJuegoTestCase, crear_grupos, crear_profesor, crear_sesion


class DashboardAdminKpisTests(BaseJuegoTestCase):
    NUM_GRUPOS = 4

    def setUp(self):
        super().setUp()
        self.login_admin()

    def _kpis(self):
        return self.client.get(reverse("dashboardadmin")).context["kpis"]

    def _crear_alumnos(self, cantidad, sesion=None, grupo=None):
        sesion = sesion or self.sesion
        for i in range(cantidad):
            Alumno.objects.create(
                profesor_idprofesor=self.profesor,
                sesion=sesion,
                grupo=grupo,
                nombrealumno=f"Alumno {i}",
            )

    def test_conteos_basicos(self):
        kpis = self._kpis()
        self.assertEqual(kpis["profesores"], 1)
        self.assertEqual(kpis["grupos"], 4)
        self.assertEqual(kpis["sesiones"], 1)

    def test_alumnos_jugado_requiere_grupo_y_partida_iniciada(self):
        # 3 alumnos con grupo, pero la sesión sigue en la fase inicial: 0 jugados.
        self._crear_alumnos(3, grupo=self.grupos[0])
        # 2 alumnos sin grupo asignado: tampoco cuentan aunque avance la sesión.
        self._crear_alumnos(2, grupo=None)

        kpis = self._kpis()
        self.assertEqual(kpis["alumnos_registrados"], 5)
        self.assertEqual(kpis["alumnos_jugado"], 0)

        # La sesión avanza: ahora los 3 con grupo cuentan como jugados.
        self.set_fase(FASES_ORDEN[1])
        kpis = self._kpis()
        self.assertEqual(kpis["alumnos_jugado"], 3)
        self.assertEqual(kpis["alumnos_registrados"], 5)

    def test_alumnos_jugado_suma_entre_sesiones(self):
        self.set_fase(FASES_ORDEN[2])
        self._crear_alumnos(2, grupo=self.grupos[0])

        otra = crear_sesion(crear_profesor("otro@udd.cl"), fase_actual=FASES_ORDEN[3])
        (grupo_otra,) = crear_grupos(otra, 1)
        for i in range(4):
            Alumno.objects.create(
                profesor_idprofesor=self.profesor,
                sesion=otra,
                grupo=grupo_otra,
                nombrealumno=f"B{i}",
            )

        self.assertEqual(self._kpis()["alumnos_jugado"], 6)

    def test_porcentajes_de_actividad(self):
        # 2 de 4 grupos con sopa, 1 con pitch, 0 con lego.
        Grupo.objects.filter(pk=self.grupos[0].pk).update(sopa_ganada=True)
        Grupo.objects.filter(pk=self.grupos[1].pk).update(
            sopa_ganada=True, pitch_texto="Nuestro pitch"
        )

        kpis = self._kpis()
        self.assertEqual(kpis["pct_sopa"], 50)
        self.assertEqual(kpis["pct_pitch"], 25)
        self.assertEqual(kpis["pct_lego"], 0)

    def test_metricas_eliminadas_no_aparecen(self):
        respuesta = self.client.get(reverse("dashboardadmin"))
        self.assertNotContains(respuesta, "Palabras sopa")
        self.assertNotContains(respuesta, "Burbujas")
        self.assertContains(respuesta, "Alumnos que han jugado")

    def test_sesiones_recientes_muestran_fase_legible_y_porcentajes(self):
        self.set_fase("f2_bubblemap")
        Grupo.objects.filter(pk=self.grupos[0].pk).update(
            pitch_texto="pitch", sopa_ganada=True
        )

        respuesta = self.client.get(reverse("dashboardadmin"))
        recientes = respuesta.context["sesiones_recientes"]

        self.assertEqual(len(recientes), 1)
        fila = recientes[0]
        # Etiqueta legible, no la clave interna.
        self.assertNotEqual(fila["fase_actual"], "f2_bubblemap")
        self.assertEqual(fila["total_grupos"], 4)
        self.assertEqual(fila["sopa"], 25)
        self.assertEqual(fila["pitch"], 25)
        self.assertEqual(fila["lego"], 0)

    def test_dashboard_sin_datos_no_rompe(self):
        from juego.models import Sesion

        Grupo.objects.all().delete()
        Sesion.objects.all().delete()

        kpis = self._kpis()
        self.assertEqual(kpis["grupos"], 0)
        self.assertEqual(kpis["pct_sopa"], 0)
        self.assertEqual(kpis["alumnos_jugado"], 0)
