from pathlib import Path
from urllib.parse import urlparse

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "import_export",
    "django_celery_beat",
    "apps.core",
    "apps.accounts",
    "apps.hotels",
    "apps.bookings",
    "apps.payments",
    "apps.notifications",
    "bot",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


def _database_from_url(url: str) -> dict:
    parsed = urlparse(url)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed.path.lstrip("/"),
        "USER": parsed.username,
        "PASSWORD": parsed.password,
        "HOST": parsed.hostname,
        "PORT": parsed.port or 5432,
    }


DATABASES = {
    "default": _database_from_url(
        config("DATABASE_URL", default="postgres://hotelbot:hotelbot@localhost:5432/hotelbookingbot")
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uz"
TIME_ZONE = config("TIME_ZONE", default="Asia/Tashkent")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/admin/"

REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_BEAT_SCHEDULE = {
    "expire-pending-bookings": {
        "task": "apps.notifications.tasks.expire_pending_bookings_task",
        "schedule": 15 * 60,  # har 15 daqiqada
    },
    "send-checkin-reminders": {
        "task": "apps.notifications.tasks.send_checkin_reminders_task",
        "schedule": 24 * 60 * 60,  # kunlik
    },
}

# --- Bot ---
BOT_TOKEN = config("BOT_TOKEN", default="")
BOT_MODE = config("BOT_MODE", default="polling")  # "polling" | "webhook"
BOT_WEBHOOK_BASE_URL = config("BOT_WEBHOOK_BASE_URL", default="")
BOT_WEBHOOK_SECRET = config("BOT_WEBHOOK_SECRET", default="")
ADMIN_GROUP_CHAT_ID = config("ADMIN_GROUP_CHAT_ID", default="", cast=str)

BOOKING_PENDING_EXPIRY_HOURS = config("BOOKING_PENDING_EXPIRY_HOURS", default=2, cast=int)

# --- Click payment gateway ---
CLICK_MERCHANT_ID = config("CLICK_MERCHANT_ID", default="")
CLICK_SERVICE_ID = config("CLICK_SERVICE_ID", default="")
CLICK_SECRET_KEY = config("CLICK_SECRET_KEY", default="")
CLICK_MERCHANT_USER_ID = config("CLICK_MERCHANT_USER_ID", default="")
CLICK_PAY_BASE_URL = config("CLICK_PAY_BASE_URL", default="https://my.click.uz/services/pay")
CLICK_RETURN_URL = config("CLICK_RETURN_URL", default="")

SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.2, send_default_pii=False)

JAZZMIN_SETTINGS = {
    "site_title": "HotelBookingBot Admin",
    "site_header": "HotelBookingBot",
    "site_brand": "HotelBookingBot",
    "site_logo": "img/logo.png",
    "site_logo_classes": "img-circle",
    "site_icon": "img/favicon.png",
    "login_logo": "img/logo.png",
    "welcome_sign": "HotelBookingBot boshqaruv paneliga xush kelibsiz",
    "search_model": ["bookings.Booking", "accounts.TelegramUser"],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "accounts.TelegramUser": "fas fa-id-card",
        "hotels.Hotel": "fas fa-hotel",
        "hotels.RoomType": "fas fa-bed",
        "hotels.Room": "fas fa-door-open",
        "bookings.Booking": "fas fa-calendar-check",
        "payments.PaymentStatus": "fas fa-money-bill",
    },
}

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAdminUser"],
}
