"""
Django settings for microservicios project.
"""

from pathlib import Path
import os

# =========================================
# BASE
# =========================================
BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================
# SEGURIDAD (RENDER)
# =========================================
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-local-only"
)

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1"
).split(",")


# =========================================
# APPS
# =========================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'Aplicaciones',
]


# =========================================
# MIDDLEWARE
# =========================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'microservicios.urls'


# =========================================
# TEMPLATES
# =========================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'Aplicaciones' / 'template'
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


WSGI_APPLICATION = 'microservicios.wsgi.application'


# =========================================
# BASE DE DATOS (RENDER / LOCAL)
# =========================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("DB_NAME", "microservi"),
        'USER': os.getenv("DB_USER", "postgres"),
        'PASSWORD': os.getenv("DB_PASSWORD", ""),
        'HOST': os.getenv("DB_HOST", "localhost"),
        'PORT': os.getenv("DB_PORT", "5432"),
    }
}


# =========================================
# USUARIO PERSONALIZADO
# =========================================
AUTH_USER_MODEL = 'Aplicaciones.Usuario'


# =========================================
# VALIDADORES
# =========================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# =========================================
# IDIOMA / ZONA HORARIA
# =========================================
LANGUAGE_CODE = 'es-ec'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True


# =========================================
# ARCHIVOS ESTÁTICOS
# =========================================
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'microservicios' / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'


# =========================================
# MEDIA
# =========================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# =========================================
# DEFAULT
# =========================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
