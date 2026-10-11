"""
Guard contra referencias estáticas rotas.

Con CompressedManifestStaticFilesStorage activo (producción), un
{% static 'x' %} que apunte a un archivo inexistente NO falla en
collectstatic: revienta con ValueError al renderizar la plantilla,
devolviendo un 500 al alumno.

En desarrollo (DEBUG=True) el backend simple no valida nada, así que
la referencia rota es invisible hasta que llega al servidor.

Estos tests recorren el árbol real de archivos y comparan contra cada
referencia declarada, sin depender de que collectstatic haya corrido.

Origen: 3b2a277 borró 'images/logo (3).webp' como huérfano sin ver que
registro.html lo usaba; el detector de huérfanos falló por el espacio y
los paréntesis del nombre. La página de registro quedó caída en 500.
"""

import os
import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

RAIZ = Path(settings.BASE_DIR)
STATIC = RAIZ / "juego" / "static"
PLANTILLAS = RAIZ / "juego" / "templates"

# {% static 'ruta' %} y {% static "ruta" %}
PATRON_TAG = re.compile(r"""\{%\s*static\s+['"]([^'"]+)['"]""")

# url(...) dentro de los CSS, con o sin comillas
PATRON_URL = re.compile(r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""")


def _inventario():
    """Rutas relativas de todo lo que existe bajo juego/static/."""
    archivos = set()

    for carpeta, _, nombres in os.walk(STATIC):
        for nombre in nombres:
            ruta = os.path.relpath(os.path.join(carpeta, nombre), STATIC)
            archivos.add(ruta.replace("\\", "/"))

    return archivos


class ReferenciasEstaticasTests(SimpleTestCase):
    """Toda referencia declarada debe corresponder a un archivo real."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.existentes = _inventario()

    def test_static_en_plantillas_existe(self):
        rotas = []

        for carpeta, _, nombres in os.walk(PLANTILLAS):
            for nombre in nombres:
                if not nombre.endswith(".html"):
                    continue

                ruta = Path(carpeta) / nombre
                texto = ruta.read_text(encoding="utf-8", errors="ignore")

                for coincidencia in PATRON_TAG.finditer(texto):
                    referencia = coincidencia.group(1)

                    # Rutas armadas en tiempo de render: no se pueden validar.
                    if "{{" in referencia or "{%" in referencia:
                        continue

                    if referencia in self.existentes:
                        continue

                    linea = texto[: coincidencia.start()].count("\n") + 1
                    relativa = ruta.relative_to(RAIZ)
                    rotas.append(f"{relativa}:{linea} -> {referencia}")

        self.assertEqual(
            rotas,
            [],
            "Referencias {% static %} sin archivo. En producción cada una "
            "es un 500 al renderizar:\n  " + "\n  ".join(rotas),
        )

    def test_url_en_css_existe(self):
        rotas = []

        for carpeta, _, nombres in os.walk(STATIC):
            for nombre in nombres:
                if not nombre.endswith(".css"):
                    continue

                ruta = Path(carpeta) / nombre
                texto = ruta.read_text(encoding="utf-8", errors="ignore")
                base = os.path.relpath(carpeta, STATIC).replace("\\", "/")

                for coincidencia in PATRON_URL.finditer(texto):
                    referencia = coincidencia.group(1).strip()
                    referencia = referencia.split("?")[0].split("#")[0]

                    if not referencia:
                        continue

                    if referencia.startswith(("http://", "https://", "//", "data:")):
                        continue

                    if referencia.startswith(settings.STATIC_URL):
                        destino = referencia[len(settings.STATIC_URL):]
                    elif referencia.startswith("/"):
                        # Absoluta fuera de STATIC_URL: la sirve otra cosa.
                        continue
                    else:
                        destino = os.path.normpath(os.path.join(base, referencia))
                        destino = destino.replace("\\", "/")

                    if destino in self.existentes:
                        continue

                    linea = texto[: coincidencia.start()].count("\n") + 1
                    relativa = ruta.relative_to(RAIZ)
                    rotas.append(f"{relativa}:{linea} -> {referencia}")

        self.assertEqual(
            rotas,
            [],
            "url() en CSS sin archivo. Rompen collectstatic en producción:\n  "
            + "\n  ".join(rotas),
        )

    def test_nombres_sin_espacios_ni_parentesis(self):
        """
        Los espacios y paréntesis en nombres de archivo rompen los scripts
        de detección de huérfanos y obligan a escapar en CSS. Fue la causa
        raíz del borrado accidental de 'logo (3).webp'.
        """
        problematicos = []

        for carpeta, _, nombres in os.walk(STATIC):
            for nombre in nombres:
                if re.search(r"[ ()]", nombre):
                    ruta = Path(carpeta) / nombre
                    problematicos.append(str(ruta.relative_to(RAIZ)))

        self.assertEqual(
            problematicos,
            [],
            "Archivos estáticos con espacios o paréntesis en el nombre:\n  "
            + "\n  ".join(problematicos),
        )
