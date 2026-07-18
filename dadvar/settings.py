import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# پایه
# =========================================================

SECRET_KEY = config('SECRET_KEY')

DEBUG = config(
    'DEBUG',
    default=True,
    cast=bool
)

ENVIRONMENT = config(
    'ENVIRONMENT',
    default='production'
)

# =========================================================
# هاست‌ها
# =========================================================

ALLOWED_HOSTS = [
    host.strip()
    for host in config(
        'ALLOWED_HOSTS',
        default='localhost,127.0.0.1'
    ).split(',')
]

# =========================================================
# CSRF
# =========================================================

CSRF_TRUSTED_ORIGINS = []

for host in ALLOWED_HOSTS:

    if (
        host and
        host != '*' and
        not host.startswith('127.') and
        host != 'localhost'
    ):

        CSRF_TRUSTED_ORIGINS.append(f'https://{host}')
        CSRF_TRUSTED_ORIGINS.append(f'http://{host}')

CSRF_TRUSTED_ORIGINS += [
    'http://localhost',
    'http://127.0.0.1',
]

# =========================================================
# Proxy
# =========================================================

USE_X_FORWARDED_HOST = config(
    'USE_X_FORWARDED_HOST',
    default=True,
    cast=bool
)

USE_X_FORWARDED_PORT = config(
    'USE_X_FORWARDED_PORT',
    default=True,
    cast=bool
)

SECURE_PROXY_SSL_HEADER = (
    'HTTP_X_FORWARDED_PROTO',
    'https'
)

# =========================================================
# اپ‌ها
# =========================================================

INSTALLED_APPS = [

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',

    'home.apps.HomeConfig',
    'accounts',
    'django_celery_beat',
    'ckeditor',
    'ckeditor_uploader',
]

# =========================================================
# Middleware
# =========================================================

MIDDLEWARE = [

    'django.middleware.security.SecurityMiddleware',

    'django.middleware.gzip.GZipMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dadvar.urls'

# =========================================================
# Templates
# =========================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates'
        ],

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

WSGI_APPLICATION = 'dadvar.wsgi.application'

# =========================================================
# Database
# =========================================================

if ENVIRONMENT == 'production':

    DATABASES = {
        'default': {

            'ENGINE': config(
                'DB_ENGINE',
                default='django.db.backends.postgresql'
            ),

            'NAME': config(
                'DB_NAME',
                default='dadvar_db'
            ),

            'USER': config(
                'DB_USER',
                default='dadvar_user'
            ),

            'PASSWORD': config(
                'DB_PASSWORD',
                default=''
            ),

            'HOST': config(
                'DB_HOST',
                default='postgres'
            ),

            'PORT': config(
                'DB_PORT',
                default='5432'
            ),
        }
    }

else:

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# =========================================================
# Password Validation
# =========================================================

AUTH_PASSWORD_VALIDATORS = [

    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },

    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator'
    },

    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator'
    },

    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator'
    },
]

# =========================================================
# زبان و زمان
# =========================================================

LANGUAGE_CODE = 'fa-ir'

TIME_ZONE = 'Asia/Tehran'

USE_I18N = True

USE_TZ = True

# =========================================================
# Static & Media
# =========================================================

STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = []

static_dir = BASE_DIR / 'static'

if static_dir.exists():
    STATICFILES_DIRS.append(static_dir)

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'

# =========================================================
# Auth
# =========================================================

AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = 'accounts:login'

LOGIN_REDIRECT_URL = 'home:index'

LOGOUT_REDIRECT_URL = 'home:index'

# =========================================================
# Site
# =========================================================

SITE_ID = 1

SITE_NAME = config(
    'SITE_NAME',
    default='دادور'
)

SITE_DOMAIN = config(
    'SITE_DOMAIN',
    default='vakiljuy.ir'
)

SITE_URL = config(
    'SITE_URL',
    default='https://vakiljuy.ir'
)

# =========================================================
# زرین پال
# =========================================================

ZARINPAL_MERCHANT_ID = config(
    'ZARINPAL_MERCHANT_ID',
    default=''
)

ZARINPAL_SANDBOX = config(
    'ZARINPAL_SANDBOX',
    default=True,
    cast=bool
)

# =========================================================
# CKEditor
# =========================================================

CKEDITOR_UPLOAD_PATH = "uploads/"

CKEDITOR_IMAGE_BACKEND = "pillow"

CKEDITOR_CONFIGS = {

    'default': {

        'toolbar': 'full',

        'height': 400,

        'width': '100%',

        'language': 'fa',

        'versionCheck': False,
    },
}

# =========================================================
# Cache
# =========================================================

try:

    CACHES = {
        "default": {

            "BACKEND":
            "django_redis.cache.RedisCache",

            "LOCATION":
            config("REDIS_URL"),

            "OPTIONS": {

                "CLIENT_CLASS":
                "django_redis.client.DefaultClient",
            }
        }
    }

except Exception:

    CACHES = {
        "default": {
            "BACKEND":
            "django.core.cache.backends.locmem.LocMemCache",
        }
    }

CACHE_MIDDLEWARE_SECONDS = 3600

CACHE_MIDDLEWARE_KEY_PREFIX = 'vakiljuy'

# =========================================================
# Email
# =========================================================

EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend'
)

EMAIL_HOST = config(
    'EMAIL_HOST',
    default=''
)

EMAIL_PORT = config(
    'EMAIL_PORT',
    default=587,
    cast=int
)

EMAIL_USE_TLS = config(
    'EMAIL_USE_TLS',
    default=True,
    cast=bool
)

EMAIL_HOST_USER = config(
    'EMAIL_HOST_USER',
    default=''
)

EMAIL_HOST_PASSWORD = config(
    'EMAIL_HOST_PASSWORD',
    default=''
)

DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='noreply@vakiljuy.ir'
)

# =========================================================
# Security
# =========================================================

if ENVIRONMENT == 'production':

    SECURE_SSL_REDIRECT = config(
        'SECURE_SSL_REDIRECT',
        default=False,
        cast=bool
    )

    SESSION_COOKIE_SECURE = config(
        'SESSION_COOKIE_SECURE',
        default=False,
        cast=bool
    )

    CSRF_COOKIE_SECURE = config(
        'CSRF_COOKIE_SECURE',
        default=False,
        cast=bool
    )

    SECURE_HSTS_SECONDS = config(
        'SECURE_HSTS_SECONDS',
        default=0,
        cast=int
    )

    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    SECURE_HSTS_PRELOAD = True

    SECURE_BROWSER_XSS_FILTER = True

    SECURE_CONTENT_TYPE_NOSNIFF = True

    X_FRAME_OPTIONS = 'SAMEORIGIN'

# =========================================================
# Logging
# =========================================================

LOG_LEVEL = config(
    'LOG_LEVEL',
    default='INFO'
)

LOGGING = {

    'version': 1,

    'disable_existing_loggers': False,

    'formatters': {

        'simple': {

            'format':
            '{levelname} {asctime} {message}',

            'style': '{',
        },
    },

    'handlers': {

        'console': {

            'class':
            'logging.StreamHandler',

            'formatter':
            'simple',
        },
    },

    'root': {

        'handlers':
        ['console'],

        'level':
        LOG_LEVEL,
    },
}

# =========================================================
# Default PK
# =========================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    "redis://redis:6379/0"
)

CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND",
    "redis://redis:6379/0"
)

CELERY_TIMEZONE = "Asia/Tehran"
CELERY_ENABLE_UTC = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True