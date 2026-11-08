from io import BytesIO
from uuid import uuid4

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def convertir_imagen_a_webp(uploaded_file, max_size=(1600, 1600), quality=75):
    """
    Convierte la imagen subida a WebP.

    Pillow lee los píxeles de forma diferida, así que un archivo truncado
    pasa Image.open y recién falla al procesarlo: toda la conversión debe
    quedar protegida. Cualquier fallo de lectura se informa como ValueError.
    """

    try:
        imagen = Image.open(uploaded_file)
        imagen = ImageOps.exif_transpose(imagen)

        if imagen.mode in ("RGBA", "LA", "P"):
            fondo = Image.new("RGB", imagen.size, (255, 255, 255))

            if imagen.mode == "P":
                imagen = imagen.convert("RGBA")

            fondo.paste(imagen, mask=imagen.split()[-1] if imagen.mode in ("RGBA", "LA") else None)
            imagen = fondo
        else:
            imagen = imagen.convert("RGB")

        imagen.thumbnail(max_size, Image.Resampling.LANCZOS)

        buffer = BytesIO()
        imagen.save(
            buffer,
            format="WEBP",
            quality=quality,
            method=6,
            optimize=True,
        )
    except (OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise ValueError("El archivo subido no es una imagen válida.") from exc

    nombre_archivo = f"{uuid4().hex}.webp"
    return nombre_archivo, ContentFile(buffer.getvalue())
