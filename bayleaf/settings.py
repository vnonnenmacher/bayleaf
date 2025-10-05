"""
Django settings for bayleaf project.
"""

from datetime import timedelta
from pathlib import Path
import json
import os


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def env(name: str, default=None, required: bool = False):
    """
    Small env getter:
    - If required=True and value is missing -> raises RuntimeError.
    - Otherwise returns default when missing.
    Why? It keeps secrets and per-env config out of code and
    lets us switch behavior (keys, issuer, lifetimes) without edits.
    """
    val = os.getenv(name, default)
    if required and (val is None or val == ""):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


# ------------------------------------------------------------
# Paths / core Django bits
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-l4z&5z%2v0$53dv**=h@2k-*wr$_(spmsmpd+13k_fbrteb(ju",
)

DEBUG = os.getenv("DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# ------------------------------------------------------------
# Apps
# ------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",  # you use its DRF backend
    "corsheaders",
    "users",
    "patients",
    "core",
    "appointments",
    "events",
    "lab",
    "professionals",
    "drf_yasg",
    "prescriptions",
    "medications",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # put it near the top
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bayleaf.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "libraries": {
                "staticfiles": "django.templatetags.static",
            },
        },
    },
]

WSGI_APPLICATION = "bayleaf.wsgi.application"

# ------------------------------------------------------------
# Database (sqlite for now)
# ------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "bayleaf",           # same as POSTGRES_DB in docker-compose
        "USER": "bayleaf",           # same as POSTGRES_USER
        "PASSWORD": "bayleaf",       # same as POSTGRES_PASSWORD
        "HOST": "db",                # service name from docker-compose.yml
        "PORT": "5432",              # default Postgres port
    }
}
# ------------------------------------------------------------
# Password validation
# ------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------
# i18n
# ------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------
# Static / media
# ------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

# ------------------------------------------------------------
# REST Framework
# ------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    # We'll later wire throttles for token-exchange; rates are set below.
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
}

# Throttle buckets we’ll use when we add /auth/token-exchange/
REST_FRAMEWORK.setdefault("DEFAULT_THROTTLE_RATES", {})
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].update(
    {
        "token_exchange": os.getenv("THROTTLE_TOKEN_EXCHANGE", "10/min"),
        "client_credentials": os.getenv("THROTTLE_CLIENT_CREDENTIALS", "10/min"),
    }
)

# ------------------------------------------------------------
# JWT / OBO config (RS256 rotation-ready)
# ------------------------------------------------------------
# Public constants other services will rely on:
BAYLEAF_ISSUER = env("BAYLEAF_ISSUER", "https://auth.bayleaf.local")
BAYLEAF_AUDIENCE_AGENT = env("BAYLEAF_AUDIENCE_AGENT", "agent")
BAYLEAF_AUDIENCE_API = env("BAYLEAF_AUDIENCE_API", "bayleaf-api")
BAYLEAF_ACTIVE_KID = env("BAYLEAF_ACTIVE_KID", "key-dev")
BAYLEAF_OLD_PUBKEYS_JSON = env("BAYLEAF_OLD_PUBKEYS_JSON", "[]")
BAYLEAF_OLD_PUBKEYS = json.loads(BAYLEAF_OLD_PUBKEYS_JSON)

# Lifetimes
ACCESS_MIN = int(env("BAYLEAF_ACCESS_LIFETIME_MIN", "30"))
REFRESH_MIN = int(env("BAYLEAF_REFRESH_LIFETIME_MIN", str(60 * 24 * 7)))  # 7 days
OBO_MIN = int(env("BAYLEAF_OBO_LIFETIME_MIN", "5"))  # short-lived OBO

# Keys (RS256 preferred). For dev, we allow falling back to HS256 if keys absent.
RSA_PRIVATE = os.getenv("BAYLEAF_RSA_PRIVATE_KEY")  # PEM
RSA_PUBLIC = os.getenv("BAYLEAF_RSA_PUBLIC_KEY")    # PEM

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

if RSA_PRIVATE and RSA_PUBLIC:
    # RS256 (prod-ready)
    SIMPLE_JWT.update(
        {
            "ALGORITHM": "RS256",
            "SIGNING_KEY": RSA_PRIVATE,
            "VERIFYING_KEY": RSA_PUBLIC,
            "ACCESS_TOKEN_LIFETIME": timedelta(minutes=ACCESS_MIN),
            "REFRESH_TOKEN_LIFETIME": timedelta(minutes=REFRESH_MIN),
            # We’ll mint OBO tokens manually with RS256 as well.
        }
    )
else:
    # Dev fallback to HS256 so local runs without PEMs.
    SIMPLE_JWT.update(
        {
            "ALGORITHM": "HS256",
            "SIGNING_KEY": env("DJANGO_SECRET_KEY", SECRET_KEY),
            "ACCESS_TOKEN_LIFETIME": timedelta(minutes=ACCESS_MIN),
            "REFRESH_TOKEN_LIFETIME": timedelta(minutes=REFRESH_MIN),
        }
    )

# Expose OBO lifetime for the view we’ll add later
BAYLEAF_OBO_LIFETIME_SECONDS = OBO_MIN * 60

# Optional service credentials for client-credentials flow (used later)
AGENT_CLIENT_ID = os.getenv("AGENT_CLIENT_ID")
AGENT_CLIENT_SECRET = os.getenv("AGENT_CLIENT_SECRET")

# ------------------------------------------------------------
# Blockchain (kept as provided)
# ------------------------------------------------------------
BLOCKCHAIN_CONTRACT_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_sampleId", "type": "string"},
            {"name": "_previousState", "type": "string"},
            {"name": "_newState", "type": "string"},
        ],
        "name": "addTransition",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

BLOCKCHAIN_CONTRACT_ADDRESS = "0x36610135c9aD0650CaAdb3A99151bdDC4E50e4c8"
WEB3_PROVIDER = "http://127.0.0.1:8545"

# Local dev: allow your front-end origins
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",   # if you keep serving from Django static
    "http://localhost:8000",
    "http://127.0.0.1:8080",   # e.g. if you’re opening the file via another server/port
    "http://localhost:8080",
]

# Preflight needs to see these; default is fine, but this makes it explicit:
CORS_ALLOW_HEADERS = [
    "authorization", "content-type", "accept", "origin", "user-agent", "x-requested-with"
]
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

CORS_ALLOW_ALL_ORIGINS = True
