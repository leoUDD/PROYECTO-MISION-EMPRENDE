# juego/tests/test_favicon.py
"""El favicon se enlaza desde los estaticos.

En el servidor, nginx atrapa /favicon.ico y responde 404 antes de llegar a
Django, asi que las paginas deben enlazar /static/images/favicon...ico.
"""

import re
from pathlib import Path

from django.urls import reverse

from .base import BaseJuegoTestCase

PLANTILLAS = Path(__file__).resolve().parents[1] / "templates"
ENLACE = re.compile(r'<link rel="icon" href="([^"]+)"')


class FaviconTests(BaseJuegoTestCase):
    def test_ninguna_plantilla_enlaza_la_ruta_raiz(self):
        culpables = [
            p.name for p in PLANTILLAS.rglob("*.html")
            if "url 'favicon'" in p.read_text(encoding="utf-8")
        ]
        self.assertEqual(culpables, [])

    def test_paginas_completas_tienen_favicon(self):
        sin_favicon = [
            p.name for p in PLANTILLAS.glob("*.html")
            if p.name != "atajos.html" and "favicon" not in p.read_text(encoding="utf-8")
        ]
        self.assertEqual(sin_favicon, [])

    def test_registro_y_lobby_lo_enlazan_desde_static(self):
        paginas = [self.client.get(reverse("registro"))]
        self.sesion.fase_actual = "lobby"
        self.sesion.save(update_fields=["fase_actual"])
        self.login_alumno()
        paginas.append(self.client.get(reverse("pantalla_espera")))
        for respuesta in paginas:
            self.assertEqual(respuesta.status_code, 200)
            enlace = ENLACE.search(respuesta.content.decode())
            self.assertIsNotNone(enlace)
            self.assertTrue(enlace.group(1).startswith("/static/images/favicon"), enlace.group(1))

    def test_la_ruta_raiz_sigue_funcionando_en_local(self):
        respuesta = self.client.get("/favicon.ico")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "image/x-icon")
