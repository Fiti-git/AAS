"""
Django settings for aas project.
"""

from pathlib import Path
import os
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-0o(b@duchc*na=6x3022%zag8y(*m5#s#z%gq)1ng6@-p74dih'
DEBUG = True

ALLOWED_HOSTS = ['128.199.24.138', 'localhost', '127.0.0.1', 'arunalusupermarket.shop']

# ✅ Add CORS settings
INSTALLED_APPS = [
    'corsheaders',  # ✅ Add this first
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'main',
    'attendance',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # ✅ Must be at the top
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'aas.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'aas.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DATABASE_NAME', 'AASDB'),
        'USER': os.environ.get('DATABASE_USER', 'postgres'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DATABASE_HOST', 'db'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'AASDB',
#         'USER': 'postgres',
#         'PASSWORD': 'postgres',
#         'HOST': 'localhost',  
#         'PORT': '5432',
#     }
# }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/employee_form'
LOGOUT_REDIRECT_URL = '/login/'
LOGIN_URL = '/login/'

# ✅ Django REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'TOKEN_OBTAIN_SERIALIZER': 'users.serializers.CustomTokenObtainPairSerializer',
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# ✅ CORS SETTINGS (development-safe)
CORS_ALLOW_ALL_ORIGINS = True  # ❗ Enable only in development. Restrict for production.

CORS_ALLOWED_ORIGINS = [
    "http://arunalusupermarket.shop",
    "https://arunalusupermarket.shop",
    "http://localhost:3000",
]
