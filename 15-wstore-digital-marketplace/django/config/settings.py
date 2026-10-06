import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

# Load environment variables from .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Ensure apps directory is in sys.path
sys.path.insert(0, str(BASE_DIR / "apps"))

def _env_flag(name, default):
    return os.getenv(name, default).strip().lower() in ("true", "1", "yes")


SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-wstore-uz-super-secret-key-production-change-this")
DEBUG = _env_flag("DEBUG", "True")

# "*" ni standart qiymatdan olib tashladik — u Host header'ni qalbakilashtirishga
# yo'l ochadi. Prod'da domenlar .env dagi ALLOWED_HOSTS orqali beriladi.
ALLOWED_HOSTS = [h.strip() for h in os.getenv(
    "ALLOWED_HOSTS", "localhost,127.0.0.1,wstore.uz,www.wstore.uz"
).split(",") if h.strip()]

# DEMO_MODE — tezkor kirish (demo-login) va "simulyatsiya qilingan to'lov"ni
# yoqadi. Bular mahsulotni BEPUL berib yuboradi va admin hisobiga kirishga
# ruxsat beradi, shuning uchun standart holatda faqat DEBUG'da yoniq.
DEMO_MODE = _env_flag("DEMO_MODE", str(DEBUG))

if not DEBUG and SECRET_KEY.startswith("django-insecure-"):
    raise ImproperlyConfigured(
        "Prod rejimida (DEBUG=False) standart SECRET_KEY bilan ishga tushirib bo'lmaydi. "
        ".env faylida SECRET_KEY ni o'rnating."
    )

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Local apps
    "core.apps.CoreConfig",
    "store.apps.StoreConfig",
    "orders.apps.OrdersConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Tilni aniqlaydi (cookie -> sessiya -> brauzer sarlavhasi).
    # SessionMiddleware'dan KEYIN, CommonMiddleware'dan OLDIN turishi shart.
    "django.middleware.locale.LocaleMiddleware",
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
                # {{ LANGUAGE_CODE }} va {% get_available_languages %} uchun
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "core.context_processors.global_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database configuration
# Falls back to SQLite if DATABASE_URL is not provided or empty
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Custom User Model
AUTH_USER_MODEL = "core.User"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

# Saytdagi tillar. Navbar'dagi almashtirgich shu ro'yxatdan yasaladi —
# yangi til qo'shish uchun shu yerga qo'shib, locale/<kod>/ ga tarjima
# faylini qo'yish kifoya.
LANGUAGES = [
    ("uz", "O'zbekcha"),
    ("ru", "Русский"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

# Tanlangan til shu cookie'da saqlanadi (bir yil).
LANGUAGE_COOKIE_NAME = "wstore_lang"
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365
LANGUAGE_COOKIE_SAMESITE = "Lax"

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (Product uploads, covers, archives)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Kesh-buster: wstore.css/wstore.js o'zgarganda havoladagi ?v= ham o'zgaradi.
# Bunsiz brauzer (va nginx'dagi uzoq muddatli kesh) eski faylni ushlab qolardi —
# ya'ni deploy qilingan tuzatish foydalanuvchiga yetib bormasdi.
#
# DEBUG rejimida har so'rovda qayta hisoblanadi (context processor orqali):
# dev server .css/.js o'zgarganda qayta yuklanmaydi, shuning uchun bir marta
# hisoblangan versiya eskirib qolar va brauzer eski faylni ko'rsatardi.
def _static_version():
    stamp = 0
    for rel in ("css/wstore.css", "js/wstore.js"):
        path = BASE_DIR / "static" / rel
        try:
            stamp = max(stamp, int(path.stat().st_mtime))
        except OSError:
            continue
    return str(stamp or "1")


STATIC_VERSION = _static_version()
# context processor DEBUG'da shu funksiyani qayta chaqiradi
STATIC_VERSION_FN = _static_version

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth redirection
LOGIN_URL = "core:login"
LOGIN_REDIRECT_URL = "store:catalog"
LOGOUT_REDIRECT_URL = "store:catalog"

# HTTPS qattiqlashtirish — faqat prod'da (DEBUG=False) yonadi, shuning uchun
# lokal http://127.0.0.1 da ishlashga xalaqit bermaydi. To'lov va sessiya
# cookie'lari shifrlanmagan ulanishda yuborilmasligi uchun kerak.
if not DEBUG:
    SECURE_SSL_REDIRECT = _env_flag("SECURE_SSL_REDIRECT", "True")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # nginx orqasida turganda Django so'rov HTTPS ekanini shu sarlavhadan biladi
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    CSRF_TRUSTED_ORIGINS = [
        f"https://{h}" for h in ALLOWED_HOSTS if h and not h.startswith(".")
    ]

# Platform and Payment Business Settings
APP_URL = os.getenv("APP_URL", "http://localhost:8000")
PRODUCT_UZS_RATE = int(os.getenv("UZS_RATE", "12600"))
LISTING_FEE_SOM = int(os.getenv("LISTING_FEE_SOM", "5000"))
MIN_WITHDRAWAL_SOM = int(os.getenv("MIN_WITHDRAWAL_SOM", "50000"))
REFERRAL_BONUS_SOM = int(os.getenv("REFERRAL_BONUS_SOM", "10000"))
PLATFORM_COMMISSION_PERCENT = int(os.getenv("PLATFORM_COMMISSION_PERCENT", "0"))

# Click Payment Settings
CLICK_SERVICE_ID = os.getenv("CLICK_SERVICE_ID", "99657")
CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID", "59136")
CLICK_MERCHANT_USER_ID = os.getenv("CLICK_MERCHANT_USER_ID", "81435")
CLICK_BRIDGE_SECRET = os.getenv("CLICK_BRIDGE_SECRET", "wstore_secret_bridge_key")
CLICK_BASE_URL = "https://my.click.uz/services/pay"

# ---- Google OAuth ("Google bilan kirish") ----
# https://console.cloud.google.com/ -> APIs & Services -> Credentials ->
# OAuth client ID (Web application). Authorized redirect URI sifatida
# GOOGLE_OAUTH_REDIRECT_URI bilan bir xil manzil kiritilishi shart.
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()

# Bo'sh qoldirilsa so'rov manzilidan avtomatik yasaladi. nginx orqasida
# turganda yoki domen/sxema boshqacha bo'lsa — shu yerda aniq ko'rsating.
GOOGLE_OAUTH_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "").strip()

# Kalitlar berilmagan bo'lsa tugma umuman ko'rsatilmaydi — aks holda
# foydalanuvchi bosib, Google'ning "invalid_client" xatosiga tushardi.
GOOGLE_AUTH_ENABLED = bool(GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET)

# Saytga egalik qiluvchi Google hisoblari. Shu emaillar bilan kirgan
# foydalanuvchi avtomatik admin (staff + superuser) bo'ladi.
#
# Bu zarur: saytga faqat Google orqali kirilgani uchun, bu ro'yxatsiz
# egasi o'z Google hisobi bilan kirganda oddiy xaridor bo'lib qolardi va
# admin huquqini berishning saytdan boshqa yo'li qolmasdi.
# Faqat Google tomonidan TASDIQLANGAN email hisobga olinadi.
ADMIN_EMAILS = [
    e.strip().lower()
    for e in os.getenv("ADMIN_EMAILS", "").split(",")
    if e.strip()
]

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
