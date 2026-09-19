# Requirements Document

## Introduction

BeautyFull es un marketplace digital para servicios profesionales de belleza y bienestar. Esta spec (Spec 01) **no** implementa lógica de negocio — únicamente construye la base técnica Django sobre la cual las specs futuras edificarán funcionalidades.

El alcance se limita a: estructura del proyecto, configuración de settings, app núcleo compartida y verificación de arranque sin errores.

## Glossary

- **Proyecto_Django**: Instancia raíz de Django configurada con `django-admin startproject`, que contiene settings, URLs raíz y configuración WSGI/ASGI.
- **App_Django**: Módulo reutilizable de Django (contiene models, views, urls, etc.) registrado en `INSTALLED_APPS`.
- **Beauty_App**: App núcleo compartida ubicada en `/apps/beauty_app/`, destinada a templates base, utilidades comunes y elementos transversales.
- **Settings_Split**: Patrón de configuración que separa settings en archivos `base.py`, `dev.py` y `prod.py` para aislar configuración por entorno.
- **Variable_de_Entorno**: Par clave-valor definido fuera del código fuente, usado para inyectar secretos y configuración específica del entorno en tiempo de ejecución.
- **Servidor_de_Desarrollo**: Servidor HTTP integrado de Django (`manage.py runserver`), usado exclusivamente en entorno local de desarrollo.
- **Smoke_Test**: Prueba mínima que verifica que el sistema arranca y responde sin errores, sin validar lógica de negocio.

## Requirements

### Requisito 1: Proyecto Django en la raíz

**User Story:** Como desarrollador, quiero que el repositorio contenga un proyecto Django correctamente estructurado en la raíz, para tener un punto de partida estandarizado sobre el cual construir funcionalidades.

#### Criterios de Aceptación

1. THE Proyecto_Django SHALL estar denominado `beautyfull` y ubicado en la raíz del repositorio.
2. THE Proyecto_Django SHALL contener un archivo `manage.py` en la raíz del repositorio que, al ejecutar `python manage.py check`, retorne el mensaje de cero problemas identificados sin errores.
3. THE Proyecto_Django SHALL contener un paquete de configuración `beautyfull/` con los archivos `__init__.py`, `urls.py`, `wsgi.py` y `asgi.py`.

---

### Requisito 2: App núcleo compartida

**User Story:** Como desarrollador, quiero una app Django núcleo para elementos compartidos (template base, utilidades comunes), para evitar duplicación entre apps de negocio futuras.

#### Criterios de Aceptación

1. THE Beauty_App SHALL estar ubicada en el directorio `/apps/beauty_app/`.
2. THE Beauty_App SHALL estar registrada en `INSTALLED_APPS` del Proyecto_Django.
3. THE Beauty_App SHALL contener un template base en `templates/base.html` (ruta relativa a la app) que defina, como mínimo, los bloques `title`, `content` y `extra_css`/`extra_js`, permitiendo que cualquier template hijo los sobrescriba mediante `{% extends "base.html" %}`.
4. THE Beauty_App SHALL contener un archivo `__init__.py` y un `apps.py` que declare una clase que herede de `AppConfig` con el atributo `name` apuntando a la app y `default_auto_field` definido.
5. THE base.html de Beauty_App SHALL estar libre de atributos `style` inline y de etiquetas `<script>` embebidas, delegando CSS a archivos en `/static/css/` y JS a archivos en `/static/js/`.

---

### Requisito 3: Estructura modular para apps de negocio

**User Story:** Como desarrollador, quiero que cada funcionalidad de negocio nueva sea una app Django independiente dentro de `/apps/`, para mantener separación de responsabilidades y facilitar el mantenimiento.

#### Criterios de Aceptación

1. WHEN se agregue una funcionalidad de negocio nueva, THE Proyecto_Django SHALL crearla como una App_Django independiente en `/apps/<nombre_app>/`, conteniendo como mínimo los archivos `__init__.py`, `apps.py`, `models.py`, `views.py` y `urls.py`.
2. THE Proyecto_Django SHALL nombrar cada app de negocio en formato snake_case compuesto exclusivamente por letras minúsculas, dígitos y guiones bajos, comenzando con una letra.
3. WHEN se agregue una funcionalidad de negocio nueva, THE Proyecto_Django SHALL mantenerla separada de Beauty_App — la nueva app no residirá como submódulo dentro del directorio de Beauty_App ni importará modelos o vistas internas de Beauty_App como parte de su propia definición.
4. WHEN se agregue una App_Django de negocio en `/apps/<nombre_app>/`, THE Proyecto_Django SHALL registrarla en INSTALLED_APPS utilizando la ruta con puntos `apps.<nombre_app>` para que Django la reconozca.

---

### Requisito 4: Settings separados por entorno

**User Story:** Como desarrollador, quiero los settings separados en archivos por entorno y con secretos inyectados por variables de entorno, para tener una configuración segura y flexible.

#### Criterios de Aceptación

1. THE Proyecto_Django SHALL organizar los settings en tres archivos: `base.py`, `dev.py` y `prod.py` dentro de un paquete `beautyfull/settings/`, incluyendo un archivo `__init__.py` que haga del directorio un paquete Python válido.
2. THE Settings_Split SHALL hacer que `dev.py` y `prod.py` importen todas las definiciones de `base.py` (mediante `from .base import *`) y sobreescriban únicamente los valores específicos de cada entorno.
3. THE Settings_Split SHALL leer los siguientes valores exclusivamente desde Variables_de_Entorno: SECRET_KEY, credenciales de base de datos (nombre, usuario, contraseña, host, puerto) y cualquier clave de API de servicios externos.
4. IF una Variable_de_Entorno requerida por los settings no está definida al iniciar la aplicación, THEN THE Settings_Split SHALL impedir el arranque del servidor y producir un mensaje de error indicando el nombre de la variable faltante.
5. THE Settings_Split SHALL no contener valores secretos (según se definen en el criterio 3) hardcodeados en ninguno de los archivos de settings; valores por defecto solo se permiten para configuraciones no sensibles.
6. THE Settings_Split SHALL definir `dev.py` como el settings por defecto para desarrollo local configurando `DJANGO_SETTINGS_MODULE = 'beautyfull.settings.dev'` en `manage.py`.
7. WHEN el desarrollador necesite ejecutar con configuración de producción, THE Settings_Split SHALL permitir la selección del entorno mediante la variable de entorno `DJANGO_SETTINGS_MODULE` con valor `beautyfull.settings.prod`.

---

### Requisito 5: Ejecución local sin errores

**User Story:** Como desarrollador, quiero que al completar esta spec el proyecto arranque localmente sin errores, para tener confianza de que la base técnica es funcional.

#### Criterios de Aceptación

1. WHEN se ejecute `python manage.py runserver`, THE Servidor_de_Desarrollo SHALL arrancar dentro de 30 segundos mostrando en la salida estándar el mensaje de inicio del servidor de desarrollo de Django sin ningún traceback ni mensaje de error.
2. WHEN se ejecute `python manage.py check`, THE Proyecto_Django SHALL reportar cero problemas (system check con 0 issues).
3. WHEN se ejecute `python manage.py runserver`, THE Servidor_de_Desarrollo SHALL producir una salida libre de líneas que contengan la palabra "WARNING" emitidas por el framework Django.
4. WHEN se ejecute `python manage.py makemigrations --check --dry-run`, THE Proyecto_Django SHALL finalizar con código de salida 0, indicando que no existen cambios de modelo pendientes de migración.

---

### Requisito 6: Smoke test de arranque

**User Story:** Como desarrollador, quiero un smoke test automatizado que verifique que el proyecto carga correctamente, para detectar regresiones en la base técnica.

#### Criterios de Aceptación

1. THE Proyecto_Django SHALL incluir un Smoke_Test que invoque `django.setup()` y verifique que la llamada se completa sin lanzar ninguna excepción.
2. THE Smoke_Test SHALL ser ejecutable mediante el test runner estándar de Django (`python manage.py test`).
3. WHEN el Smoke_Test se ejecute, THE Proyecto_Django SHALL finalizar con código de salida 0 y 0 tests fallidos reportados por el test runner.
4. IF `django.setup()` lanza una excepción durante el Smoke_Test, THEN THE Smoke_Test SHALL fallar indicando que la configuración del proyecto es inválida.

---

## Fuera de Alcance

- El campo "modalidad" (`a_domicilio`, `en_local`, `ambos`) para el futuro modelo Professional/Business **no** forma parte de esta spec.
- Lógica de negocio (catálogo, reservas, pagos, seguimiento) queda fuera de este alcance.
- Estos elementos se registrarán en un `roadmap.md` para referencia futura.

## Notas Técnicas

- **Testing**: Hypothesis (property-based testing) no aplica — no hay lógica de negocio aún. Solo se requiere un smoke test.
- **MCP autorizado**: Únicamente GitHub. Cualquier otro requiere solicitud explícita del usuario.
- **Hooks automáticos**: No se configuran en esta spec.
