"""El sorteo del pitch corre desde el polling y debe ocurrir una sola vez."""

import threading

from django.db import connections
from django.test import TransactionTestCase, skipUnlessDBFeature

from juego.models import Grupo, Sesion
from juego.views import autoavanzar_si_todos_listos, sortear_orden_pitch

from .base import BaseJuegoTestCase, crear_grupos, crear_sesion


def ordenes(sesion):
    return sorted(
        Grupo.objects.filter(sesion=sesion).values_list("orden_presentacion", flat=True)
    )


class SorteoPitchTests(BaseJuegoTestCase):
    NUM_GRUPOS = 4

    def setUp(self):
        super().setUp()
        self.set_fase("f4_orden_pitch")

    def marcar_todos_listos(self):
        Grupo.objects.filter(sesion=self.sesion).update(listo_f4_orden=True)

    def test_sorteo_deja_numeros_unicos_y_presenta_el_primero(self):
        self.marcar_todos_listos()
        self.assertTrue(autoavanzar_si_todos_listos(self.sesion))

        self.sesion.refresh_from_db()
        self.assertEqual(ordenes(self.sesion), [1, 2, 3, 4])
        self.assertTrue(self.sesion.orden_sorteado)
        self.assertEqual(self.sesion.grupo_presentando.orden_presentacion, 1)
        self.assertEqual(
            Grupo.objects.filter(sesion=self.sesion, listo_f4_orden=True).count(), 0
        )

    def test_sesion_desactualizada_no_vuelve_a_sortear(self):
        desactualizada = Sesion.objects.get(pk=self.sesion.pk)
        self.marcar_todos_listos()
        self.assertTrue(sortear_orden_pitch(self.sesion))

        orden = dict(
            Grupo.objects.filter(sesion=self.sesion).values_list("idgrupo", "orden_presentacion")
        )
        presentador = Sesion.objects.get(pk=self.sesion.pk).grupo_presentando_id

        self.marcar_todos_listos()
        self.assertFalse(desactualizada.orden_sorteado)
        self.assertFalse(sortear_orden_pitch(desactualizada))

        self.assertEqual(
            dict(Grupo.objects.filter(sesion=self.sesion).values_list("idgrupo", "orden_presentacion")),
            orden,
        )
        self.assertEqual(Sesion.objects.get(pk=self.sesion.pk).grupo_presentando_id, presentador)

    def test_no_sortea_si_falta_un_grupo(self):
        Grupo.objects.filter(pk=self.grupos[0].pk).update(listo_f4_orden=True)
        self.assertFalse(sortear_orden_pitch(self.sesion))
        self.assertFalse(Sesion.objects.get(pk=self.sesion.pk).orden_sorteado)

    def test_no_sortea_fuera_de_la_fase(self):
        self.marcar_todos_listos()
        self.set_fase("f4_construccion_pitch")
        self.assertFalse(sortear_orden_pitch(self.sesion))


@skipUnlessDBFeature("has_select_for_update")
class SorteoConcurrenteTests(TransactionTestCase):
    """SQLite no tiene bloqueo de filas: esta prueba corre solo en MySQL."""

    HILOS = 8

    def test_sorteos_simultaneos_producen_un_solo_orden(self):
        for _ in range(10):
            sesion = crear_sesion(fase_actual="f4_orden_pitch")
            crear_grupos(sesion, 6)
            Grupo.objects.filter(sesion=sesion).update(listo_f4_orden=True)

            barrera = threading.Barrier(self.HILOS)
            resultados = []

            def sortear():
                try:
                    copia = Sesion.objects.get(pk=sesion.pk)
                    barrera.wait()
                    resultados.append(sortear_orden_pitch(copia))
                finally:
                    connections.close_all()

            hilos = [threading.Thread(target=sortear) for _ in range(self.HILOS)]
            for hilo in hilos:
                hilo.start()
            for hilo in hilos:
                hilo.join()

            self.assertEqual(resultados.count(True), 1)
            self.assertEqual(ordenes(sesion), [1, 2, 3, 4, 5, 6])
            sesion.refresh_from_db()
            self.assertEqual(sesion.grupo_presentando.orden_presentacion, 1)
