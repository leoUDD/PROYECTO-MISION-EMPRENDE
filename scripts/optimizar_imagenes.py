#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
optimizar_imagenes.py - Paquete C1 de Mision Emprende UDD.

Convierte a WebP los PNG de juego/static/images/ que estan referenciados
desde el codigo, reescribe todas las referencias en templates, CSS y JS, y
borra los PNG originales.

A diferencia del paquete C2, aqui SI cambian los nombres de archivo, asi que
la reescritura de referencias es parte del trabajo y no un efecto colateral.

Regla de seleccion:
  - Se convierte todo PNG bajo juego/static/images/ con al menos una
    referencia en un .html, .css o .js.
  - Los PNG sin ninguna referencia NO se tocan: se reportan y punto. El
    borrado de huerfanos fue trabajo del paquete A.
  - Los PNG de EXCLUIDOS no se tocan aunque parezcan huerfanos.

Uso:
    py scripts/optimizar_imagenes.py --dry-run
    py scripts/optimizar_imagenes.py
    py scripts/optimizar_imagenes.py --calidad 85
    py scripts/optimizar_imagenes.py --ssim     (requiere scikit-image)
"""

import argparse
import collections
import os
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

CALIDAD = 90
METODO = 6  # 0 rapido / 6 lento y mas compacto

# PNG que no se convierten nunca, con el motivo.
EXCLUIDOS = {
    # Tematica.image es un CharField y la plantilla hace {% static tema.image %}
    # con el valor que venga de la base de datos. Convertir el archivo sin
    # actualizar la fila de produccion deja la tematica sin imagen, y ningun
    # escaneo de codigo puede detectarlo.
    "tematicas/salud.png": "referenciada desde la base de datos (Tematica.image)",
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


def pngs_en_images():
    encontrados = []
    for dirpath, _dirnames, filenames in os.walk(DIR_IMAGENES):
        for nombre in filenames:
            if nombre.lower().endswith(".png"):
                completo = os.path.join(dirpath, nombre)
                clave = os.path.relpath(completo, DIR_IMAGENES).replace("\\", "/")
                encontrados.append((clave, completo))
    return sorted(encontrados)


def contar_referencias(nombres_png):
    """{nombre_archivo.png: {ruta_codigo: n_ocurrencias}}"""
    conteo = collections.defaultdict(dict)
    for ruta in archivos_de_codigo():
        try:
            with open(ruta, "r", encoding="utf-8", errors="replace") as fh:
                texto = fh.read()
        except OSError:
            continue
        for nombre in nombres_png:
            n = texto.count(nombre)
            if n:
                conteo[nombre][ruta] = n
    return conteo


def convertir(origen, destino, calidad):
    im = Image.open(origen)
    # Las imagenes en modo paleta con transparencia deben pasar por RGBA o
    # Pillow pierde el canal alfa al guardar en WebP.
    if im.mode in ("P", "LA"):
        im = im.convert("RGBA")
    elif im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGB")
    im.save(destino, "WEBP", quality=calidad, method=METODO)
    return im


def _plano(ruta):
    """Abre y aplana sobre blanco, para que el canal alfa no falsee el SSIM."""
    im = Image.open(ruta)
    if im.mode in ("P", "LA"):
        im = im.convert("RGBA")
    if im.mode == "RGBA":
        fondo = Image.new("RGB", im.size, (255, 255, 255))
        fondo.paste(im, mask=im.split()[3])
        return fondo
    return im.convert("RGB")


def medir_ssim(ruta_png, ruta_webp):
    try:
        import numpy as np
        from skimage.metrics import structural_similarity
    except ImportError:
        return None
    a = _plano(ruta_png)
    b = _plano(ruta_webp)
    return float(structural_similarity(np.asarray(a), np.asarray(b), channel_axis=2))


def main():
    p = argparse.ArgumentParser(description="Paquete C1: PNG -> WebP.")
    p.add_argument("--dry-run", action="store_true",
                   help="Muestra el plan sin escribir nada.")
    p.add_argument("--calidad", type=int, default=CALIDAD,
                   help="Calidad WebP, 0-100. Por defecto %d." % CALIDAD)
    p.add_argument("--ssim", action="store_true",
                   help="Mide SSIM de cada conversion. Requiere scikit-image.")
    args = p.parse_args()

    if not os.path.isdir(DIR_IMAGENES):
        print("ERROR: no existe %s" % DIR_IMAGENES)
        return 1

    todos = pngs_en_images()
    if not todos:
        print("No hay PNG en juego/static/images/. Nada que hacer.")
        return 0

    nombres = [os.path.basename(c) for c, _ in todos]
    refs = contar_referencias(nombres)

    a_convertir, huerfanos, excluidos = [], [], []
    for clave, ruta in todos:
        if clave in EXCLUIDOS:
            excluidos.append((clave, ruta))
        elif refs.get(os.path.basename(clave)):
            a_convertir.append((clave, ruta))
        else:
            huerfanos.append((clave, ruta))

    print("=" * 70)
    print("PLAN")
    print("=" * 70)
    print("PNG encontrados:     %d" % len(todos))
    print("A convertir:         %d" % len(a_convertir))
    print("Excluidos:           %d" % len(excluidos))
    print("Sin referencias:     %d (no se tocan)" % len(huerfanos))

    for clave, _ in excluidos:
        print("  EXCLUIDO  %-34s %s" % (clave, EXCLUIDOS[clave]))
    for clave, ruta in huerfanos:
        print("  HUERFANO  %-34s %s" % (clave, mb(os.path.getsize(ruta))))

    if not a_convertir:
        print("\nNo hay nada que convertir.")
        return 0

    print()
    print("=" * 70)
    print("CONVERSION (calidad %d)" % args.calidad)
    print("=" * 70)
    print("%-30s %10s %10s %8s" % ("archivo", "PNG", "WebP", "ahorro"))

    total_antes = total_despues = 0
    renombres = {}   # NombreArchivo.png -> NombreArchivo.webp
    valores_ssim = []

    for clave, ruta_png in a_convertir:
        ruta_webp = ruta_png[:-4] + ".webp"
        if os.path.exists(ruta_webp):
            print("  CONFLICTO: ya existe %s, se omite %s" % (rel(ruta_webp), clave))
            continue

        antes = os.path.getsize(ruta_png)
        if args.dry_run:
            print("%-30s %10s %10s %8s" % (clave, mb(antes), "?", "[dry-run]"))
            total_antes += antes
            continue

        convertir(ruta_png, ruta_webp, args.calidad)
        despues = os.path.getsize(ruta_webp)

        if despues >= antes:
            os.remove(ruta_webp)
            print("%-30s %10s %10s  OMITIDO, el WebP no mejora"
                  % (clave, mb(antes), mb(despues)))
            continue

        total_antes += antes
        total_despues += despues
        print("%-30s %10s %10s %7.0f%%"
              % (clave, mb(antes), mb(despues), 100.0 * (antes - despues) / antes))

        if args.ssim:
            v = medir_ssim(ruta_png, ruta_webp)
            if v is None:
                args.ssim = False
                print("  (scikit-image no esta instalado, se omite el SSIM)")
            else:
                valores_ssim.append((clave, v))

        renombres[os.path.basename(clave)] = os.path.basename(ruta_webp)

    if args.dry_run:
        print("-" * 70)
        print("%-30s %10s" % ("TOTAL a convertir", mb(total_antes)))
        print("\nSimulacion terminada. No se escribio nada.")
        return 0

    print("-" * 70)
    print("%-30s %10s %10s %7.0f%%"
          % ("TOTAL", mb(total_antes), mb(total_despues),
             100.0 * (total_antes - total_despues) / total_antes if total_antes else 0))

    if valores_ssim:
        vs = [v for _, v in valores_ssim]
        print("\nSSIM: %.4f - %.4f, media %.4f"
              % (min(vs), max(vs), sum(vs) / len(vs)))
        for clave, v in sorted(valores_ssim, key=lambda x: x[1])[:3]:
            print("  el mas bajo: %-30s %.4f" % (clave, v))

    # ---- Reescritura de referencias ------------------------------------
    print()
    print("=" * 70)
    print("REESCRITURA DE REFERENCIAS")
    print("=" * 70)

    tocados = 0
    sustituciones = 0
    for ruta in archivos_de_codigo():
        try:
            with open(ruta, "r", encoding="utf-8", errors="replace") as fh:
                original = fh.read()
        except OSError:
            continue
        texto = original
        n_local = 0
        for viejo, nuevo in renombres.items():
            k = texto.count(viejo)
            if k:
                texto = texto.replace(viejo, nuevo)
                n_local += k
        if texto != original:
            with open(ruta, "w", encoding="utf-8", newline="") as fh:
                fh.write(texto)
            tocados += 1
            sustituciones += n_local
            print("  %-56s %2d" % (rel(ruta), n_local))

    print("-" * 70)
    print("%d sustituciones en %d archivos." % (sustituciones, tocados))

    # ---- Borrado de los PNG --------------------------------------------
    print()
    print("=" * 70)
    print("BORRADO DE LOS PNG ORIGINALES")
    print("=" * 70)
    borrados = 0
    for clave, ruta_png in a_convertir:
        if os.path.basename(clave) in renombres and os.path.exists(ruta_png):
            os.remove(ruta_png)
            borrados += 1
    print("%d PNG eliminados." % borrados)

    print()
    print("=" * 70)
    print("Ahorro total: %s" % mb(total_antes - total_despues))
    print("Ahora corre:  py scripts/verificar_referencias.py")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
