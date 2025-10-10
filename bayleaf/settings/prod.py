# bayleaf/settings/prod.py
"""
Django settings — Production.
uWSGI behind a reverse proxy (e.g., Nginx). PostgreSQL from docker-compose.
"""

from pathlib import Path
import os
import json


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def env(name: str, default=None, required: bool = False):
    val = os.getenv(name, default)
    if required and (val is None or val == ""):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


def list_from_env(name: str, default: str = ""):
    raw = os.getenv(name, default)
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


# ------------------------------------------------------------
# Paths / core
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = env("DJANGO_SECRET_KEY", required=True)
DEBUG = False
ALLOWED_HOSTS = list_from_env("ALLOWED_HOSTS", "*")  # set to your domains in env

# If you’re behind a proxy/ELB/Ingress forwarding X-Forwarded-Proto:
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves collected static safely
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
# Database
# ------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", "bayleaf"),
        "USER": env("DB_USER", "bayleaf"),
        "PASSWORD": env("DB_PASSWORD", "bayleaf"),
        "HOST": env("DB_HOST", "db"),
        "PORT": env("DB_PORT", "5432"),
        "CONN_MAX_AGE": int(env("DB_CONN_MAX_AGE", "60")),  # persistent conns
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
# Static / Media (prod)
# ------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Manifest storage ensures cache-busting; requires collectstatic:
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

# ------------------------------------------------------------
# Security headers / cookies
# ------------------------------------------------------------
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", "1") == "1"
SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", "31536000"))  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = env("SECURE_HSTS_INCLUDE_SUBDOMAINS", "1") == "1"
SECURE_HSTS_PRELOAD = env("SECURE_HSTS_PRELOAD", "1") == "1"
SECURE_REFERRER_POLICY = env("SECURE_REFERRER_POLICY", "same-origin")
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# ------------------------------------------------------------
# CORS / CSRF
# ------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = env("CORS_ALLOW_ALL_ORIGINS", "0") == "1"
CORS_ALLOWED_ORIGINS = list_from_env("CORS_ALLOWED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = list_from_env("CSRF_TRUSTED_ORIGINS", "")

# ------------------------------------------------------------
# DRF
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
    "PAGE_SIZE": int(env("DRF_PAGE_SIZE", "10")),
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
}
REST_FRAMEWORK.setdefault("DEFAULT_THROTTLE_RATES", {})
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].update(
    {
        "token_exchange": env("THROTTLE_TOKEN_EXCHANGE", "10/min"),
        "client_credentials": env("THROTTLE_CLIENT_CREDENTIALS", "10/min"),
    }
)

# ------------------------------------------------------------
# JWT / OBO
# ------------------------------------------------------------
BAYLEAF_ISSUER = env("BAYLEAF_ISSUER", "https://auth.bayleaf.local")
BAYLEAF_AUDIENCE_AGENT = env("BAYLEAF_AUDIENCE_AGENT", "agent")
BAYLEAF_AUDIENCE_API = env("BAYLEAF_AUDIENCE_API", "bayleaf-api")
BAYLEAF_ACTIVE_KID = env("BAYLEAF_ACTIVE_KID", "key-1")
BAYLEAF_OLD_PUBKEYS_JSON = env("BAYLEAF_OLD_PUBKEYS_JSON", "[]")
BAYLEAF_OLD_PUBKEYS = json.loads(BAYLEAF_OLD_PUBKEYS_JSON)

ACCESS_MIN = int(env("BAYLEAF_ACCESS_LIFETIME_MIN", "30"))
REFRESH_MIN = int(env("BAYLEAF_REFRESH_LIFETIME_MIN", str(60 * 24 * 7)))  # 7 days
OBO_MIN = int(env("BAYLEAF_OBO_LIFETIME_MIN", "5"))

RSA_PRIVATE = env("BAYLEAF_RSA_PRIVATE_KEY", required=True)  # require RS256 in prod
RSA_PUBLIC = env("BAYLEAF_RSA_PUBLIC_KEY", required=True)

from datetime import timedelta as _td  # local alias to keep scope clean
SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": os.getenv("JWT_SECRET", SECRET_KEY),
    "VERIFYING_KEY": RSA_PUBLIC,
    "ACCESS_TOKEN_LIFETIME": _td(minutes=ACCESS_MIN),
    "REFRESH_TOKEN_LIFETIME": _td(minutes=REFRESH_MIN),
}
BAYLEAF_OBO_LIFETIME_SECONDS = OBO_MIN * 60

AGENT_CLIENT_ID = os.getenv("AGENT_CLIENT_ID")
AGENT_CLIENT_SECRET = os.getenv("AGENT_CLIENT_SECRET")

# ------------------------------------------------------------
# Email (SMTP in prod; configure via env)
# ------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", "smtp")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env("EMAIL_USE_TLS", "1") == "1"
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "no-reply@bayleaf.local")

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
LOG_LEVEL = env("DJANGO_LOG_LEVEL", "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(asctime)s %(levelname)s [%(name)s] %(message)s"},
        "simple": {"format": "%(levelname)s %(name)s: %(message)s"},
        "json": {
            "()": "django.utils.log.ServerFormatter",
            "format": '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}',
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "django.server": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "django.db.backends": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "bayleaf": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "careplans": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}
