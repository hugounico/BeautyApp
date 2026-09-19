from .base import *

DEBUG = True

# SECRET_KEY con default no-secreto para desarrollo local
SECRET_KEY = config('SECRET_KEY', default='dev-insecure-key-not-for-production')

# Base de datos — SQLite local
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
