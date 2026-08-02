# juego/auth.py
"""
Autenticación server-side para los paneles de profesor y administración.

Reemplaza el modal JavaScript de perfiles.html, que validaba contraseñas
hardcodeadas en el cliente y era trivialmente evitable.

Roles:
    - Profesor: se autentica con su email y una clave propia, almacenada
      hasheada en Usuario.password (hashers de Django).
    - Admin: se autentica con la clave global settings.CLAVE_ADMIN.

Estado en sesión:
    request.session["profesor_id"]  -> id del profesor autenticado.
    request.session["es_admin"]     -> True si entró como administrador.

Decoradores:
    @requiere_staff   -> profesor autenticado o admin.
    @requiere_admin   -> solo admin.

Ambos decoradores responden JSON 403 a peticiones AJAX/JSON y redirigen
al login en peticiones normales de navegador.
"""



from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Profesor


# ---------------------------------------------------------------------------
# Helpers de estado
# ---------------------------------------------------------------------------

def profesor_autenticado(request):
    """Devuelve el Profesor autenticado en esta sesión, o None."""
    profesor_id = request.session.get("profesor_id")

    if not profesor_id:
        return None

    return Profesor.objects.filter(pk=profesor_id).first()


def es_admin(request):
    return bool(request.session.get("es_admin"))


def es_staff(request):
    """Admin, o un profesor que EXISTE en la base.

    Verificar la existencia evita sesiones fantasma: si el admin elimina a un
    profesor logueado, su profesor_id en sesión deja de ser válido.
    """
    if es_admin(request):
        return True

    return profesor_autenticado(request) is not None


def _es_peticion_json(request):
    """Heurística para responder 403 JSON en vez de redirect en llamadas fetch."""
    accept = request.headers.get("Accept", "")
    content_type = request.headers.get("Content-Type", "")
    requested_with = request.headers.get("X-Requested-With", "")

    return (
        "application/json" in accept
        or "application/json" in content_type
        or requested_with == "XMLHttpRequest"
    )


def _denegar(request):
    if _es_peticion_json(request):
        return JsonResponse(
            {"ok": False, "error": "Acceso restringido. Inicia sesión como profesor o administrador."},
            status=403,
        )

    login_url = reverse("login_acceso")
    query = urlencode({"next": request.get_full_path()})
    return redirect(f"{login_url}?{query}")


# ---------------------------------------------------------------------------
# Decoradores
# ---------------------------------------------------------------------------

def requiere_staff(view_func):
    """Permite el acceso a profesores autenticados y al administrador."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if es_staff(request):
            return view_func(request, *args, **kwargs)
        return _denegar(request)

    return _wrapped


def requiere_admin(view_func):
    """Permite el acceso solo al administrador."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if es_admin(request):
            return view_func(request, *args, **kwargs)
        return _denegar(request)

    return _wrapped


# ---------------------------------------------------------------------------
# Validación de claves
# ---------------------------------------------------------------------------

def errores_de_clave(clave_plana):
    """Valida la robustez de la clave.

    Requisitos: mínimo 8 caracteres, con letras, números y símbolos.
    Además aplica los AUTH_PASSWORD_VALIDATORS de settings (claves
    comunes, similitud, etc.).

    Devuelve una lista de mensajes de error; vacía si la clave es aceptable.
    """
    errores = []

    try:
        validate_password(clave_plana)
    except ValidationError as exc:
        errores.extend(exc.messages)

    if not any(c.isalpha() for c in clave_plana):
        errores.append("La clave debe incluir al menos una letra.")

    if not any(c.isdigit() for c in clave_plana):
        errores.append("La clave debe incluir al menos un número.")

    if not any(not c.isalnum() for c in clave_plana):
        errores.append("La clave debe incluir al menos un símbolo (p. ej. - _ . ! #).")

    return errores


# ---------------------------------------------------------------------------
# Gestión de claves de profesor
# ---------------------------------------------------------------------------

def asignar_clave_profesor(profesor, clave_plana):
    """Hashea y guarda la clave en el Usuario asociado al profesor."""
    usuario = profesor.usuario_idusuario
    usuario.password = make_password(clave_plana)
    usuario.save(update_fields=["password"])


def verificar_clave_profesor(profesor, clave_plana):
    usuario = profesor.usuario_idusuario

    if not usuario or not usuario.password:
        return False

    # Las cuentas antiguas guardaban "temp" en texto plano: nunca son válidas.
    if not usuario.password.startswith(("pbkdf2_", "argon2", "bcrypt", "scrypt")):
        return False

    return check_password(clave_plana, usuario.password)


# ---------------------------------------------------------------------------
# Vistas de login / logout
# ---------------------------------------------------------------------------

def _redireccion_segura(request, defecto):
    destino = request.POST.get("next") or request.GET.get("next") or ""

    if destino and url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(destino)

    return redirect(defecto)


def login_acceso(request):
    rol_inicial = request.GET.get("rol", "profesor")

    if request.method == "POST":
        rol = (request.POST.get("rol") or "").strip()
        clave = request.POST.get("clave") or ""

        if rol == "admin":
            if settings.CLAVE_ADMIN and constant_time_compare(clave, settings.CLAVE_ADMIN):
                request.session["es_admin"] = True
                request.session.modified = True
                return _redireccion_segura(request, "dashboardadmin")

            messages.error(request, "Clave de administrador incorrecta.")

        elif rol == "profesor":
            email = (request.POST.get("email") or "").strip()
            profesor = Profesor.objects.filter(emailprofesor__iexact=email).first()

            if profesor and verificar_clave_profesor(profesor, clave):
                request.session["profesor_id"] = profesor.idprofesor
                request.session.modified = True
                return _redireccion_segura(request, "dashboardprofesor")

            messages.error(request, "Email o clave incorrectos.")

        else:
            messages.error(request, "Rol de acceso inválido.")

        rol_inicial = rol or rol_inicial

    return render(request, "login_acceso.html", {
        "rol_inicial": rol_inicial,
        "next": request.GET.get("next", ""),
    })


def logout_acceso(request):
    request.session.pop("profesor_id", None)
    request.session.pop("es_admin", None)
    request.session.modified = True
    messages.success(request, "Sesión de acceso cerrada.")
    return redirect("perfiles")
