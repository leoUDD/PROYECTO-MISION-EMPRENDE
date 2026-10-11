#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
optimizar_media.py - Paquete C2 de Mision Emprende UDD.

Reduce el peso de los videos y del audio estatico sin cambiar ni un solo
nombre de archivo, de modo que ninguna referencia {% static %} ni ninguna
regla CSS necesite tocarse.

Videos  (juego/static/videos/*.mp4):
    1080p -> 720p, H.264 preset slow CRF 26, audio AAC 96 kbps,
    metadatos eliminados, moov al inicio (+faststart).
    Los .webm se ignoran a proposito: TutorialProfesor.webm ya es VP9 a
    198 kbps y reencodearlo a H.264 lo haria mas pesado.

Audio   (juego/static/sounds/*.mp3):
    MP3 96 kbps joint-stereo a 44,1 kHz, sin caratula embebida y sin
    etiquetas ID3. Las caratulas PNG/JPEG incrustadas pesan 1,22 MB en
    total y se sirven a cada alumno sin que nadie las vea nunca.

El script es idempotente: si un archivo ya cumple el objetivo lo omite.
Nunca reemplaza un original por una version mas pesada.

Uso:
    py scripts/optimizar_media.py --dry-run
    py scripts/optimizar_media.py
    py scripts/optimizar_media.py --solo video
    py scripts/optimizar_media.py --solo audio
    py scripts/optimizar_media.py --ssim        (mide calidad, es lento)
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_VIDEOS = os.path.join(RAIZ, "juego", "static", "videos")
DIR_SONIDOS = os.path.join(RAIZ, "juego", "static", "sounds")

ALTURA_OBJETIVO = 720
CRF_VIDEO = 26
PRESET_VIDEO = "slow"
BITRATE_AUDIO_VIDEO = "96k"
BITRATE_AUDIO_MP3 = "96k"
SAMPLERATE_MP3 = "44100"

# Un MP3 se considera ya optimizado si esta por debajo de este bitrate
# y no arrastra caratula embebida.
UMBRAL_KBPS_MP3 = 100


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def mb(n):
    return "%.2f MB" % (n / 1048576.0)


def comprobar_ffmpeg():
    faltan = [b for b in ("ffmpeg", "ffprobe") if shutil.which(b) is None]
    if faltan:
        print("ERROR: no se encontro %s en el PATH." % " ni ".join(faltan))
        print("Instalalo con:  winget install Gyan.FFmpeg")
        print("Despues cierra y vuelve a abrir la terminal para refrescar el PATH.")
        sys.exit(1)


def sondear(ruta):
    """Devuelve el dict de ffprobe para un archivo, o None si falla."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,bit_rate,size",
        "-show_streams",
        "-of", "json", ruta,
    ]
    try:
        salida = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        print("  ffprobe fallo en %s: %s" % (ruta, e))
        return None
    return json.loads(salida)


def stream_de(info, tipo):
    for s in info.get("streams", []):
        if s.get("codec_type") == tipo:
            return s
    return None


def tiene_caratula(info):
    for s in info.get("streams", []):
        if s.get("codec_type") == "video":
            return True
    return False


def ejecutar_ffmpeg(cmd, etiqueta):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print("  ERROR al procesar %s" % etiqueta)
        print("  " + (proc.stderr or "").strip()[-800:])
        return False
    return True


def reemplazar_si_conviene(original, temporal):
    """Sustituye el original solo si el nuevo archivo es mas liviano."""
    antes = os.path.getsize(original)
    despues = os.path.getsize(temporal)
    if despues >= antes:
        os.remove(temporal)
        print("  OMITIDO: la version nueva (%s) no mejora la actual (%s)."
              % (mb(despues), mb(antes)))
        return 0
    os.replace(temporal, original)
    ahorro = antes - despues
    print("  %s -> %s  (-%s, %.0f%%)"
          % (mb(antes), mb(despues), mb(ahorro), 100.0 * ahorro / antes))
    return ahorro


def medir_ssim(original_backup, nuevo, ancho, alto):
    """SSIM del reencode reescalado contra el original. Devuelve float o None."""
    filtro = ("[1:v]scale=%d:%d:flags=lanczos[up];[0:v][up]ssim" % (ancho, alto))
    cmd = ["ffmpeg", "-v", "error", "-i", original_backup, "-i", nuevo,
           "-lavfi", filtro, "-f", "null", "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r"All:([0-9.]+)", proc.stderr or "")
    return float(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Videos
# ---------------------------------------------------------------------------

def procesar_videos(dry_run, con_ssim):
    if not os.path.isdir(DIR_VIDEOS):
        print("No existe %s, se omiten los videos." % DIR_VIDEOS)
        return 0

    ahorro_total = 0
    archivos = sorted(f for f in os.listdir(DIR_VIDEOS) if f.lower().endswith(".mp4"))
    if not archivos:
        print("No hay .mp4 en %s." % DIR_VIDEOS)
        return 0

    print("\n=== VIDEOS (%d archivos .mp4) ===" % len(archivos))
    for nombre in archivos:
        ruta = os.path.join(DIR_VIDEOS, nombre)
        info = sondear(ruta)
        if info is None:
            continue
        v = stream_de(info, "video")
        if v is None:
            print("%s: sin pista de video, se omite." % nombre)
            continue

        ancho = int(v.get("width") or 0)
        alto = int(v.get("height") or 0)
        peso = os.path.getsize(ruta)
        print("\n%s  (%dx%d, %s)" % (nombre, ancho, alto, mb(peso)))

        if alto <= ALTURA_OBJETIVO:
            print("  OMITIDO: ya esta a %dp o menos." % ALTURA_OBJETIVO)
            continue

        if dry_run:
            print("  [dry-run] se reencodearia a %dp CRF %d preset %s."
                  % (ALTURA_OBJETIVO, CRF_VIDEO, PRESET_VIDEO))
            continue

        temporal = ruta + ".tmp.mp4"
        cmd = [
            "ffmpeg", "-y", "-v", "error", "-i", ruta,
            "-map_metadata", "-1",
            "-vf", "scale=-2:%d:flags=lanczos" % ALTURA_OBJETIVO,
            "-c:v", "libx264", "-preset", PRESET_VIDEO, "-crf", str(CRF_VIDEO),
            "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", BITRATE_AUDIO_VIDEO, "-ac", "2",
            "-movflags", "+faststart",
            temporal,
        ]
        print("  Codificando (esto tarda; ~1-2x la duracion del video)...")
        if not ejecutar_ffmpeg(cmd, nombre):
            if os.path.exists(temporal):
                os.remove(temporal)
            continue

        if con_ssim:
            respaldo = ruta + ".orig"
            shutil.copy2(ruta, respaldo)
            valor = medir_ssim(respaldo, temporal, ancho, alto)
            os.remove(respaldo)
            if valor is not None:
                print("  SSIM medido: %.4f" % valor)

        ahorro_total += reemplazar_si_conviene(ruta, temporal)

    return ahorro_total


# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------

def procesar_audio(dry_run):
    if not os.path.isdir(DIR_SONIDOS):
        print("No existe %s, se omite el audio." % DIR_SONIDOS)
        return 0

    ahorro_total = 0
    archivos = sorted(f for f in os.listdir(DIR_SONIDOS) if f.lower().endswith(".mp3"))
    if not archivos:
        print("No hay .mp3 en %s." % DIR_SONIDOS)
        return 0

    print("\n=== AUDIO (%d archivos .mp3) ===" % len(archivos))
    for nombre in archivos:
        ruta = os.path.join(DIR_SONIDOS, nombre)
        info = sondear(ruta)
        if info is None:
            continue

        peso = os.path.getsize(ruta)
        bitrate = int(info.get("format", {}).get("bit_rate") or 0)
        kbps = bitrate / 1000.0
        caratula = tiene_caratula(info)
        print("\n%s  (%.0f kbps, %s%s)"
              % (nombre, kbps, mb(peso), ", con caratula embebida" if caratula else ""))

        if kbps and kbps <= UMBRAL_KBPS_MP3 and not caratula:
            print("  OMITIDO: ya esta a %d kbps o menos y sin caratula." % UMBRAL_KBPS_MP3)
            continue

        if dry_run:
            print("  [dry-run] se reencodearia a %s, %s Hz, sin caratula ni ID3."
                  % (BITRATE_AUDIO_MP3, SAMPLERATE_MP3))
            continue

        temporal = ruta + ".tmp.mp3"
        cmd = [
            "ffmpeg", "-y", "-v", "error", "-i", ruta,
            "-map", "0:a:0",
            "-map_metadata", "-1",
            "-c:a", "libmp3lame", "-b:a", BITRATE_AUDIO_MP3, "-ar", SAMPLERATE_MP3,
            "-write_xing", "1", "-id3v2_version", "3",
            temporal,
        ]
        if not ejecutar_ffmpeg(cmd, nombre):
            if os.path.exists(temporal):
                os.remove(temporal)
            continue

        ahorro_total += reemplazar_si_conviene(ruta, temporal)

    return ahorro_total


# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Paquete C2: optimizacion de video y audio.")
    p.add_argument("--dry-run", action="store_true",
                   help="Muestra que se haria sin tocar ningun archivo.")
    p.add_argument("--solo", choices=["video", "audio"], default=None,
                   help="Procesa solo videos o solo audio.")
    p.add_argument("--ssim", action="store_true",
                   help="Mide el SSIM de cada video reencodeado. Duplica el tiempo.")
    args = p.parse_args()

    comprobar_ffmpeg()

    total = 0
    if args.solo in (None, "video"):
        total += procesar_videos(args.dry_run, args.ssim)
    if args.solo in (None, "audio"):
        total += procesar_audio(args.dry_run)

    print("\n" + "=" * 60)
    if args.dry_run:
        print("Simulacion terminada. No se modifico ningun archivo.")
    else:
        print("Ahorro total: %s" % mb(total))
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
