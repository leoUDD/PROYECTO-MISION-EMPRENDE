# juego/tests/test_grupos.py
"""Creación y distribución de grupos para una sesión."""

from juego.models import Alumno, Grupo
from juego.views import crear_grupos_para_alumnos

from .base import BaseJuegoTestCase


class CrearGruposTests(BaseJuegoTestCase):
    NUM_GRUPOS = 0  # esta suite crea los suyos

    def _crear_alumnos(self, cantidad):
        alumnos = []
        for i in range(cantidad):
            alumnos.append(
                Alumno.objects.create(
                    profesor_idprofesor=self.profesor,
                    sesion=self.sesion,
                    nombrealumno=f"Alumno {i}",
                )
            )
        return alumnos

    def test_distribucion_por_maximo(self):
        alumnos = self._crear_alumnos(17)

        creados = crear_grupos_para_alumnos(self.sesion, alumnos, max_por_grupo=8)

        self.assertEqual(creados, 3)
        grupos = Grupo.objects.filter(sesion=self.sesion)
        self.assertEqual(grupos.count(), 3)

        # Reparto round-robin: 6, 6 y 5 integrantes.
        tamanos = sorted(
            g.alumno_set.count() for g in grupos
        )
        self.assertEqual(tamanos, [5, 6, 6])

    def test_cantidad_manual_de_grupos(self):
        alumnos = self._crear_alumnos(10)
        creados = crear_grupos_para_alumnos(
            self.sesion, alumnos, cantidad_grupos_manual=2
        )
        self.assertEqual(creados, 2)

    def test_codigos_de_acceso_unicos(self):
        alumnos = self._crear_alumnos(24)
        crear_grupos_para_alumnos(self.sesion, alumnos, max_por_grupo=4)

        codigos = list(
            Grupo.objects.filter(sesion=self.sesion).values_list(
                "codigoacceso", flat=True
            )
        )
        self.assertEqual(len(codigos), len(set(codigos)))
        self.assertTrue(all(codigos))

    def test_todos_los_alumnos_quedan_asignados(self):
        alumnos = self._crear_alumnos(9)
        crear_grupos_para_alumnos(self.sesion, alumnos, max_por_grupo=4)

        sin_grupo = Alumno.objects.filter(sesion=self.sesion, grupo__isnull=True)
        self.assertEqual(sin_grupo.count(), 0)

    def test_sin_alumnos_no_crea_grupos(self):
        self.assertEqual(crear_grupos_para_alumnos(self.sesion, []), 0)
        self.assertEqual(Grupo.objects.filter(sesion=self.sesion).count(), 0)

    def test_grupos_nuevos_parten_con_10_tokens(self):
        alumnos = self._crear_alumnos(4)
        crear_grupos_para_alumnos(self.sesion, alumnos, max_por_grupo=4)
        grupo = Grupo.objects.filter(sesion=self.sesion).first()
        self.assertEqual(grupo.tokensgrupo, 10)
