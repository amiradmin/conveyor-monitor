import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = ["*"] if DEBUG else [h for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "apps.monitoring",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

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
            ]
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "conveyor_monitor"),
        "USER": os.getenv("POSTGRES_USER", "conveyor"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "conveyor"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

LANGUAGE_CODE = "en-us"
LANGUAGES = [("en", "English"), ("fa", "Persian"), ("ar", "Arabic")]
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS = [origin for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if origin]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

VISION_SERVICE_URL = os.getenv("VISION_SERVICE_URL", "http://vision-service:8010")
PLC_GATEWAY_URL = os.getenv("PLC_GATEWAY_URL", "http://plc-gateway:8020")
PLC_WRITE_ENABLED = os.getenv("PLC_WRITE_ENABLED", "false").lower() == "true"
INTERNAL_SERVICE_TOKEN = os.getenv("INTERNAL_SERVICE_TOKEN", "dev-internal-token")
EVIDENCE_CAPTURE_ENABLED = os.getenv("EVIDENCE_CAPTURE_ENABLED", "true").lower() == "true"
EVIDENCE_CAPTURE_TIMEOUT_SECONDS = float(os.getenv("EVIDENCE_CAPTURE_TIMEOUT_SECONDS", "4"))
EVIDENCE_URL_TTL_SECONDS = int(os.getenv("EVIDENCE_URL_TTL_SECONDS", "900"))

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_ENDPOINT", "localhost:9000")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "conveyor-events")
MINIO_REGION = os.getenv("MINIO_REGION", "us-east-1")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_PUBLIC_SECURE = os.getenv("MINIO_PUBLIC_SECURE", "false").lower() == "true"

# Conveyor process/calibration defaults. These can be overridden per site through .env.
BULK_DENSITY_T_PER_M3 = float(os.getenv("BULK_DENSITY_T_PER_M3", "1.32"))
NOMINAL_CAPACITY_TPH = float(os.getenv("NOMINAL_CAPACITY_TPH", "600"))
TELEMETRY_STALE_SECONDS = int(os.getenv("TELEMETRY_STALE_SECONDS", "6"))
ALARM_COOLDOWN_SECONDS = int(os.getenv("ALARM_COOLDOWN_SECONDS", "60"))

# Alarm trigger thresholds plus lower recovery thresholds provide hysteresis.
# ACK only means the operator has seen the alarm; the condition stays latched
# until the measured value crosses its recovery threshold.
ALIGNMENT_WARNING_MM = float(os.getenv("ALIGNMENT_WARNING_MM", "25"))
ALIGNMENT_CRITICAL_MM = float(os.getenv("ALIGNMENT_CRITICAL_MM", "40"))
ALIGNMENT_RECOVERY_MM = float(os.getenv("ALIGNMENT_RECOVERY_MM", "20"))
TEAR_WARNING_PROBABILITY = float(os.getenv("TEAR_WARNING_PROBABILITY", "0.35"))
TEAR_CRITICAL_PROBABILITY = float(os.getenv("TEAR_CRITICAL_PROBABILITY", "0.65"))
TEAR_RECOVERY_PROBABILITY = float(os.getenv("TEAR_RECOVERY_PROBABILITY", "0.25"))
OVERLOAD_WARNING_PERCENT = float(os.getenv("OVERLOAD_WARNING_PERCENT", "80"))
OVERLOAD_CRITICAL_PERCENT = float(os.getenv("OVERLOAD_CRITICAL_PERCENT", "100"))
OVERLOAD_RECOVERY_PERCENT = float(os.getenv("OVERLOAD_RECOVERY_PERCENT", "75"))
