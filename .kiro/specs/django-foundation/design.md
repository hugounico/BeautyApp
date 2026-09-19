# Design Document

## Overview

Este documento describe las decisiones técnicas para la Spec 01 (django-foundation) de BeautyFull: un proyecto Django mínimo, sin lógica de negocio, que establece la estructura de directorios, configuración por entorno, app núcleo compartida y verificación de arranque.

El objetivo es producir un scaffold que:

- Arranque sin errores con `python manage.py runserver` y `python manage.py check`.
- Aísle secretos en variables de entorno.
- Permita agregar apps de negocio futuras en `/apps/<nombre>/` sin modificar la base.
- Cumpla las convenciones de nombrado, frontend y gobernanza definidas en los steering files.

---

## Architecture

### Estructura de Directorios

```
BautyApp/                          ← raíz del repositorio (nombre confirmado)
├── manage.py
├── beautyfull/                    ← paquete raíz del proyecto Django
│   ├── __init__.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py
│       ├── dev.py
│       └── prod.py
├── apps/                          ← directorio contenedor de todas las apps
│   ├── __init__.py                ← hace de /apps/ un paquete Python
│   └── beauty_app/                ← app núcleo compartida
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
├── .env.example                   ← plantilla de variables de entorno
├── requirements.txt
└── roadmap.md
```

> **Nota sobre la carpeta raíz**: `BautyApp` queda confirmado como nombre definitivo de la carpeta raíz del repositorio. No confundir con el paquete Django (`beautyfull`) ni con la app núcleo (`beauty_app`).

> **Decisión sobre `templates/` en la raíz**: Se elimina de esta spec. No existe un caso de uso actual que justifique un directorio global de templates. Cuando una spec futura requiera overrides globales de templates (ej: páginas de error personalizadas 404/500), se creará `templates/` en la raíz y se configurará en `TEMPLATES[0]['DIRS']`. Registrado en `roadmap.md`.

### Decisión Clave: Cómo hacer `/apps/` importable

**Problema**: Django necesita importar las apps registradas en `INSTALLED_APPS`. Si las apps viven dentro de `/apps/`, hay que decidir cómo resolver la ruta de importación.

**Alternativas evaluadas:**

| Opción | Mecanismo | Pros | Contras |
|--------|-----------|------|---------|
| A: `sys.path.insert` | Añadir `/apps/` al path en settings | Apps se registran como `'beauty_app'` directamente | Manipula sys.path, confuso para IDEs, no refleja la estructura real del disco |
| B: Paquete Python | `/apps/__init__.py` hace de `/apps/` un paquete; `AppConfig.name = 'apps.beauty_app'` | Sin manipulación de sys.path, imports explícitos y trazables, `apps.beauty_app` en INSTALLED_APPS coincide con el sistema de ficheros | Las migraciones se etiquetan `apps_beauty_app`, app_label debe configurarse explícitamente |
| C: `app_label` explícito | Opción B + `class Meta: app_label = 'beauty_app'` en cada modelo | Migraciones limpias con label corto | Más boilerplate en cada modelo |

**Decisión: Opción B (paquete Python)** — con `label` en AppConfig.

**Justificación:**
- El requisito 3.4 pide explícitamente registrar apps con la ruta `apps.<nombre_app>` en `INSTALLED_APPS`.
- Usar `/apps/__init__.py` convierte el directorio en paquete importable sin tocar `sys.path`.
- Django resuelve el `app_label` a partir de `AppConfig.label` si se define — así las tablas de BD y migraciones usan el nombre corto `beauty_app`, no `apps_beauty_app`.
- Evitamos manipulación implícita de rutas que dificulta debugging y rompe herramientas de análisis estático.

**Implementación concreta en `apps.py`:**

```python
from django.apps import AppConfig

class BeautyAppConfig(AppConfig):
    name = 'apps.beauty_app'        # ruta de importación real
    label = 'beauty_app'            # label corto para migrations/DB
    default_auto_field = 'django.db.models.BigAutoField'
```

**Registro en INSTALLED_APPS:**

```python
INSTALLED_APPS = [
    # ...django apps...
    'apps.beauty_app',
]
```

### Diagrama de Componentes

```mermaid
graph TD
    subgraph "Repositorio BautyApp"
        MP[manage.py]
        subgraph "beautyfull/ (paquete proyecto)"
            URLS[urls.py]
            WSGI[wsgi.py]
            ASGI[asgi.py]
            subgraph "settings/"
                BASE[base.py]
                DEV[dev.py]
                PROD[prod.py]
            end
        end
        subgraph "apps/ (paquete contenedor)"
            subgraph "beauty_app/"
                APPS_PY[apps.py]
                MODELS[models.py]
                VIEWS[views.py]
                TEMPLATES[templates/base.html]
                TESTS[tests.py]
            end
        end
        subgraph "static/"
            CSS[css/]
            JS[js/]
        end
    end

    MP -->|DJANGO_SETTINGS_MODULE| DEV
    DEV -->|from .base import *| BASE
    BASE -->|INSTALLED_APPS| APPS_PY
```

---

## Components and Interfaces

### 1. `manage.py`

- Punto de entrada CLI estándar de Django.
- Define `DJANGO_SETTINGS_MODULE = 'beautyfull.settings.dev'` como valor por defecto.
- No manipula `sys.path` — la resolución de imports se delega al mecanismo de paquete Python.

### 2. Paquete `beautyfull/`

| Archivo | Responsabilidad |
|---------|----------------|
| `__init__.py` | Vacío — marca el directorio como paquete |
| `urls.py` | URLconf raíz — hace `include('apps.beauty_app.urls')` (mecanismo cableado desde ahora; `apps/beauty_app/urls.py` existe con `urlpatterns = []` vacío para que specs futuras solo agreguen rutas) |
| `wsgi.py` | Punto de entrada WSGI para producción |
| `asgi.py` | Punto de entrada ASGI para producción |

### 3. Paquete `beautyfull/settings/`

| Archivo | Responsabilidad |
|---------|----------------|
| `__init__.py` | Vacío — marca como paquete |
| `base.py` | Configuración compartida: INSTALLED_APPS, MIDDLEWARE, TEMPLATES, STATICFILES_DIRS, internacionalización, validación de variables de entorno |
| `dev.py` | `from .base import *`, DEBUG=True, SQLite local, SECRET_KEY de desarrollo (leída de .env) |
| `prod.py` | `from .base import *`, DEBUG=False, BD PostgreSQL (credenciales de env), ALLOWED_HOSTS desde env |

### 4. Paquete `apps/`

- `__init__.py` vacío que convierte `/apps/` en paquete Python importable.
- Cada app de negocio futura será un sub-paquete aquí.

### 5. App `apps.beauty_app`

| Archivo | Responsabilidad |
|---------|----------------|
| `apps.py` | `BeautyAppConfig` con `name='apps.beauty_app'`, `label='beauty_app'` |
| `templates/base.html` | Template base con bloques `title`, `content`, `extra_css`, `extra_js` |
| `models.py` | Vacío (sin modelos en esta spec) |
| `views.py` | Vista mínima o vacío |
| `urls.py` | URLconf de la app — existe con `urlpatterns = []` vacío; `beautyfull/urls.py` ya lo incluye vía `include('apps.beauty_app.urls')`, dejando el mecanismo cableado para cuando la app tenga rutas reales |
| `tests.py` | Smoke test |

### 6. Directorio `static/`

- `static/css/` — hojas de estilo (vacío inicialmente, referenciado desde `base.html`).
- `static/js/` — scripts (vacío inicialmente, referenciado desde `base.html`).
- Configurado en `base.py` con `STATICFILES_DIRS`.

---

## Data Models

Esta spec no define modelos de datos. El archivo `models.py` de `beauty_app` permanece vacío.

Las specs futuras (catálogo, reservas, pagos) crearán sus propios modelos en sus respectivas apps dentro de `/apps/`.

---

## Correctness Properties

Esta spec no define lógica de negocio, por lo que no se formulan propiedades de corrección complejas. Las propiedades verificables son:

### Property 1: Arranque limpio

**Validates: Requirements 5.1, 5.2, 5.3**

El proyecto Django arranca sin excepciones, sin warnings y sin errores de system check. Verificable mediante `python manage.py check` (0 issues) y `python manage.py runserver` (sin traceback ni WARNING).

### Property 2: Aislamiento de secretos

**Validates: Requirements 4.3, 4.4, 4.5**

Ningún archivo de settings contiene valores literales de SECRET_KEY, contraseñas de BD o claves de API. Verificable mediante inspección de código — todos los secretos se leen exclusivamente con `config()` de python-decouple.

### Property 3: Modularidad de la app núcleo

**Validates: Requirements 2.2, 3.3**

La app núcleo (`beauty_app`) es independiente — no importa ni depende de apps de negocio que no existen aún. Verificable mediante `python manage.py test apps.beauty_app` ejecutándose exitosamente sin ninguna otra app de negocio presente.

---

## Error Handling

### Variables de Entorno Faltantes

El mecanismo de lectura de variables de entorno en `base.py` utilizará la función `config()` de la librería `python-decouple`. Para variables obligatorias (SECRET_KEY, credenciales de BD en producción), NO se proporcionará valor por defecto:

```python
from decouple import config, UndefinedValueError

SECRET_KEY = config('SECRET_KEY')  # sin default → falla si no está definida
```

Si la variable no existe, `python-decouple` lanza `UndefinedValueError` con el nombre de la variable, impidiendo el arranque. Esto cumple el requisito 4.4.

### Modo de Desarrollo

En `dev.py`, la SECRET_KEY puede tener un valor por defecto explícitamente no-secreto para facilitar el desarrollo local:

```python
SECRET_KEY = config('SECRET_KEY', default='dev-insecure-key-not-for-production')
```

Esto es aceptable porque `dev.py` nunca se usa en producción y el valor default es evidentemente no-secreto.

### Errores de Importación de Apps

Si una app listada en `INSTALLED_APPS` no existe en `/apps/`, Django produce un `ModuleNotFoundError` estándar al ejecutar `manage.py check`. No se requiere manejo adicional.

---

## Testing Strategy

### Enfoque

Esta spec no contiene lógica de negocio susceptible de property-based testing. El único test requerido es un **smoke test** que verifica que el proyecto Django se configura e inicializa correctamente.

**¿Por qué no PBT?** No hay funciones puras con espacio de entrada variable. La spec define estructura de archivos y configuración — verificables con un test de integración mínimo (smoke test).

### Smoke Test

```python
# apps/beauty_app/tests.py
from django.test import TestCase
import django

class SmokeTest(TestCase):
    def test_django_setup_completes_without_exception(self):
        """Verifica que django.setup() se completa sin errores.
        
        Como el test runner ya invoca django.setup() antes de ejecutar
        los tests, si llegamos aquí sin excepción, la configuración es válida.
        """
        # django.setup() ya fue invocado por el test runner.
        # Verificamos que las apps están cargadas correctamente.
        from django.apps import apps
        self.assertTrue(apps.is_installed('apps.beauty_app'))
```

### Ejecución

```bash
python manage.py test apps.beauty_app
```

### Verificación Manual (check-list para CI/desarrollador)

| Comando | Resultado esperado | Req. |
|---------|-------------------|------|
| `python manage.py check` | 0 issues | 1.2, 5.2 |
| `python manage.py makemigrations --check --dry-run` | exit 0 | 5.4 |
| `python manage.py test apps.beauty_app` | 0 failures | 6.3 |
| `python manage.py runserver` (manual) | Arranca sin WARNING ni traceback | 5.1, 5.3 |

---

## Trazabilidad Requisitos → Verificación

| Requisito | Criterio | Método de Verificación |
|-----------|----------|----------------------|
| 1.1 | Proyecto denominado `beautyfull` en raíz | Inspección de estructura: existencia de `beautyfull/` |
| 1.2 | `manage.py check` sin errores | Comando: `python manage.py check` |
| 1.3 | Paquete con `__init__.py`, `urls.py`, `wsgi.py`, `asgi.py` | Inspección de estructura |
| 2.1 | `beauty_app` en `/apps/beauty_app/` | Inspección de estructura |
| 2.2 | Registrada en INSTALLED_APPS | Inspección de `base.py` + smoke test |
| 2.3 | `base.html` con bloques `title`, `content`, `extra_css`, `extra_js` | Inspección de template |
| 2.4 | `apps.py` con AppConfig válido | Inspección + `manage.py check` |
| 2.5 | `base.html` sin style inline ni script embebido | Inspección de template |
| 3.1 | Estructura mínima de app de negocio | Documentado (no se crea app de negocio en esta spec) |
| 3.2 | Nombre snake_case | Convención documentada |
| 3.3 | Separación de beauty_app | Convención documentada |
| 3.4 | Registro con `apps.<nombre>` | Ejemplo en INSTALLED_APPS |
| 4.1 | Settings en `base.py`, `dev.py`, `prod.py` + `__init__.py` | Inspección de estructura |
| 4.2 | `dev.py`/`prod.py` importan de `base.py` | Inspección de código |
| 4.3 | Secretos desde variables de entorno | Inspección de `base.py`/`prod.py` (uso de `config()`) |
| 4.4 | Fallo si variable requerida ausente | Test manual: ejecutar sin .env en prod |
| 4.5 | Sin secretos hardcodeados | Inspección de código |
| 4.6 | `dev.py` como default en `manage.py` | Inspección de `manage.py` |
| 4.7 | Selección de entorno vía `DJANGO_SETTINGS_MODULE` | Documentado + mecanismo estándar Django |
| 5.1 | Arranque sin traceback en <30s | Verificación manual con `runserver` |
| 5.2 | `manage.py check` → 0 issues | Comando |
| 5.3 | Sin WARNING de Django | Verificación manual con `runserver` |
| 5.4 | `makemigrations --check --dry-run` → exit 0 | Comando |
| 6.1 | Smoke test invoca `django.setup()` sin excepción | `python manage.py test` |
| 6.2 | Ejecutable con test runner estándar | `python manage.py test apps.beauty_app` |
| 6.3 | Exit 0, 0 failures | `python manage.py test` |
| 6.4 | Si setup falla, test falla indicando configuración inválida | Comportamiento del test runner |

---

## Dependencies

| Paquete | Versión (pin) | Justificación |
|---------|---------------|---------------|
| Django | >=5.1,<5.2 | LTS actual, soporte extendido |
| python-decouple | >=3.8,<4.0 | Lectura de variables de entorno sin dependencias adicionales |
| psycopg[binary] | >=3.1,<4.0 | Driver PostgreSQL requerido por `prod.py` — no se ejercita en esta spec (dev usa SQLite) pero se incluye para que el entorno de producción funcione sin pasos adicionales |

### Evaluación: `python-decouple` vs `django-environ` (DATABASE_URL)

**Contexto**: Plataformas de despliegue modernas (Railway, Render, Heroku) inyectan la conexión a BD como una sola variable `DATABASE_URL` en formato `postgres://user:pass@host:port/dbname`. El diseño actual usa 5 variables separadas (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT).

| Criterio | python-decouple | django-environ |
|----------|----------------|----------------|
| Soporte de `DATABASE_URL` nativo | No — requiere parsing manual o helper adicional | Sí — `env.db()` parsea `DATABASE_URL` automáticamente |
| Dependencias transitivas | Cero | Incluye wrappers para cache, email, search |
| Error explícito si falta variable | `UndefinedValueError` con nombre de variable | `ImproperlyConfigured` con nombre de variable |
| Complejidad de API | Mínima: `config('KEY')` | Mayor: `env('KEY')`, `env.db()`, `env.cache()`, etc. |
| Peso del paquete | ~15 KB | ~50 KB |

**Decisión: Se mantiene `python-decouple`.**

**Justificación:**
1. En esta spec, `dev.py` usa SQLite (sin variables de BD) y `prod.py` configura PostgreSQL. El parsing de `DATABASE_URL` no es necesario ahora.
2. Cuando una spec futura requiera despliegue en Railway/Render/Heroku, se puede migrar a `django-environ` o agregar un helper de 5 líneas que parsee `DATABASE_URL` con `urllib.parse`. El costo de migración es mínimo (renombrar `config()` → `env()`).
3. `python-decouple` cumple el requisito 4.4 (error explícito si falta variable) sin traer código no utilizado.
4. Se descarta `DATABASE_URL` en esta fase porque introduce complejidad prematura: no hay despliegue definido y el driver de PostgreSQL solo está presente como dependencia declarada, no ejercitada.

> **Nota**: Si en una spec futura se define la plataforma de despliegue y ésta requiere `DATABASE_URL`, reevaluar esta decisión.

---

## Decisiones de Diseño Adicionales

### Template `base.html`

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}BeautyFull{% endblock %}</title>
    {% load static %}
    <link rel="stylesheet" href="{% static 'css/main.css' %}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
    <script src="{% static 'js/main.js' %}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

- Sin atributos `style=""` ni `<script>` inline (requisito 2.5, steering frontend).
- CSS y JS cargados desde `/static/` (steering frontend-conventions).
- Bloques `title`, `content`, `extra_css`, `extra_js` (requisito 2.3).

### Convención para Apps de Negocio Futuras

Cuando se cree una nueva app (ej: `catalogo`):

1. Crear directorio `/apps/catalogo/` con archivos mínimos.
2. En `apps/catalogo/apps.py`:
   ```python
   class CatalogoConfig(AppConfig):
       name = 'apps.catalogo'
       label = 'catalogo'
       default_auto_field = 'django.db.models.BigAutoField'
   ```
3. Añadir `'apps.catalogo'` a `INSTALLED_APPS` en `base.py`.

### Archivo `.env.example`

```env
# Variables requeridas
SECRET_KEY=cambiar-en-produccion
# DATABASE (solo producción)
# DB_NAME=beautyfull_db
# DB_USER=beautyfull_user
# DB_PASSWORD=
# DB_HOST=localhost
# DB_PORT=5432
```

---

## Fuera de Alcance de Este Diseño

- Definición de modelos de datos (specs futuras).
- Sistema de diseño visual (placeholder en steering, se llenará en spec de UI).
- Lógica de autenticación/usuarios.
- CI/CD pipeline.
- Docker/containerización.
