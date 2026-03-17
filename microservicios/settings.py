"""
Django settings for microservicios project.
"""

from pathlib import Path
import os
from datetime import timedelta

# =========================================
# BASE
# =========================================
BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================
# SEGURIDAD
# =========================================
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-local-only"
)

# ⚠️ PARA DESARROLLO (evita 500 silencioso)
DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".onrender.com",
    "sistemacomtablearicode.com",
    "www.sistemacomtablearicode.com",
]


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

    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',

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

    'corsheaders.middleware.CorsMiddleware',
]


ROOT_URLCONF = 'microservicios.urls'


# =========================================
# TEMPLATES (🔥 AQUÍ ESTABA EL PROBLEMA)
# =========================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'Aplicaciones' / 'template'
        ],
        'APP_DIRS': False,
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
# BASE DE DATOS
# =========================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'microservi',
        'USER': 'postgres',
        'PASSWORD': 'Ariel1997',
        'HOST': 'localhost',
        'PORT': '5432',
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
# ⚠️ es-ec NO existe en Django
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True


# =========================================
# ARCHIVOS ESTÁTICOS
# =========================================
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'


# =========================================
# MEDIA
# =========================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# =========================================
# REST FRAMEWORK / JWT
# =========================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOW_ALL_ORIGINS = True


CSRF_TRUSTED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "https://sistemacomtablearicode.com",
    "https://www.sistemacomtablearicode.com",
]
