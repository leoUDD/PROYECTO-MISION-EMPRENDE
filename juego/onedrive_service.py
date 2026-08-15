import msal
import requests

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

from .models import OneDriveAuth


GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

SCOPES = [
    "Files.ReadWrite",
    "User.Read",
]

ONEDRIVE_USERNAME = "emprendimiento@udd.cl"


def _obtener_fernet():
    clave = settings.MS_TOKEN_ENCRYPTION_KEY

    if not clave:
        raise RuntimeError(
            "MS_TOKEN_ENCRYPTION_KEY no está configurada."
        )

    return Fernet(clave.encode("utf-8"))


def _cargar_cache():
    cache = msal.SerializableTokenCache()

    registro = (
        OneDriveAuth.objects
        .order_by("pk")
        .first()
    )

    if not registro:
        return cache

    if not registro.token_cache_encriptado:
        return cache

    try:
        contenido = _obtener_fernet().decrypt(
            registro.token_cache_encriptado.encode("utf-8")
        )

        cache.deserialize(
            contenido.decode("utf-8")
        )

    except InvalidToken as exc:
        raise RuntimeError(
            "No fue posible descifrar la autorización de OneDrive."
        ) from exc

    return cache


def _guardar_cache(cache, forzar=False):
    if not forzar and not cache.has_state_changed:
        return

    contenido = cache.serialize().encode("utf-8")

    contenido_cifrado = (
        _obtener_fernet()
        .encrypt(contenido)
        .decode("utf-8")
    )

    registro = (
        OneDriveAuth.objects
        .order_by("pk")
        .first()
    )

    if not registro:
        registro = OneDriveAuth()

    registro.token_cache_encriptado = contenido_cifrado
    registro.save()


def _crear_app(cache):
    return msal.ConfidentialClientApplication(
        client_id=settings.MS_CLIENT_ID,
        authority=(
            "https://login.microsoftonline.com/"
            f"{settings.MS_TENANT_ID}"
        ),
        client_credential=settings.MS_CLIENT_SECRET,
        token_cache=cache,
    )


def iniciar_autorizacion():
    cache = _cargar_cache()
    app = _crear_app(cache)

    flow = app.initiate_auth_code_flow(
        scopes=SCOPES,
        redirect_uri=settings.MS_REDIRECT_URI,
        login_hint=ONEDRIVE_USERNAME,
    )

    if "auth_uri" not in flow:
        raise RuntimeError(
            "Microsoft no pudo iniciar el flujo de autorización."
        )

    return flow


def completar_autorizacion(flow, respuesta):
    cache = _cargar_cache()
    app = _crear_app(cache)

    try:
        resultado = app.acquire_token_by_auth_code_flow(
            flow,
            respuesta,
        )

    except ValueError as exc:
        raise RuntimeError(
            "Microsoft rechazó la respuesta de autenticación."
        ) from exc

    if "access_token" not in resultado:
        descripcion = resultado.get(
            "error_description",
            resultado.get(
                "error",
                "No fue posible obtener autorización."
            ),
        )

        raise RuntimeError(descripcion)

    _guardar_cache(
        cache,
        forzar=True,
    )

    return resultado


def obtener_access_token():
    cache = _cargar_cache()
    app = _crear_app(cache)

    cuentas = app.get_accounts(
        username=ONEDRIVE_USERNAME
    )

    if not cuentas:
        cuentas = app.get_accounts()

    if not cuentas:
        raise RuntimeError(
            "OneDrive todavía no está autorizado. "
            "Ingresa primero a /onedrive/conectar/."
        )

    resultado = app.acquire_token_silent(
        SCOPES,
        account=cuentas[0],
    )

    # Si MSAL renovó el token,
    # persistimos nuevamente el cache.
    _guardar_cache(cache)

    if not resultado:
        raise RuntimeError(
            "No fue posible obtener un token de OneDrive. "
            "Es necesario volver a autorizar la cuenta."
        )

    if "access_token" not in resultado:
        descripcion = resultado.get(
            "error_description",
            resultado.get(
                "error",
                "No fue posible obtener el token."
            ),
        )

        raise RuntimeError(descripcion)

    return resultado["access_token"]


def obtener_usuario_onedrive():
    token = obtener_access_token()

    respuesta = requests.get(
        f"{GRAPH_BASE_URL}/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
        timeout=30,
    )

    respuesta.raise_for_status()

    return respuesta.json()