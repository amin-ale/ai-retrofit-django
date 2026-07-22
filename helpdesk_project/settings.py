import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_flag(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-key-not-for-production")

DEBUG = _env_flag("DJANGO_DEBUG", True)

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "helpdesk",
    "copilot",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

ROOT_URLCONF = "helpdesk_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
            ],
        },
    },
]

WSGI_APPLICATION = "helpdesk_project.wsgi.application"
ASGI_APPLICATION = "helpdesk_project.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_DB_PATH", str(BASE_DIR / "db.sqlite3")),
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

COPILOT = {
    "ENABLED": _env_flag("COPILOT_ENABLED", True),
    "LLM_BACKEND": os.environ.get("COPILOT_LLM_BACKEND", "fake"),
    "EMBEDDING_BACKEND": os.environ.get("COPILOT_EMBEDDING_BACKEND", "hashing"),
    "EMBEDDING_DIM": int(os.environ.get("COPILOT_EMBEDDING_DIM", "256")),
    "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
    "ANTHROPIC_BASE_URL": os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
    "ANTHROPIC_VERSION": os.environ.get("ANTHROPIC_VERSION", "2023-06-01"),
    "MODEL": os.environ.get("COPILOT_MODEL", "claude-haiku-4-5"),
    "MAX_TOKENS": int(os.environ.get("COPILOT_MAX_TOKENS", "512")),
    "REQUEST_TIMEOUT": float(os.environ.get("COPILOT_REQUEST_TIMEOUT", "30")),
    "VOYAGE_API_KEY": os.environ.get("VOYAGE_API_KEY", ""),
    "VOYAGE_BASE_URL": os.environ.get("VOYAGE_BASE_URL", "https://api.voyageai.com"),
    "VOYAGE_MODEL": os.environ.get("VOYAGE_MODEL", "voyage-3.5-lite"),
    "DAILY_TOKEN_BUDGET": int(os.environ.get("COPILOT_DAILY_TOKEN_BUDGET", "20000")),
    "MAX_ROWS": int(os.environ.get("COPILOT_MAX_ROWS", "100")),
    "PRICE_INPUT_PER_MTOK": float(os.environ.get("COPILOT_PRICE_INPUT", "1.00")),
    "PRICE_OUTPUT_PER_MTOK": float(os.environ.get("COPILOT_PRICE_OUTPUT", "5.00")),
    "SEARCH_TOP_K": int(os.environ.get("COPILOT_SEARCH_TOP_K", "5")),
}
