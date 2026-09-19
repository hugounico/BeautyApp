# Implementation Plan

## Overview

Esta spec construye la fundación técnica del proyecto Django (BeautyFull Spec 01), sin lógica de negocio. Las tareas siguen un orden de dependencias estricto: primero se crean los paquetes Python que serán referenciados (`apps/`, `apps/beauty_app/`), luego el proyecto raíz (`beautyfull/`) y la configuración (`settings/`), y finalmente los pasos de verificación positiva y negativa que validan el arranque limpio.

---

## Task Dependency Graph

| Tarea | Depende de |
|-------|-----------|
| Task 1 — Dependencias y `.env.example` | _(ninguna)_ |
| Task 2 — Paquete contenedor `apps/` | _(ninguna)_ |
| Task 3 — App núcleo `apps/beauty_app/` | Task 2 |
| Task 4 — Paquete raíz `beautyfull/` + `manage.py` + `urls.py` | Task 3 |
| Task 5 — Settings split `beautyfull/settings/` | Task 3, Task 4 |
| Task 6 — Directorio `static/` | Task 5 (necesita que `STATICFILES_DIRS` en `base.py` ya exista) |
| Task 7 — Smoke test | Task 3, Task 5 |
| Task 8 — Verificación de arranque (camino positivo) | Tasks 1–7 |
| Task 9 — Verificación de fallo por variable faltante (camino negativo) | Task 5 (necesita que `prod.py` exista para probar su fallo) |

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": [1, 2],
      "description": "Sin dependencias — pueden ejecutarse en paralelo o en cualquier orden"
    },
    {
      "wave": 2,
      "tasks": [3],
      "description": "Requiere Wave 1 (Task 2: paquete apps/ debe existir)"
    },
    {
      "wave": 3,
      "tasks": [4],
      "description": "Requiere Wave 2 (Task 3: beauty_app debe existir para el include en urls.py)"
    },
    {
      "wave": 4,
      "tasks": [5],
      "description": "Requiere Wave 2 y Wave 3 (Tasks 3 y 4 deben existir)"
    },
    {
      "wave": 5,
      "tasks": [6, 7, 9],
      "description": "Requiere Wave 4 (Task 5: base.py con STATICFILES_DIRS y settings completos; prod.py para Task 9)"
    },
    {
      "wave": 6,
      "tasks": [8],
      "description": "Requiere Waves 1–5 (Tasks 1–7 y Task 9 completas)"
    }
  ]
}
```

---

## Tasks

- [x] 1. Inicializar dependencias y archivo de entorno
  - Crear `requirements.txt` con los pins definidos en el diseño: `Django>=5.1,<5.2`, `python-decouple>=3.8,<4.0`, `psycopg[binary]>=3.1,<4.0`. Completado.
  - Crear `.env.example` con `SECRET_KEY` y las variables de BD de producción comentadas (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT). Completado.
  - Crear entorno virtual: `python -m venv venv`. Completado.
  - Instalar dependencias con `.\venv\Scripts\python.exe -m pip install -r requirements.txt`. Completado — Django 5.1.15, python-decouple 3.8, psycopg 3.3.5 instalados.
  - _Requirements: 4.3, 4.5_

- [x] 2. Crear el paquete contenedor `apps/`
  - Ejecutar `mkdir apps` desde la raíz del repositorio para crear el directorio (no existe comando de Django para esto).
  - Crear `apps/__init__.py` (vacío) que convierte `/apps/` en un paquete Python importable sin manipular `sys.path`.
  - _Requirements: 3.1, 3.4_

- [x] 3. Implementar la app núcleo `apps/beauty_app/`
  - [x] 3.1 Scaffoldear la app con `.\venv\Scripts\django-admin.exe startapp beauty_app apps/beauty_app` desde la raíz del repositorio.
    - Este comando es standalone (no depende de `manage.py`, que aún no existe en este punto) y genera `__init__.py`, `apps.py`, `models.py`, `views.py`, `tests.py`, `admin.py` y `migrations/`.
    - Editar el `apps.py` generado: renombrar la clase a `BeautyAppConfig`, establecer `name = 'apps.beauty_app'`, `label = 'beauty_app'` y confirmar `default_auto_field = 'django.db.models.BigAutoField'`.
    - El `tests.py` generado por defecto será reemplazado por el smoke test en Task 7 — no eliminarlo aquí.
    - _Requirements: 2.1, 2.4, 3.4_
  - [x] 3.2 Confirmar `models.py` y `views.py` generados por el comando.
    - Dejar `models.py` vacío (el comando lo genera con un comentario; se puede mantener o limpiar).
    - Dejar `views.py` vacío o mínimo — el comando lo genera vacío por defecto.
    - _Requirements: 2.1_
  - [x] 3.3 Crear `apps/beauty_app/urls.py` con `urlpatterns = []` vacío.
    - Deja el mecanismo de include ya cableado con el URLconf raíz para que specs futuras solo agreguen rutas.
    - _Requirements: 1.3_
  - [x] 3.4 Crear `apps/beauty_app/templates/base.html`.
    - Definir los bloques `title`, `content`, `extra_css` y `extra_js`.
    - Cargar CSS y JS desde `/static/` con `{% static %}`; sin atributos `style=""` inline ni etiquetas `<script>` embebidas.
    - _Requirements: 2.3, 2.5_

- [x] 4. Crear el paquete raíz `beautyfull/` y `manage.py`
  - [x] 4.1 Scaffoldear el proyecto con `.\venv\Scripts\django-admin.exe startproject beautyfull .` desde la raíz del repositorio.
    - El punto final es obligatorio: evita crear una carpeta `beautyfull/beautyfull/` duplicada y coloca `manage.py` directamente en la raíz.
    - Este comando genera `manage.py`, `beautyfull/__init__.py`, `beautyfull/settings.py`, `beautyfull/urls.py`, `beautyfull/wsgi.py` y `beautyfull/asgi.py`.
    - **Eliminar** el `beautyfull/settings.py` generado — será reemplazado por el paquete `settings/` (con `base.py`, `dev.py`, `prod.py`) definido en Task 5. No editarlo in situ.
    - Actualizar `DJANGO_SETTINGS_MODULE = 'beautyfull.settings.dev'` en `manage.py`, `wsgi.py` y `asgi.py` (el comando genera `beautyfull.settings` por defecto).
    - No manipular `sys.path` — la resolución de imports se delega al mecanismo de paquete Python.
    - _Requirements: 1.1, 1.3, 4.6, 4.7_
  - [x] 4.2 Crear `beautyfull/urls.py` como URLconf raíz.
    - Incluir `path('', include('apps.beauty_app.urls'))` — la app referenciada ya existe (Task 3), por lo que el include no rompe el proyecto.
    - _Requirements: 1.3_

- [x] 5. Implementar el settings split en `beautyfull/settings/`
  - [x] 5.1 Crear `beautyfull/settings/__init__.py` (vacío) y `base.py` con la configuración compartida.
    - Definir `INSTALLED_APPS` incluyendo las apps de Django y `'apps.beauty_app'` — la app ya existe (Task 3), por lo que el registro no produce ModuleNotFoundError.
    - Configurar `MIDDLEWARE`, `TEMPLATES` (con `APP_DIRS = True`), internacionalización, `STATIC_URL` y `STATICFILES_DIRS` apuntando a `/static/`.
    - Leer `SECRET_KEY` con `config('SECRET_KEY')` de python-decouple, sin valor por defecto.
    - No hardcodear ningún secreto en `base.py`.
    - _Requirements: 4.1, 4.3, 4.4, 4.5_
  - [x] 5.2 Crear `dev.py` con `from .base import *`.
    - `DEBUG = True`, BD SQLite local, `SECRET_KEY` con default no-secreto explícito para desarrollo (`config('SECRET_KEY', default='dev-insecure-key-not-for-production')`).
    - _Requirements: 4.1, 4.2, 4.6_
  - [x] 5.3 Crear `prod.py` con `from .base import *`.
    - `DEBUG = False`, BD PostgreSQL con credenciales leídas de variables de entorno sin default (falla si faltan), `ALLOWED_HOSTS` desde env.
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.7_

- [x] 6. Crear el directorio `static/`
  - Crear `static/css/` y `static/js/` (vacíos inicialmente, referenciados desde `base.html`).
  - Confirmar que `STATICFILES_DIRS` en `base.py` apunta a estas rutas.
  - _Requirements: 2.5_

- [x] 7. Implementar el smoke test
  - Reemplazar el `apps/beauty_app/tests.py` generado por `django-admin startapp` (vacío) con una clase `SmokeTest(TestCase)`.
  - El test verifica que las apps están cargadas correctamente tras `django.setup()` (p. ej. `apps.is_installed('apps.beauty_app')`), fallando si la configuración es inválida.
  - _Requirements: 6.1, 6.2, 6.4_

- [x] 8. Verificar arranque limpio del proyecto (camino positivo)
  - Ejecutar `.\venv\Scripts\python.exe manage.py check` y confirmar 0 issues.
  - Ejecutar `.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run` y confirmar exit 0.
  - Ejecutar `.\venv\Scripts\python.exe manage.py test apps.beauty_app` y confirmar 0 failures (exit 0).
  - Ejecutar `.\venv\Scripts\python.exe manage.py runserver` manualmente y confirmar arranque sin traceback ni líneas WARNING del framework.
  - Reportar el resultado (éxito/falla) de cada comando antes de marcar la tarea como completa.
  - _Requirements: 1.2, 5.1, 5.2, 5.3, 5.4, 6.3_

- [x] 9. Verificar el comportamiento de fallo por variable de entorno faltante (camino negativo)
  - Ejecutar con `DJANGO_SETTINGS_MODULE=beautyfull.settings.prod` sin `.env` presente y sin `SECRET_KEY` exportada: `$env:DJANGO_SETTINGS_MODULE='beautyfull.settings.prod'; .\venv\Scripts\python.exe manage.py check`
  - Confirmar que el comando falla con exit code distinto de 0 y que el error es un `UndefinedValueError` que menciona explícitamente `SECRET_KEY`.
  - Reportar el resultado (éxito/falla) igual que el resto de los comandos de verificación antes de marcar la tarea como completa.
  - _Requirements: 4.4_

---

## Notes

- **Entorno virtual obligatorio**: Todas las tareas que ejecuten `python`, `pip`, `django-admin` o `manage.py` (Tasks 3, 4, 5, 7, 8 y 9) deben invocar el intérprete del venv con su ruta completa: `.\venv\Scripts\python.exe ...` (para python/pip/manage.py) y `.\venv\Scripts\django-admin.exe ...` (para django-admin). No usar `Activate.ps1` — la política de ejecución de PowerShell en este entorno bloquea ese script.
- **Tramo Task 4 → Task 5 no es 100% ejecutable de forma aislada**: en ese punto `manage.py` ya apunta a `beautyfull.settings.dev`, pero el paquete `settings/` aún no existe. Esto es inherente al orden de arranque de Django (el proyecto raíz debe existir antes de que sus settings puedan definirse como paquete separado), no un defecto del ordenamiento de tareas. No intentar ejecutar `manage.py check` entre estas dos tareas.
- **Único MCP autorizado en esta fase: GitHub**. No habilitar Hooks automáticos ni servidores MCP de Documentation o PostgreSQL sin pedido explícito del usuario.
