# juego/tests/test_validaciones.py
"""Formularios inválidos, datos faltantes, IDs inexistentes y duplicados."""

import io

from django.urls import reverse

from juego.models import Profesor, Sesion

from .base import BaseJuegoTestCase


class CrearSesionValidacionTests(BaseJuegoTestCase):
    def _csv(self, contenido="Nombre,Correo\nAna,a@udd.cl"):
        archivo = io.BytesIO(contenido.encode("utf-8"))
        archivo.name = "alumnos.csv"
        return archivo

    def setUp(self):
        super().setUp()
        self.login_profesor()

    def test_sin_nombre_no_crea_sesion(self):
        respuesta = self.client.post(reverse("crear_sesion"), {
            "nombre": "",
            "modo_creacion": "recomendado",
            "archivo_excel": self._csv(),
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Debes darle un nombre")
        self.assertEqual(Sesion.objects.count(), 1)  # solo la del setUp

    def test_sin_archivo_no_crea_sesion(self):
        respuesta = self.client.post(reverse("crear_sesion"), {
            "nombre": "Sesión X",
            "modo_creacion": "recomendado",
        })
        self.assertContains(respuesta, "Debes subir el archivo")
        self.assertEqual(Sesion.objects.count(), 1)

    def test_archivo_sin_estudiantes_no_crea_sesion(self):
        respuesta = self.client.post(reverse("crear_sesion"), {
            "nombre": "Sesión X",
            "modo_creacion": "recomendado",
            "archivo_excel": self._csv("Nombre,Correo\n"),
        })
        self.assertContains(respuesta, "no tiene estudiantes")
        self.assertEqual(Sesion.objects.count(), 1)

    def test_formato_no_soportado_muestra_error(self):
        archivo = io.BytesIO(b"contenido")
        archivo.name = "alumnos.txt"
        respuesta = self.client.post(reverse("crear_sesion"), {
            "nombre": "Sesión X",
            "modo_creacion": "recomendado",
            "archivo_excel": archivo,
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Sesion.objects.count(), 1)


class RegistrarProfesorValidacionTests(BaseJuegoTestCase):
    def setUp(self):
        super().setUp()
        self.login_admin()

    def test_email_duplicado_es_rechazado(self):
        """Regresión: antes cada envío creaba un Profesor y Usuario nuevos."""
        respuesta = self.client.post(reverse("registrarprofesor"), {
            "email": "PROFE@udd.cl",  # existe como profe@udd.cl
            "facultad": "Derecho",
            "clave": "clave123",
        }, follow=True)

        self.assertContains(respuesta, "Ya existe un profesor")
        self.assertEqual(
            Profesor.objects.filter(emailprofesor__iexact="profe@udd.cl").count(), 1
        )

    def test_campos_faltantes_no_crean_profesor(self):
        total_antes = Profesor.objects.count()

        self.client.post(reverse("registrarprofesor"), {
            "email": "nuevo@udd.cl",
            "facultad": "",
            "clave": "clave123",
        })
        self.client.post(reverse("registrarprofesor"), {
            "email": "nuevo@udd.cl",
            "facultad": "Derecho",
            "clave": "",
        })

        self.assertEqual(Profesor.objects.count(), total_antes)

    def test_profesor_nuevo_puede_loguearse_de_inmediato(self):
        self.client.post(reverse("registrarprofesor"), {
            "email": "flamante@udd.cl",
            "facultad": "Diseño",
            "clave": "suClave99!",
        })

        # Nuevo navegador limpio.
        self.client.session.flush()
        self.client.post(reverse("login_acceso"), {
            "rol": "profesor",
            "email": "flamante@udd.cl",
            "clave": "suClave99!",
        })
        nuevo = Profesor.objects.get(emailprofesor="flamante@udd.cl")
        self.assertEqual(self.client.session.get("profesor_id"), nuevo.idprofesor)


class IdsInexistentesTests(BaseJuegoTestCase):
    def test_estado_sesion_inexistente_404(self):
        respuesta = self.client.get(reverse("estado_sesion", args=[99999]))
        self.assertEqual(respuesta.status_code, 404)

    def test_control_sesion_inexistente_404(self):
        self.login_profesor()
        respuesta = self.client.get(reverse("control_sesion", args=[99999]))
        self.assertEqual(respuesta.status_code, 404)

    def test_siguiente_fase_sesion_inexistente_404(self):
        self.login_profesor()
        respuesta = self.post_json(reverse("profesor_siguiente_fase", args=[99999]))
        self.assertEqual(respuesta.status_code, 404)

    def test_alumno_no_entra_al_dashboard_del_profesor(self):
        """Checklist de permisos: estudiante -> dashboard profesor, denegado."""
        self.login_alumno(self.grupo)
        respuesta = self.client.get(reverse("dashboardprofesor"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("login_acceso"), respuesta.url)
