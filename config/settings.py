from pathlib import Path
import os

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-change-this-key"
)

DEBUG = False

ALLOWED_HOSTS = [
    'task-managment-system-ryjg.onrender.com',
    '127.0.0.1',
    'localhost',
]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Your Apps
    'accounts',
    'task',
    'wallet',
    'verification',
    'api',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # WhiteNoise
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'config.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # templates folder
        'DIRS': [BASE_DIR / 'templates'],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'config.wsgi.application'


# DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
]


# LANGUAGE
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Colombo'

USE_I18N = True

USE_TZ = True


# STATIC FILES
STATIC_URL = 'static/'

_static_dir = BASE_DIR / 'static'
STATICFILES_DIRS = [_static_dir] if _static_dir.is_dir() else []

STATIC_ROOT = BASE_DIR / 'staticfiles'


# MEDIA FILES
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# DEFAULT PRIMARY KEY
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# CUSTOM USER MODEL
AUTH_USER_MODEL = 'accounts.User'


# LOGIN URLS
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'


# WHITENOISE STATIC FILES
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# SECURITY SETTINGS
CSRF_TRUSTED_ORIGINS = [
    'https://task-managment-system-ryjg.onrender.com',
]


SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# OPTIONAL SECURITY
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# CELERY CONFIGURATION
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE