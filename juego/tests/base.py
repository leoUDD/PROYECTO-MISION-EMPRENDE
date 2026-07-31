# juego/tests/base.py
"""Helpers compartidos por toda la suite de tests."""

from django.test import TestCase

from juego.auth import asignar_clave_profesor
from juego.models import Grupo, Profesor, Sesion, Usuario


def crear_profesor(email="profe@udd.cl", clave="clave-segura-123"):
    usuario = Usuario.objects.create(password="")
    profesor = Profesor.objects.create(
        usuario_idusuario=usuario,
        emailprofesor=email,
        facultad="Ingeniería",
    )
    asignar_clave_profesor(profesor, clave)
    return profesor


def crear_sesion(profesor=None, **kwargs):
    profesor = profesor or crear_profesor()
    defaults = {"nombre": "Sesión de prueba"}
    defaults.update(kwargs)
    return Sesion.objects.create(profesor=profesor, **defaults)


def crear_grupos(sesion, cantidad, tokens=10):
    grupos = []
    for i in range(cantidad):
        grupos.append(
            Grupo.objects.create(
                sesion=sesion,
                nombregrupo=f"Grupo {i + 1}",
                tokensgrupo=tokens,
                codigoacceso=f"TST{i:03d}{sesion.idsesion % 100:02d}",
            )
        )
    return grupos


class BaseJuegoTestCase(TestCase):
    """Crea una sesión con grupos y helpers de login para alumno y staff."""

    NUM_GRUPOS = 2

    def setUp(self):
        super().setUp()
        self.profesor = crear_profesor()
        self.sesion = crear_sesion(self.profesor)
        self.grupos = crear_grupos(self.sesion, self.NUM_GRUPOS)
        self.grupo = self.grupos[0] if self.grupos else None

    def login_alumno(self, grupo=None):
        """Simula un navegador de grupo con la sesión de Django del juego."""
        grupo = grupo or self.grupo
        session = self.client.session
        session["grupo_id"] = grupo.idgrupo
        session["sesion_id"] = grupo.sesion_id
        session.save()
        return grupo

    def login_profesor(self, profesor=None):
        profesor = profesor or self.profesor
        session = self.client.session
        session["profesor_id"] = profesor.idprofesor
        session.save()
        return profesor

    def login_admin(self):
        session = self.client.session
        session["es_admin"] = True
        session.save()

    def set_fase(self, fase, **extra):
        self.sesion.fase_actual = fase
        for campo, valor in extra.items():
            setattr(self.sesion, campo, valor)
        self.sesion.save()
        self.sesion.refresh_from_db()

    def post_json(self, url, payload=None):
        import json as _json

        return self.client.post(
            url,
            data=_json.dumps(payload or {}),
            content_type="application/json",
        )
