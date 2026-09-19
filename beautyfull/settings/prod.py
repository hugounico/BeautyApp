from .base import *

DEBUG = False

# SECRET_KEY desde variable de entorno (sin default — falla si no está definida)
SECRET_KEY = config('SECRET_KEY')

# ALLOWED_HOSTS desde variable de entorno (falla si no está definida)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

# Base de datos — PostgreSQL con credenciales desde variables de entorno (sin default)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
    }
}
