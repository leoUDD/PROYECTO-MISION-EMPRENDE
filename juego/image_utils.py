from io import BytesIO
from uuid import uuid4

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError


def convertir_imagen_a_webp(uploaded_file, max_size=(1600, 1600), quality=75):
 
    try:
        imagen = Image.open(uploaded_file)
        imagen = ImageOps.exif_transpose(imagen)
    except UnidentifiedImageError:
        raise ValueError("El archivo subido no es una imagen válida.")

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

    nombre_archivo = f"{uuid4().hex}.webp"
    return nombre_archivo, ContentFile(buffer.getvalue())