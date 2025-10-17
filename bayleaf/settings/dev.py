# bayleaf/settings/dev.py

"""
Django settings — Development.
Uses PostgreSQL from docker-compose (service: db) and runserver.
Designed to run without collectstatic via simpler storage.
"""

from pathlib import Path
import os
import json
from datetime import timedelta


# ------------------------------------------------------------
# Helpers (same helper as your current file)
# ------------------------------------------------------------
def env(name: str, default=None, required: bool = False):
    val = os.getenv(name, default)
    if required and (val is None or val == ""):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


# ------------------------------------------------------------
# Paths / core Django bits
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent


SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-l4z&5z%2v0$53dv**=h@2k-*wr$_(spmsmpd+13k_fbrteb(ju",
)

DEBUG = True
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
    "django_filters",
    "corsheaders",
    "drf_yasg",
    # your apps
    "users",
    "patients",
    "core",
    "appointments",
    "events",
    "lab",
    "professionals",
    "prescriptions",
    "medications",
    "careplans",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # fine in dev too
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
            "libraries": {"staticfiles": "django.templatetags.static"},
        },
    },
]

WSGI_APPLICATION = "bayleaf.wsgi.application"

# ------------------------------------------------------------
# Database (defaults for docker-compose; overridable via env)
# ------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "bayleaf"),
        "USER": os.getenv("DB_USER", "bayleaf"),
        "PASSWORD": os.getenv("DB_PASSWORD", "bayleaf"),
        "HOST": os.getenv("DB_HOST", "db"),
        "PORT": os.getenv("DB_PORT", "5432"),
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
# In dev, avoid the Manifest storage (no need to run collectstatic):
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

# ------------------------------------------------------------
# CORS / CSRF (dev-friendly)
# ------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
]
CORS_ALLOW_HEADERS = [
    "authorization", "content-type", "accept", "origin", "user-agent", "x-requested-with"
]
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

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
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
}
REST_FRAMEWORK.setdefault("DEFAULT_THROTTLE_RATES", {})
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].update(
    {
        "token_exchange": os.getenv("THROTTLE_TOKEN_EXCHANGE", "50/min"),
        "client_credentials": os.getenv("THROTTLE_CLIENT_CREDENTIALS", "50/min"),
    }
)

# ------------------------------------------------------------
# JWT / OBO config (same behavior as your current file)
# ------------------------------------------------------------
BAYLEAF_ISSUER = env("BAYLEAF_ISSUER", "http://localhost:8000")
BAYLEAF_AUDIENCE_AGENT = env("BAYLEAF_AUDIENCE_AGENT", "agent")
BAYLEAF_AUDIENCE_API = env("BAYLEAF_AUDIENCE_API", "bayleaf-api")
BAYLEAF_ACTIVE_KID = env("BAYLEAF_ACTIVE_KID", "key-dev")
BAYLEAF_OLD_PUBKEYS_JSON = env("BAYLEAF_OLD_PUBKEYS_JSON", "[]")
BAYLEAF_OLD_PUBKEYS = json.loads(BAYLEAF_OLD_PUBKEYS_JSON)

ACCESS_MIN = int(env("BAYLEAF_ACCESS_LIFETIME_MIN", "60"))
REFRESH_MIN = int(env("BAYLEAF_REFRESH_LIFETIME_MIN", str(60 * 24 * 14)))  # 14 days
OBO_MIN = int(env("BAYLEAF_OBO_LIFETIME_MIN", "10"))

RSA_PRIVATE = os.getenv("BAYLEAF_RSA_PRIVATE_KEY")
RSA_PUBLIC = os.getenv("BAYLEAF_RSA_PUBLIC_KEY")

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

if RSA_PRIVATE and RSA_PUBLIC:
    SIMPLE_JWT.update(
        {
            "ALGORITHM": "RS256",
            "SIGNING_KEY": RSA_PRIVATE,
            "VERIFYING_KEY": RSA_PUBLIC,
            "ACCESS_TOKEN_LIFETIME": timedelta(minutes=ACCESS_MIN),
            "REFRESH_TOKEN_LIFETIME": timedelta(minutes=REFRESH_MIN),
        }
    )
else:
    SIMPLE_JWT.update(
        {
            "ALGORITHM": "HS256",
            "SIGNING_KEY": env("DJANGO_SECRET_KEY", SECRET_KEY),
            "ACCESS_TOKEN_LIFETIME": timedelta(minutes=ACCESS_MIN),
            "REFRESH_TOKEN_LIFETIME": timedelta(minutes=REFRESH_MIN),
        }
    )

BAYLEAF_OBO_LIFETIME_SECONDS = OBO_MIN * 60

AGENT_CLIENT_ID = os.getenv("AGENT_CLIENT_ID")
AGENT_CLIENT_SECRET = os.getenv("AGENT_CLIENT_SECRET")

# ------------------------------------------------------------
# Email (console in dev)
# ------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ------------------------------------------------------------
# Logging (verbose in dev)
# ------------------------------------------------------------
LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "DEBUG")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(asctime)s %(levelname)s [%(name)s] %(message)s"},
        "simple": {"format": "%(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "django.server": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "django.db.backends": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "bayleaf": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "careplans": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}

# Handy for dev tooling (e.g., django-debug-toolbar if you add it later)
INTERNAL_IPS = ["127.0.0.1", "localhost"]
