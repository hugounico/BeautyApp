from pathlib import Path
from decouple import config

# Rutas base
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps del proyecto
    'apps.beauty_app',
    'apps.usuarios',
    'apps.categorias',
    'apps.proveedores',
    'apps.servicios',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'beautyfull.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'beautyfull.wsgi.application'

# Internacionalización
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Primary key por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model (Decision 2 - data-model-core)
AUTH_USER_MODEL = 'usuarios.Usuario'

# Destinos de autenticación (Destino_Por_Defecto). Compartido por dev y prod.
LOGIN_URL = 'login'            # a dónde enviar a un usuario no autenticado
LOGIN_REDIRECT_URL = 'home'    # Destino_Por_Defecto tras login exitoso (R2.8)
LOGOUT_REDIRECT_URL = 'home'   # Destino_Por_Defecto tras logout (R2.9)

# Validadores de contraseña estándar de Django (R3.3). Sin opciones ni
# parámetros personalizados: se usan los validadores por defecto.
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Archivos estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
