"""
Django settings for microservicios project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================
# CONFIGURACIÓN GENERAL
# =========================================
SECRET_KEY = 'django-insecure-12bpkct$-0pk$#v*1$#p*x18ih8vmqd%^a@td9kxpegdla80pr'
DEBUG = True
ALLOWED_HOSTS = ['*']  # Para evitar errores durante desarrollo


# =========================================
# APPS INSTALADAS
# =========================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Tu app
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
            os.path.join(BASE_DIR, 'Aplicaciones', 'template')
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
AUTH_USER_MODEL = 'Aplicaciones.Usuario'   # ¡IMPORTANTE!


# =========================================
# VALIDADORES DE CONTRASEÑA
# =========================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# =========================================
# INTERNACIONALIZACIÓN
# =========================================
LANGUAGE_CODE = 'es-ec'  # Español Ecuador
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True


# =========================================
# ARCHIVOS ESTÁTICOS
# =========================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'microservicios', 'static'),  # ✅ Ahora Django lo reconoce correctamente
]

# Carpeta donde collectstatic copiará los archivos
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# =========================================
# ARCHIVOS SUBIDOS
# =========================================
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
