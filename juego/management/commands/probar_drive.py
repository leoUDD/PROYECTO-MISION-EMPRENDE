from django.conf import settings
from django.core.management.base import BaseCommand

from juego.drive_service import (
    FOLDER_MIME_TYPE,
    construir_servicio_drive,
)


class Command(BaseCommand):
    help = "Prueba la conexión con Drive y crea la carpeta principal."

    def handle(self, *args, **options):
        self.stdout.write(
            "Conectando con Google Drive..."
        )

        servicio = construir_servicio_drive()

        nombre_carpeta = settings.GOOGLE_DRIVE_ROOT_NAME
        nombre_consulta = nombre_carpeta.replace(
            "'",
            "\\'",
        )

        consulta = (
            f"name = '{nombre_consulta}' and "
            f"mimeType = '{FOLDER_MIME_TYPE}' and "
            "trashed = false"
        )

        resultado = servicio.files().list(
            q=consulta,
            spaces="drive",
            fields="files(id, name)",
            pageSize=10,
        ).execute()

        carpetas = resultado.get("files", [])

        if carpetas:
            carpeta = carpetas[0]

            self.stdout.write(
                self.style.WARNING(
                    "La carpeta ya existía."
                )
            )
        else:
            carpeta = servicio.files().create(
                body={
                    "name": nombre_carpeta,
                    "mimeType": FOLDER_MIME_TYPE,
                },
                fields="id, name",
            ).execute()

            self.stdout.write(
                self.style.SUCCESS(
                    "La carpeta fue creada correctamente."
                )
            )

        carpeta_id = carpeta["id"]

        self.stdout.write(
            self.style.SUCCESS(
                f"Nombre: {carpeta['name']}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"ID: {carpeta_id}"
            )
        )

        self.stdout.write("")
        self.stdout.write(
            "Agrega esto a tu archivo .env:"
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'GOOGLE_DRIVE_ROOT_FOLDER_ID="{carpeta_id}"'
            )
        )