# Arquitectura

## Estructura del Proyecto

```
BautyApp/                          ← raíz del repositorio
├── manage.py                      ← CLI Django, default: beautyfull.settings.dev
├── beautyfull/                    ← paquete raíz del proyecto (settings, urls, wsgi, asgi)
│   ├── __init__.py
│   ├── urls.py                    ← URLconf raíz
│   ├── wsgi.py
│   ├── asgi.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py                ← configuración compartida
│       ├── dev.py                 ← DEBUG=True, SQLite
│       └── prod.py               ← DEBUG=False, PostgreSQL, secretos obligatorios
├── apps/                          ← paquete contenedor de todas las apps Django
│   ├── __init__.py
│   └── beauty_app/                ← app núcleo compartida (templates base, utilidades)
│       ├── __init__.py
│       ├── apps.py
│       ├── models.py
│       ├── views.py
│       ├── urls.py
│       ├── templates/
│       │   └── base.html
│       └── tests.py
├── static/
│   ├── css/
│   └── js/
├── .env.example
├── requirements.txt
└── roadmap.md
```

## Reglas Arquitectónicas

1. **Paquete `/apps/`**: contiene `__init__.py` — es un paquete Python. No se manipula `sys.path`.
2. **AppConfig.name**: cada app usa `name = 'apps.<nombre_app>'` (ruta de importación real).
3. **AppConfig.label**: cada app define `label = '<nombre_app>'` para mantener migraciones y tablas con el nombre corto.
4. **INSTALLED_APPS**: las apps se registran como `'apps.<nombre_app>'`.
5. **Settings split**: `base.py` compartido, `dev.py` y `prod.py` heredan con `from .base import *`.
6. **Secretos**: exclusivamente via variables de entorno (python-decouple). Sin hardcoding.
7. **Templates**: herencia desde `base.html` de beauty_app. Sin styles inline ni JS embebido.
8. **Static files**: CSS en `/static/css/`, JS en `/static/js/`.

## Dependencias Base

- Django >=5.1,<5.2
- python-decouple >=3.8,<4.0

## Convención para Nuevas Apps

Toda funcionalidad de negocio nueva se crea en `/apps/<nombre_snake_case>/` siguiendo:
- `apps.py` con `name='apps.<nombre>'`, `label='<nombre>'`
- Archivos mínimos: `__init__.py`, `apps.py`, `models.py`, `views.py`, `urls.py`
- Registro en `INSTALLED_APPS` como `'apps.<nombre>'`

---

> **Gobernanza:** Si en cualquier spec futuro una instrucción contradice este steering file, Kiro debe detenerse y pedir clarificación explícita antes de continuar — nunca resolver la contradicción por su cuenta ni ignorar silenciosamente ninguna fuente.
