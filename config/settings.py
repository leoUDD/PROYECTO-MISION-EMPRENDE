"""
Django settings for config project.

Todas las opciones sensibles se controlan por variables de entorno (.env).

Variables relevantes:
    DJANGO_SECRET_KEY       Obligatoria en producción.
    DJANGO_DEBUG            "True" solo en desarrollo (por defecto: False).
    DJANGO_ALLOWED_HOSTS    Lista separada por comas (por defecto: localhost,127.0.0.1).
    DJANGO_CSRF_TRUSTED     Orígenes confiables separados por comas.
    DB_ENGINE               "sqlite" (por defecto) o "mysql".
    DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT   Solo para MySQL.
    CLAVE_ADMIN             Clave del panel de administración (obligatoria en producción).
"""

from pathlib import Path
import os
import sys
import pymysql

pymysql.install_as_MySQLdb()

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env_bool(nombre, defecto=False):
    return os.getenv(nombre, str(defecto)).strip().lower() in ("1", "true", "yes", "si", "sí")


DEBUG = _env_bool("DJANGO_DEBUG", False)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "").strip()

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-secret-unsafe-solo-desarrollo"
    else:
        raise RuntimeError(
            "DJANGO_SECRET_KEY es obligatoria en producción. "
            "Genera una con: python -c \"from django.core.management.utils import "
            "get_random_secret_key; print(get_random_secret_key())\""
        )

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "DJANGO_CSRF_TRUSTED",
        "http://localhost:8000,https://localhost:8000",
    ).split(",")
    if o.strip()
]

# ---------------------------------------------------------------------------
# Base de datos: SQLite en desarrollo, MySQL en producción (DB_ENGINE=mysql).
# ---------------------------------------------------------------------------
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").strip().lower()

if DB_ENGINE == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME", "mision_emprende"),
            "USER": os.getenv("DB_USER", "root"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
                # Evita datos corruptos silenciosos (fechas inválidas, truncamientos).
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'juego',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# juego/static/ ya lo descubre AppDirectoriesFinder porque 'juego' esta en
# INSTALLED_APPS. Declararlo tambien en STATICFILES_DIRS lo hacia recorrer dos
# veces y provocaba avisos de archivo duplicado en collectstatic.

# El manifiesto exige que collectstatic haya corrido: sin staticfiles.json,
# cualquier {% static %} lanza ValueError. Django fuerza DEBUG=False durante
# la suite de tests, asi que sin esta condicion 29 tests fallarian en un clon
# recien hecho. En desarrollo y en tests se usa el backend simple.
_EJECUTANDO_TESTS = "test" in sys.argv
_MANIFIESTO_ESTATICOS = not DEBUG and not _EJECUTANDO_TESTS

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if _MANIFIESTO_ESTATICOS
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

# Borra las copias sin hash de STATIC_ROOT: sin esto cada archivo quedaria
# duplicado y staticfiles/ pesaria el doble.
WHITENOISE_KEEP_ONLY_HASHED_FILES = True

# La lista por defecto de whitenoise 6.4 omite los formatos de audio, asi que
# gzipea los MP3 sin ganar nada. Se agregan a mano.
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = (
    "jpg", "jpeg", "png", "gif", "webp", "ico",
    "zip", "gz", "tgz", "bz2", "tbz", "xz", "br",
    "swf", "flv", "woff", "woff2",
    "3gp", "3gpp", "asf", "avi", "m4v", "mov", "mp4", "mpeg", "mpg", "webm", "wmv",
    "mp3", "m4a", "ogg", "opus", "wav",
)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# Seguridad HTTP: solo se endurece fuera de desarrollo.
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = _env_bool("DJANGO_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_HSTS_SECONDS", "3600"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # el JS del juego lee el token para los fetch POST
X_FRAME_OPTIONS = "DENY"

# ---------------------------------------------------------------------------
# Acceso a paneles de profesor / administración.
# ---------------------------------------------------------------------------
CLAVE_ADMIN = os.getenv("CLAVE_ADMIN", "").strip()

if not CLAVE_ADMIN:
    if DEBUG:
        CLAVE_ADMIN = "admin123"  # solo desarrollo
    else:
        raise RuntimeError("CLAVE_ADMIN es obligatoria en producción.")

# ---------------------------------------------------------------------------
# Logging: reemplaza los print() de depuración.
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[{levelname}] {asctime} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "loggers": {
        "juego": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
        },
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN", "").strip()
GOOGLE_DRIVE_ROOT_NAME = os.getenv("GOOGLE_DRIVE_ROOT_NAME", "Misión Emprende").strip()
GOOGLE_DRIVE_ROOT_FOLDER_ID = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID", "").strip()


# =====================================================
# Microsoft OneDrive / Graph
# =====================================================

MS_CLIENT_ID = os.getenv(
    "MS_CLIENT_ID",
    "",
).strip()

MS_TENANT_ID = os.getenv(
    "MS_TENANT_ID",
    "",
).strip()

MS_CLIENT_SECRET = os.getenv(
    "MS_CLIENT_SECRET",
    "",
).strip()

MS_REDIRECT_URI = os.getenv(
    "MS_REDIRECT_URI",
    "",
).strip()

ONEDRIVE_ROOT_FOLDER = os.getenv(
    "ONEDRIVE_ROOT_FOLDER",
    "Mision Emprende",
).strip()

MS_TOKEN_ENCRYPTION_KEY = os.getenv(
    "MS_TOKEN_ENCRYPTION_KEY",
    "",
).strip()


# =====================================================
# Celery / Redis
# =====================================================

CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    "redis://127.0.0.1:6379/0",
).strip()

CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

DEV_TOOLS_ENABLED = (
    os.getenv(
        "DEV_TOOLS_ENABLED",
        "False",
    ).strip().lower()
    in {"1", "true", "yes", "on"}
)