"""Los nombres de equipo no deben insertarse como HTML sin escapar.

Los tests de Django no ejecutan JavaScript, así que se revisa el código de las
plantillas para que nadie reintroduzca una inserción insegura.
"""

import re
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import SimpleTestCase

PLANTILLAS = settings.BASE_DIR / "juego" / "templates"
CON_ESCAPE = (
    "control_sesion.html",
    "orden_presentacion.html",
    "presentar_pitch.html",
    "bubblemap.html",
)
# Un dato de usuario interpolado directamente dentro de un template literal.
INSERCION_INSEGURA = re.compile(r"\$\{(item\.nombre|nombre|textoCorto\(texto\))\}")


class EscaparHtmlTests(SimpleTestCase):
    def test_existe_el_script(self):
        self.assertTrue(finders.find("js/escapar_html.js"))

    def test_las_pantallas_cargan_el_script(self):
        for nombre in CON_ESCAPE:
            contenido = Path(PLANTILLAS / nombre).read_text(encoding="utf-8")
            self.assertIn("js/escapar_html.js", contenido, nombre)

    def test_no_hay_inserciones_sin_escapar(self):
        for nombre in CON_ESCAPE:
            contenido = Path(PLANTILLAS / nombre).read_text(encoding="utf-8")
            self.assertIsNone(INSERCION_INSEGURA.search(contenido), nombre)
