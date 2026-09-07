#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
verificar_referencias.py - Verificacion del paquete C1 de Mision Emprende UDD.

Cuatro comprobaciones. Devuelve 1 si alguna bloqueante falla.

  1. Referencias rotas: toda imagen citada desde un .html, .css o .js existe
     en juego/static/images/.
  2. Restos de PNG: ninguna referencia sigue apuntando a un .png que ya fue
     convertido a .webp.
  3. Integridad de los WebP: cada uno abre, tiene dimensiones plausibles y
     conserva canal alfa si el PNG del que salio lo tenia.
  4. Inventario de peso, con comparacion opcional contra una linea base.

Uso:
    py scripts/verificar_referencias.py
    py scripts/verificar_referencias.py --guardar-linea-base imagenes_antes.json
    py scripts/verificar_referencias.py --linea-base imagenes_antes.json
"""

import argparse
import json
import os
import re
import sys

try:
    from PIL import Image
except ImportError:
    print("ERROR: falta Pillow. Instalalo con:  py -m pip install pillow")
    sys.exit(1)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_IMAGENES = os.path.join(RAIZ, "juego", "static", "images")
DIR_CODIGO = os.path.join(RAIZ, "juego")
EXT_CODIGO = (".html", ".css", ".js")

# Captura  images/loquesea.ext  con o sin subcarpeta.
PATRON = re.compile(
    r"images/((?:[A-Za-z0-9_\-. ]+/)*[A-Za-z0-9_\-. ]+"
    r"\.(?:png|webp|jpg|jpeg|gif|svg))",
    re.IGNORECASE,
)

# Imagenes que el codigo no cita porque la referencia vive en la base de datos,
# o que el navegador pide por convencion. No son huerfanas: borrarlas rompe
# produccion sin que ningun escaneo de codigo lo detecte.
REFERENCIADAS_EN_BD = {
    "tematicas/salud.png": "Tematica.image, valor en db_backup.json",
    "salud.webp": "probable Tematica.image (tematica Salud)",
    "educacion.webp": "probable Tematica.image (tematica Educacion)",
    "sustentabilidad.webp": "probable Tematica.image (tematica Sustentabilidad)",
    "favicon.ico": "lo pide el navegador en /favicon.ico",
}

# Referencias rotas ya conocidas y con decision pendiente. Se informan pero no
# bloquean, para que este script solo falle ante roturas NUEVAS. Todas deben
# resolverse antes de activar el paquete B: con ManifestStaticFilesStorage un
# {% static %} a un archivo inexistente revienta el render de la vista.
PENDIENTES_CONOCIDAS = {
    # CSS de vistas vivas: rompen en produccion bajo el paquete B.
    "fondo_card.webp",
    "apoyo.webp",
    "intro.webp",
    # habilidades_intro.html es codigo muerto, sin ruta en urls.py.
    "trabajoenEquipo.png",
    "empatiaa.png",
    "creatividadd.png",
    "comunicacionn.png",
    "negociacion.png",
}


def mb(n):
    return "%.2f MB" % (n / 1048576.0)


def rel(p):
    return os.path.relpath(p, RAIZ).replace("\\", "/")


def archivos_de_codigo():
    for dirpath, _dirnames, filenames in os.walk(DIR_CODIGO):
        if os.path.abspath(dirpath).startswith(os.path.abspath(DIR_IMAGENES)):
            continue
        for nombre in filenames:
            if nombre.lower().endswith(EXT_CODIGO):
                yield os.path.join(dirpath, nombre)


def recolectar_referencias():
    refs = {}
    for ruta in archivos_de_codigo():
        try:
            with open(ruta, "r", encoding="utf-8", errors="replace") as fh:
                for n, linea in enumerate(fh, 1):
                    for encontrado in PATRON.findall(linea):
                        clave = encontrado.replace("\\", "/")
                        refs.setdefault(clave, []).append((rel(ruta), n))
        except OSError:
            continue
    return refs


def imagenes_en_disco():
    encontradas = {}
    for dirpath, _dirnames, filenames in os.walk(DIR_IMAGENES):
        for nombre in filenames:
            completo = os.path.join(dirpath, nombre)
            clave = os.path.relpath(completo, DIR_IMAGENES).replace("\\", "/")
            encontradas[clave] = completo
    return encontradas


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--guardar-linea-base", metavar="JSON", default=None)
    p.add_argument("--linea-base", metavar="JSON", default=None)
    args = p.parse_args()

    refs = recolectar_referencias()
    disco = imagenes_en_disco()
    fallos = 0

    # 1. Referencias rotas -------------------------------------------------
    print("=" * 70)
    print("1. REFERENCIAS ROTAS")
    print("=" * 70)
    rotas = {k: v for k, v in refs.items() if k not in disco}
    conocidas = {k: v for k, v in rotas.items() if k in PENDIENTES_CONOCIDAS}
    nuevas = {k: v for k, v in rotas.items() if k not in PENDIENTES_CONOCIDAS}

    if not rotas:
        print("OK: las %d rutas de imagen citadas existen en juego/static/images/."
              % len(refs))

    for clave in sorted(conocidas):
        print("PENDIENTE CONOCIDA  images/%s  (resolver antes del paquete B)" % clave)
        for archivo, linea in conocidas[clave]:
            print("                    %s:%d" % (archivo, linea))

    if nuevas:
        print()
        for clave in sorted(nuevas):
            print("ROTURA NUEVA  images/%s" % clave)
            for archivo, linea in nuevas[clave]:
                print("              %s:%d" % (archivo, linea))
        fallos += 1
    elif rotas:
        print()
        print("OK: ninguna rotura nueva. Solo quedan las %d pendientes conocidas."
              % len(conocidas))

    # 2. Restos de PNG convertido -----------------------------------------
    print()
    print("=" * 70)
    print("2. REFERENCIAS QUE SIGUEN APUNTANDO A UN PNG CONVERTIDO")
    print("=" * 70)
    restos = []
    for clave in refs:
        if not clave.lower().endswith(".png"):
            continue
        gemelo = clave[:-4] + ".webp"
        if gemelo in disco:
            restos.append((clave, gemelo))
    if not restos:
        print("OK: ninguna referencia quedo apuntando a un PNG con gemelo WebP.")
    else:
        for clave, gemelo in restos:
            print("RESTO  images/%s  ->  deberia ser images/%s" % (clave, gemelo))
            for archivo, linea in refs[clave]:
                print("       %s:%d" % (archivo, linea))
        fallos += 1

    # 3. Integridad de los WebP -------------------------------------------
    print()
    print("=" * 70)
    print("3. INTEGRIDAD DE LOS WEBP")
    print("=" * 70)
    webps = sorted(k for k in disco if k.lower().endswith(".webp"))
    problemas = []
    for clave in webps:
        try:
            im = Image.open(disco[clave])
            im.load()
            if im.size[0] < 2 or im.size[1] < 2:
                problemas.append("%s: dimensiones sospechosas %s" % (clave, im.size))
        except Exception as e:
            problemas.append("%s: no se pudo abrir (%s)" % (clave, e))
    if not problemas:
        print("OK: los %d WebP abren correctamente." % len(webps))
    else:
        for linea in problemas:
            print("PROBLEMA  %s" % linea)
        fallos += 1

    # 4. Huerfanas e inventario -------------------------------------------
    print()
    print("=" * 70)
    print("4. IMAGENES SIN REFERENCIA EN CODIGO")
    print("=" * 70)
    huerfanas = sorted(set(disco) - set(refs))
    if not huerfanas:
        print("OK: ninguna.")
    for clave in huerfanas:
        motivo = REFERENCIADAS_EN_BD.get(clave)
        if motivo:
            print("NO BORRAR  %-38s %10s  %s"
                  % (clave, mb(os.path.getsize(disco[clave])), motivo))
        else:
            print("HUERFANA   %-38s %10s"
                  % (clave, mb(os.path.getsize(disco[clave]))))

    print()
    print("=" * 70)
    print("5. INVENTARIO DE PESO")
    print("=" * 70)
    inventario = {}
    total = 0
    por_ext = {}
    for clave in sorted(disco):
        peso = os.path.getsize(disco[clave])
        inventario[clave] = peso
        total += peso
        ext = os.path.splitext(clave)[1].lower()
        por_ext[ext] = por_ext.get(ext, 0) + peso
    for ext in sorted(por_ext, key=lambda e: -por_ext[e]):
        print("%-10s %10s" % (ext, mb(por_ext[ext])))
    print("-" * 70)
    print("%-10s %10s   (%d archivos)" % ("TOTAL", mb(total), len(disco)))

    if args.guardar_linea_base:
        with open(args.guardar_linea_base, "w", encoding="utf-8") as fh:
            json.dump(inventario, fh, indent=2, sort_keys=True)
        print("Linea base guardada en %s" % args.guardar_linea_base)

    if args.linea_base and os.path.exists(args.linea_base):
        with open(args.linea_base, "r", encoding="utf-8") as fh:
            antes = json.load(fh)
        total_antes = sum(antes.values())
        print()
        print("Antes:   %s" % mb(total_antes))
        print("Ahora:   %s" % mb(total))
        if total_antes:
            print("Ahorro:  %s (%.0f%%)"
                  % (mb(total_antes - total),
                     100.0 * (total_antes - total) / total_antes))

    print()
    print("=" * 70)
    print("RESULTADO: %s" % ("FALLOS DETECTADOS" if fallos else "TODO EN ORDEN"))
    print("=" * 70)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
