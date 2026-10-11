#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
verificar_media.py - Verificacion del paquete C2 de Mision Emprende UDD.

Hace cuatro comprobaciones y devuelve codigo de salida 1 si alguna falla
de forma bloqueante:

  1. Referencias rotas: todo archivo de video o audio citado en un template,
     un CSS o un JS existe realmente en juego/static/.
  2. Huerfanos: archivos de video o audio que no cita nadie.
  3. Objetivos C2: ningun MP4 por encima de 720p, ningun MP3 por encima de
     100 kbps, ningun MP3 con caratula embebida.
  4. Inventario de peso, con el total antes y despues si se le pasa
     --linea-base con el JSON generado por una corrida previa.

Uso:
    py scripts/verificar_media.py
    py scripts/verificar_media.py --guardar-linea-base media_antes.json
    py scripts/verificar_media.py --linea-base media_antes.json
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_STATIC = os.path.join(RAIZ, "juego", "static")
DIRS_A_ESCANEAR = [
    os.path.join(RAIZ, "juego", "templates"),
    os.path.join(RAIZ, "juego", "static", "css"),
    os.path.join(RAIZ, "juego", "static", "js"),
]
EXT_CODIGO = (".html", ".css", ".js", ".py")
EXT_MEDIA = (".mp4", ".webm", ".mov", ".mp3", ".wav", ".ogg", ".m4a")

# Captura rutas tipo  videos/Viaje.mp4  o  sounds/alarma.mp3  o  audio/x.mp3
PATRON = re.compile(
    r"((?:videos|sounds|audio|media)/[A-Za-z0-9_\-.]+"
    r"\.(?:mp4|webm|mov|mp3|wav|ogg|m4a))",
    re.IGNORECASE,
)

UMBRAL_KBPS_MP3 = 100
ALTURA_MAXIMA = 720

# Referencias rotas ya conocidas y con decision pendiente. Se informan pero
# no bloquean, para que este script solo falle ante roturas NUEVAS.
# Todas deben resolverse antes de activar el paquete B: con
# ManifestStaticFilesStorage, un {% static %} apuntando a un archivo
# inexistente revienta el render de la vista.
PENDIENTES_CONOCIDAS = {
    # bubblemap.html es una vista viva: esta rompe en produccion bajo B.
    "audio/success.mp3",
    # habilidades_intro.html es codigo muerto (sin ruta en urls.py).
    "videos/TeamWork.webm",
    "videos/Empatia.webm",
    "videos/Creatividad.webm",
    "videos/Comunicacion.webm",
    "videos/Negociacion.webm",
}


def mb(n):
    return "%.2f MB" % (n / 1048576.0)


def archivos_de_codigo():
    for base in DIRS_A_ESCANEAR:
        if not os.path.isdir(base):
            continue
        for dirpath, _dirnames, filenames in os.walk(base):
            for nombre in filenames:
                if nombre.lower().endswith(EXT_CODIGO):
                    yield os.path.join(dirpath, nombre)


def recolectar_referencias():
    """{ruta_relativa_static: [ (archivo, linea), ... ]}"""
    refs = {}
    for ruta in archivos_de_codigo():
        try:
            with open(ruta, "r", encoding="utf-8", errors="replace") as fh:
                for n, linea in enumerate(fh, 1):
                    for encontrado in PATRON.findall(linea):
                        clave = encontrado.replace("\\", "/")
                        refs.setdefault(clave, []).append(
                            (os.path.relpath(ruta, RAIZ), n)
                        )
        except OSError as e:
            print("  aviso: no se pudo leer %s (%s)" % (ruta, e))
    return refs


def archivos_media_en_static():
    encontrados = []
    for dirpath, _dirnames, filenames in os.walk(DIR_STATIC):
        for nombre in filenames:
            if nombre.lower().endswith(EXT_MEDIA):
                completo = os.path.join(dirpath, nombre)
                encontrados.append(
                    os.path.relpath(completo, DIR_STATIC).replace("\\", "/")
                )
    return sorted(encontrados)


def sondear(ruta):
    if shutil.which("ffprobe") is None:
        return None
    cmd = ["ffprobe", "-v", "error",
           "-show_entries", "format=duration,bit_rate,size",
           "-show_streams", "-of", "json", ruta]
    try:
        salida = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None
    return json.loads(salida)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--guardar-linea-base", metavar="JSON", default=None)
    p.add_argument("--linea-base", metavar="JSON", default=None)
    args = p.parse_args()

    refs = recolectar_referencias()
    presentes = set(archivos_media_en_static())
    fallos = 0

    # 1. Referencias rotas -------------------------------------------------
    print("=" * 68)
    print("1. REFERENCIAS ROTAS")
    print("=" * 68)
    rotas = {k: v for k, v in refs.items() if k not in presentes}
    # media/ se sirve desde MEDIA_ROOT, no desde static: no es un fallo aqui.
    rotas = {k: v for k, v in rotas.items() if not k.startswith("media/")}
    conocidas = {k: v for k, v in rotas.items() if k in PENDIENTES_CONOCIDAS}
    nuevas = {k: v for k, v in rotas.items() if k not in PENDIENTES_CONOCIDAS}

    if not rotas:
        print("OK: las %d rutas de media citadas existen en juego/static/."
              % len(refs))

    for clave in sorted(conocidas):
        print("PENDIENTE CONOCIDA  %s  (no bloquea, resolver antes del paquete B)"
              % clave)
        for archivo, linea in conocidas[clave]:
            print("                    citado en %s:%d" % (archivo, linea))

    if nuevas:
        print()
        for clave in sorted(nuevas):
            print("ROTURA NUEVA  %s" % clave)
            for archivo, linea in nuevas[clave]:
                print("              citado en %s:%d" % (archivo, linea))
        fallos += 1
    elif rotas:
        print()
        print("OK: ninguna rotura nueva. Solo quedan las pendientes conocidas.")

    # 2. Huerfanos ---------------------------------------------------------
    print()
    print("=" * 68)
    print("2. ARCHIVOS SIN NINGUNA REFERENCIA")
    print("=" * 68)
    huerfanos = sorted(presentes - set(refs))
    if not huerfanos:
        print("OK: no hay media huerfana.")
    else:
        total_huerfano = 0
        for clave in huerfanos:
            peso = os.path.getsize(os.path.join(DIR_STATIC, clave))
            total_huerfano += peso
            print("HUERFANO  %-42s %s" % (clave, mb(peso)))
        print("Peso muerto: %s (aviso, no bloquea)" % mb(total_huerfano))

    # 3. Objetivos C2 ------------------------------------------------------
    print()
    print("=" * 68)
    print("3. OBJETIVOS DEL PAQUETE C2")
    print("=" * 68)
    if shutil.which("ffprobe") is None:
        print("ffprobe no esta en el PATH: se omite esta comprobacion.")
    else:
        incumplen = []
        for clave in sorted(presentes):
            ruta = os.path.join(DIR_STATIC, clave)
            info = sondear(ruta)
            if info is None:
                continue
            fmt = info.get("format", {})
            kbps = (int(fmt.get("bit_rate") or 0)) / 1000.0
            pistas_video = [s for s in info.get("streams", [])
                            if s.get("codec_type") == "video"]

            if clave.lower().endswith(".mp4"):
                for s in pistas_video:
                    alto = int(s.get("height") or 0)
                    if alto > ALTURA_MAXIMA:
                        incumplen.append("%s: %dp, por encima de %dp"
                                         % (clave, alto, ALTURA_MAXIMA))
            elif clave.lower().endswith(".mp3"):
                if kbps > UMBRAL_KBPS_MP3:
                    incumplen.append("%s: %.0f kbps, por encima de %d"
                                     % (clave, kbps, UMBRAL_KBPS_MP3))
                if pistas_video:
                    incumplen.append("%s: conserva caratula embebida" % clave)

        if not incumplen:
            print("OK: todos los MP4 estan a %dp o menos y todos los MP3 "
                  "a %d kbps o menos, sin caratulas." % (ALTURA_MAXIMA, UMBRAL_KBPS_MP3))
        else:
            for linea in incumplen:
                print("INCUMPLE  %s" % linea)
            fallos += 1

    # 4. Inventario de peso ------------------------------------------------
    print()
    print("=" * 68)
    print("4. INVENTARIO DE PESO")
    print("=" * 68)
    inventario = {}
    total = 0
    for clave in sorted(presentes):
        peso = os.path.getsize(os.path.join(DIR_STATIC, clave))
        inventario[clave] = peso
        total += peso
        print("%-46s %10s" % (clave, mb(peso)))
    print("-" * 68)
    print("%-46s %10s" % ("TOTAL media en juego/static/", mb(total)))

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
    print("=" * 68)
    print("RESULTADO: %s" % ("FALLOS DETECTADOS" if fallos else "TODO EN ORDEN"))
    print("=" * 68)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
