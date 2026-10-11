# juego/management/commands/crear_profesor.py
"""
Crea un profesor con clave de acceso, o actualiza la clave si el email ya existe.

Uso:
    python manage.py crear_profesor correo@udd.cl claveSegura --facultad "Ingeniería"
"""

from django.core.management.base import BaseCommand, CommandError

from juego.auth import asignar_clave_profesor, errores_de_clave
from juego.models import Profesor, Usuario


class Command(BaseCommand):
    help = "Crea un profesor (o actualiza su clave) para el login del panel."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)
        parser.add_argument("clave", type=str)
        parser.add_argument("--facultad", type=str, default="")
        parser.add_argument(
            "--forzar",
            action="store_true",
            help="Omite la validación de robustez de la clave.",
        )

    def handle(self, *args, **options):
        email = options["email"].strip()
        clave = options["clave"]
        facultad = options["facultad"].strip()

        if not options["forzar"]:
            errores = errores_de_clave(clave)
            if errores:
                raise CommandError(
                    "Clave demasiado débil: " + " ".join(errores)
                    + " (usa --forzar para omitir esta validación)"
                )

        profesor = Profesor.objects.filter(emailprofesor__iexact=email).first()

        if profesor:
            asignar_clave_profesor(profesor, clave)
            if facultad:
                profesor.facultad = facultad
                profesor.save(update_fields=["facultad"])
            self.stdout.write(self.style.SUCCESS(f"Clave actualizada para {email}."))
            return

        usuario = Usuario.objects.create(password="")
        profesor = Profesor.objects.create(
            usuario_idusuario=usuario,
            emailprofesor=email,
            facultad=facultad or None,
        )
        asignar_clave_profesor(profesor, clave)
        self.stdout.write(self.style.SUCCESS(f"Profesor {email} creado."))
