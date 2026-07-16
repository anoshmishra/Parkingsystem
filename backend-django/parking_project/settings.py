import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def csv_env(name, default=""):
    return [
        value.strip()
        for value in os.getenv(name, default).split(",")
        if value.strip()
    ]


def bool_env(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


IS_HOSTED = bool(os.getenv("RENDER") or os.getenv("DJANGO_ENV") == "production")
DEBUG = bool_env("DEBUG", default=not IS_HOSTED)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-secret-key"
    else:
        raise RuntimeError("SECRET_KEY must be set when DEBUG is disabled.")

DEFAULT_ALLOWED_HOSTS = "localhost,127.0.0.1" if DEBUG else os.getenv("RENDER_EXTERNAL_HOSTNAME", "")
ALLOWED_HOSTS = csv_env("ALLOWED_HOSTS", DEFAULT_ALLOWED_HOSTS)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "parking",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "parking.middleware.GlobalExceptionMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "parking_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "parking_project.wsgi.application"
ASGI_APPLICATION = "parking_project.asgi.application"

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    if DEBUG:
        DATABASE_URL = "postgres://parking_user:parking_pass@127.0.0.1:5432/parking_db"
    else:
        raise RuntimeError("DATABASE_URL must be set when DEBUG is disabled.")

DATABASES = {
    "default": dj_database_url.config(default=DATABASE_URL)
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = csv_env(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000" if DEBUG else "",
)
CORS_ALLOWED_ORIGIN_REGEXES = csv_env("CORS_ALLOWED_ORIGIN_REGEXES")

# Booking receipt email via SendGrid's SMTP relay. Keep the API key in Render only.
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_PORT = 587
EMAIL_HOST_USER = "apikey"
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
EMAIL_USE_SSL = False
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Parking Reservations <no-reply@example.com>")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
PARKING_DEVELOPER_EMAIL = os.getenv("PARKING_DEVELOPER_EMAIL", "anoshmishra09@gmail.com")
PARKING_RECEIPT_TIME_ZONE = os.getenv("PARKING_RECEIPT_TIME_ZONE", "Asia/Kolkata")
