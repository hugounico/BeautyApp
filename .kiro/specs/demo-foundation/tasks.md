# Implementation Plan: demo-foundation

## Overview

Este plan convierte el diseño aprobado de la fundación de BeautyFull en una serie de pasos de código incrementales y trazables a los requerimientos R1–R6. El orden está pensado para que cada tarea construya sobre la anterior sin dejar código huérfano: primero el cambio de modelo y su migración (R1), luego la configuración de settings y autenticación nativa (R2), después el registro público (R3), el comando `seed_demo` (R4), el shell visual (R5), y finalmente el escenario integral y la verificación de no-regresión (R6).

El trabajo respeta los Steering del workspace (`naming-conventions`, `frontend-conventions`, `architecture`, `execution-conventions`), que se referencian y no se repiten. **No** se usan property-based tests: toda la verificación es con `django.test.TestCase` / `Client`, conforme al diseño y a la Nota final de R6.

### Convenciones de ejecución aplicables a TODAS las tareas

- Toda edición de archivos de texto (`.py`, `.html`, `.md`, `.css`, `.js`, `.txt`) se realiza **exclusivamente** con las herramientas nativas del IDE (lectura, escritura, reemplazo de fragmento). **Prohibido** editar texto con PowerShell (`Set-Content`, `Get-Content`+`.Replace()`, heredocs, redirecciones `>`/`>>`, `[System.IO.File]::WriteAllText`).
- PowerShell (`execute_pwsh`) se reserva para: `pip`, `manage.py`, `django-admin`, crear directorios (`New-Item`/`mkdir`) y correr tests/verificaciones.
- Antes de cualquier tarea que dependa del entorno, confirmar el venv: `.\venv\Scripts\python.exe --version`.
- Verificación con evidencia: tras editar un archivo, releerlo y mostrar el fragmento relevante; tras ejecutar un comando, mostrar su output completo y textual. Un comando sin error no es evidencia por sí mismo.
- Ante dos fallos del mismo enfoque, detenerse y reportar (comando exacto, error textual, paso afectado) antes de reintentar o cambiar de estrategia.

## Tasks

- [x] 0. T0 — Preflight / baseline READ-ONLY (no modifica archivos)
  - Verificar y mostrar evidencia textual de: rama actual, HEAD actual y `git status --short`.
  - Ejecutar `git diff v0.1-data-model-core -- apps/proveedores/models.py apps/usuarios/models.py` y confirmar que el diff está **vacío** (nada cambió desde la verificación de campos hecha en Design: `nombre_comercial`, `fecha_creacion`, `preferencias`). Si el diff **no** está vacío, DETENERSE y reportar qué cambió antes de continuar — no asumir que las verificaciones de Design siguen válidas.
  - Confirmar el Python del venv: `.\venv\Scripts\python.exe --version`.
  - Ejecutar `.\venv\Scripts\python.exe manage.py test` y confirmar que los 31 tests baseline siguen en verde.
  - Ejecutar `.\venv\Scripts\python.exe manage.py check` y confirmar que no hay errores.
  - Inspeccionar (solo lectura) la estructura actual de URLs, templates y static relevante para R2, R3 y R5 (qué existe hoy antes de tocarlo).
  - Si T0 encuentra cualquier otra contradicción con Requirements o Design, DETENERSE y reportarla. No corregir automáticamente arquitectura, modelos, settings ni Design. No continuar a Wave 1.
  - _Requisitos: R6.1, R6.2 (verificación de baseline previa a la implementación)_

- [x] 1. R1 — Vínculo opcional `Usuario` ⇄ `ProveedorProfesional` (modelo, migración y admin)
  - [x] 1.1 Agregar el campo `usuario` a `ProveedorProfesional`
    - En `apps/proveedores/models.py`, importar `settings` (`from django.conf import settings`) y agregar a `ProveedorProfesional` un `OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name='perfil_proveedor')`.
    - Documentar en el docstring del campo/modelo que el vínculo de proveedor es **opcional** (`null/blank`) frente al de `Cliente` que es requerido, ambos con `on_delete=CASCADE` (dato declarativo para R1.7).
    - Mantener nombres según `naming-conventions` (campo `usuario` en snake_case; clase en PascalCase).
    - _Requisitos: R1.1, R1.2, R1.3, R1.4, R1.7, R1.8_

  - [x] 1.2 Generar la migración nullable sin backfill
    - Ejecutar `.\venv\Scripts\python.exe manage.py makemigrations proveedores` para generar un `AddField` del campo `usuario` como nullable.
    - Verificar (releyendo el archivo de migración generado) que es un `AddField` con `null=True` y que **no** solicita valor de relleno, de modo que las filas existentes queden con `usuario = NULL` sin pérdida de datos.
    - _Requisitos: R1.6_

  - [x] 1.3 Exponer `usuario` como editable en `ProveedorProfesionalAdmin`
    - En `apps/proveedores/admin.py`, hacer `usuario` editable (incluirlo en `fields`/`fieldsets` o dejarlo disponible), permitiendo asociar (seleccionar un `Usuario`) y desasociar (dejar vacío → persiste `NULL`).
    - Preservar `list_display`, `list_filter` y `search_fields` existentes; opcionalmente agregar `usuario` a `list_display`.
    - _Requisitos: R1.5_

  - [x] 1.4 Tests del vínculo de proveedor
    - Con `django.test.TestCase`: R1.1 (introspección del campo: `related_name='perfil_proveedor'`, `null/blank`, CASCADE); R1.2 (guardar sin `usuario` no lanza error); R1.3 (segundo `ProveedorProfesional` con un `Usuario` ya vinculado es rechazado y el vínculo previo queda intacto); R1.4 (borrar el `Usuario` elimina el `ProveedorProfesional` por CASCADE); R1.6 (filas existentes quedan con `usuario=NULL`); R1.8 (un `Usuario` puede no tener ni cliente ni proveedor; sin roles).
    - R1.5: test de admin que verifica que `usuario` es editable.
    - Para R1.6 se usa la verificación automatizada más simple que demuestre el comportamiento requerido (migración `AddField` nullable sin backfill + comportamiento del modelo), sin construir infraestructura de migration testing compleja para un solo criterio.
    - R1.7 es declarativo → **excluido** de test.
    - _Requisitos: R1.1, R1.2, R1.3, R1.4, R1.5, R1.6, R1.8_

- [x] 2. R2 — Autenticación nativa en `apps.usuarios`
  - [x] 2.1 Configurar destinos de autenticación en settings
    - En `beautyfull/settings/base.py` agregar `LOGIN_URL = 'login'`, `LOGIN_REDIRECT_URL = 'home'` y `LOGOUT_REDIRECT_URL = 'home'` (Destino_Por_Defecto compartido por dev y prod).
    - No modificar `MIDDLEWARE`, `TEMPLATES`, `AUTH_USER_MODEL` ni estáticos (ya presentes en la baseline).
    - _Requisitos: R2.8, R2.9_

  - [x] 2.2 Implementar vistas de login y logout nativas
    - En `apps/usuarios/views.py`, definir el login sobre `django.contrib.auth.views.LoginView` con `template_name` namespaced, `redirect_authenticated_user=True`, autenticando por `username`.
    - Garantizar mensaje de error visible **en español** ante credenciales inválidas (apoyado en `LANGUAGE_CODE='es-cl'`), sin iniciar sesión ni modificar la sesión previa.
    - Validar `next` con la semántica de `django.utils.http.url_has_allowed_host_and_scheme`: ruta relativa interna segura → redirige allí; ausente/vacío/externo → `LOGIN_REDIRECT_URL = home`.
    - Definir el logout sobre `django.contrib.auth.views.LogoutView` (solo POST; GET no cierra sesión), redirigiendo a `LOGOUT_REDIRECT_URL = home`.
    - _Requisitos: R2.1, R2.2, R2.3, R2.4, R2.5, R2.7, R2.8, R2.9, R2.10_

  - [x] 2.3 Plantilla de login y rutas con nombre
    - Crear la plantilla de login namespaced en `apps/usuarios/templates/usuarios/` que **extiende `base.html`** mediante `{% extends %}` (`frontend-conventions`; sin estilos/JS inline).
    - En `apps/usuarios/urls.py` definir las rutas con nombre `login` (GET, POST) y `logout` (POST), e incluir la URLconf de `usuarios` en `beautyfull/urls.py`.
    - _Requisitos: R2.4, R2.6, R2.11, R5.5_

  - [x] 2.4 Tests de autenticación
    - Integración con `Client`: R2.1 (login válido inicia sesión); R2.2 (login inválido → error en español, no inicia sesión); R2.3 (login fallido preserva sesión previa); R2.4/R2.6 (logout solo vía POST con CSRF); R2.5 (logout vía GET no cierra sesión); R2.7 (`next` interno seguro redirige allí); R2.8 (`next` ausente/externo → `home`); R2.9 (logout POST → `home`); R2.10 (usuario autenticado pidiendo login/registro → `home`).
    - Render: R2.11 (plantilla de login extiende `base.html`).
    - _Requisitos: R2.1, R2.2, R2.3, R2.4, R2.5, R2.6, R2.7, R2.8, R2.9, R2.10, R2.11_

- [x] 3. Checkpoint — Asegurar que los tests pasan
  - Ejecutar la suite y mostrar la evidencia textual completa. Ante un fallo nuevo, una regresión o un resultado inesperado, DETENERSE y reportar, sin continuar automáticamente. No modificar tests existentes solo para forzar verde.

- [x] 4. R3 — Registro público de clientes en `apps.usuarios`
  - [x] 4.1 Implementar `RegistroClienteForm`
    - En `apps/usuarios/forms.py`, crear `RegistroClienteForm` (PascalCase) reutilizando la mecánica de `UserCreationForm`: `username` (obligatorio, rechaza duplicados), `password1`/`password2` (obligatorios, validados por los validadores activos de Django, deben coincidir), más campos opcionales `telefono` (`CharField`) y `preferencias` (`TextField`, `MaxLengthValidator(2000)`) del `Cliente`.
    - Mensajes de error en español (incluido "las contraseñas no coinciden").
    - _Requisitos: R3.2, R3.3, R3.4, R3.9_

  - [x] 4.2 Implementar `RegistroClienteView`
    - En `apps/usuarios/views.py`, crear `RegistroClienteView` (PascalCase) que:
      - Crea únicamente `Usuario` + `Cliente` (`related_name='perfil_cliente'`), sin `ProveedorProfesional`; fuerza `is_staff=False`, `is_superuser=False`, sin grupos ni permisos.
      - Realiza toda escritura dentro de `with transaction.atomic():`; **ninguna** escritura (ni `form.save()` parcial) ocurre antes de abrir la transacción; `fecha_creacion` se fija por `auto_now_add`.
      - Ante fallo intermedio: rollback total (sin `Usuario` huérfano ni `Cliente` sin `Usuario`) + mensaje de error en español vía `messages`.
      - En éxito: `login()` automático, redirección a `home` y mensaje de bienvenida en español.
      - Datos inválidos / `username` duplicado → re-render con errores en español, sin crear registros.
      - Si `request.user.is_authenticated`, redirige a `home` sin mostrar el formulario.
    - _Requisitos: R3.1, R3.5, R3.6, R3.7, R3.8, R3.9, R2.10_

  - [x] 4.3 Plantilla y ruta de registro
    - Crear la plantilla de registro namespaced en `apps/usuarios/templates/usuarios/` que **extiende `base.html`** (`frontend-conventions`).
    - En `apps/usuarios/urls.py` definir la ruta con nombre `registro` (GET, POST).
    - Al crear la ruta `registro`, completar la verificación diferida de la Task 7.1 confirmando mediante `reverse()` que `home`, `login`, `logout` y `registro` resuelven correctamente.
    - _Requisitos: R3.10, R5.5_

  - [x]* 4.4 Tests de registro
    - Integración con `Client`: R3.1/R3.5 (crea solo `Usuario`+`Cliente`, no privilegiado, sin proveedor); R3.3 (contraseña validada por validadores de Django); R3.4 (contraseñas distintas → error en español, sin registros); R3.6 (creación atómica + `fecha_creacion` auto); R3.7 (fallo en transacción → rollback total, sin huérfanos); R3.8 (éxito → auto-login + redirect `home` + mensaje de bienvenida); R3.9 (`username` duplicado/datos inválidos → errores en español, sin registros).
    - Ejemplo: R3.2 (el form expone los campos obligatorios y opcionales esperados); render R3.10 (plantilla de registro extiende `base.html`).
    - _Requisitos: R3.1, R3.2, R3.3, R3.4, R3.5, R3.6, R3.7, R3.8, R3.9, R3.10_

- [x] 5. R4 — Comando `seed_demo` en `apps.beauty_app`
  - [x] 5.1 Crear el esqueleto del management command
    - Crear el paquete `apps/beauty_app/management/commands/` (con sus `__init__.py` vía `New-Item`/`mkdir` para los directorios) y el archivo `seed_demo.py` con `class Command(BaseCommand)` y `handle()`.
    - _Requisitos: R4.1_

  - [x] 5.2 Fail-before-write de contraseñas desde entorno
    - Al inicio de `handle()`, **antes de cualquier escritura y antes de abrir la transacción**, leer `DEMO_CLIENTE_PASSWORD` y `DEMO_PROVEEDOR_PASSWORD` con `decouple.config` **sin fallback**.
    - Capturar `decouple.UndefinedValueError` y terminar con `CommandError` indicando el **nombre** de la variable ausente, dejando la BD sin cambios.
    - _Requisitos: R4.8, R4.9_

  - [x] 5.3 Dataset idempotente dentro de una transacción atómica
    - Toda la escritura ocurre dentro de un único `with transaction.atomic():` (rollback total ante fallo).
    - Upsert por claves naturales con `update_or_create`/`get_or_create`: `Categoria` por `nombre`; `Servicio` por `(categoria, nombre)`; `ProveedorProfesional` por `nombre_comercial` con marcador estable `[DEMO]`; usuarios demo por `username`.
    - Crear 3 categorías (Peluquería, Manicure, Masajes) y 6 servicios (Corte Niño, Corte Adulto, Coloración; Manicure Permanente; Masaje Relajante, Masaje Descontracturante), todos con `precio_base_clp=20000`.
    - Los 6 servicios demo usan `duracion_minutos=60`; `seed_demo` administra/converge ese campo para esos 6 servicios. Es un valor uniforme del dataset de Demo Socios v0.1 para satisfacer el modelo (campo obligatorio, ≥1) y mantener la demo determinista; NO es una regla comercial definitiva de BeautyFull.
    - Crear exactamente 3 proveedores demo con marcador `[DEMO]`.
    - Cablear el M2M `Servicio.proveedores`: cada servicio con ≥1 proveedor y ≥1 servicio con ≥2 proveedores (reparto determinista).
    - Política de convergencia: administra **solo** sus propias claves naturales, **nunca** borra registros ajenos y converge **solo** los campos definidos en el dataset (incl. re-aplicar `set_password` y `precio_base_clp=20000`); sin campo `is_demo` ni campos nuevos en modelos.
    - _Requisitos: R4.1, R4.2, R4.3, R4.5, R4.6, R4.7_

  - [x] 5.4 Usuarios demo y selección determinista del proveedor con cuenta
    - Crear `cliente_demo` (`Usuario` + `Cliente`) y `proveedor_demo` (`Usuario`) vinculado por el `OneToOneField` de R1 a **exactamente uno** de los 3 proveedores demo.
    - La selección se basa en un flag `recibe_cuenta_demo=True` **hard-coded en la estructura de datos en-Python** del comando sobre exactamente una entrada de proveedor (determinista y estable entre ejecuciones; **no** lexicográfico, **no** un campo nuevo del modelo, **no** derivado de `nombre_comercial`).
    - _Requisitos: R4.4_

  - [x] 5.5 Resumen de salida y documentación de variables
    - Al finalizar con éxito, imprimir vía `self.stdout.write` el conteo de registros **creados** y **actualizados**.
    - Documentar en `.env.example` los nombres `DEMO_CLIENTE_PASSWORD` y `DEMO_PROVEEDOR_PASSWORD` **sin valores** (edición con herramienta nativa del IDE).
    - _Requisitos: R4.10, R4.11_

  - [x]* 5.6 Tests del comando `seed_demo`
    - Integración (invocando el comando): R4.1 (3 categorías / 6 servicios, `precio_base_clp=20000`); R4.2 (3 proveedores demo con marcador estable); R4.3 (cada servicio ≥1 proveedor, ≥1 servicio con ≥2); R4.4 (`cliente_demo`, `proveedor_demo` vinculado al proveedor marcado `recibe_cuenta_demo=True`); R4.5/R4.6 (segunda ejecución converge sin duplicar ni tocar no-demo); R4.7 (fallo intermedio → rollback total); R4.8/R4.9 (contraseñas desde env sin fallback; variable ausente → aborta sin escribir, nombrando la variable); R4.11 (salida con conteo creados/actualizados).
    - Ejemplo (archivo): R4.10 (`.env.example` documenta ambas variables sin valores).
    - _Requisitos: R4.1, R4.2, R4.3, R4.4, R4.5, R4.6, R4.7, R4.8, R4.9, R4.10, R4.11_

- [x] 6. Checkpoint — Asegurar que los tests pasan
  - Ejecutar la suite y mostrar la evidencia textual completa. Ante un fallo nuevo, una regresión o un resultado inesperado, DETENERSE y reportar, sin continuar automáticamente. No modificar tests existentes solo para forzar verde.

- [x] 7. R5 — Shell visual base en `apps.beauty_app`
  - [x] 7.1 Home mínima y ruta con nombre
    - Crear la vista Home (contenido global, sin catálogo: sin listados de servicios, categorías ni proveedores) y su plantilla namespaced `apps/beauty_app/templates/beauty_app/home.html` que extiende `base.html`.
    - En `apps/beauty_app/urls.py` definir la ruta con nombre `home` e incluirla en `beautyfull/urls.py`. Ejecutada en Wave 2 por dependencia real de R2; en este punto se verifica que `home`, `login` y `logout` resuelven por nombre. La verificación de `registro` queda diferida a la Task 4.3.
    - _Requisitos: R5.4, R5.5_

  - [x] 7.2 Componentes globales navbar y mensajes
    - Crear `apps/beauty_app/templates/components/navbar.html` (navbar responsive mobile-first) y `apps/beauty_app/templates/components/messages.html` (recorre `messages`; **no** renderiza ningún elemento si no hay mensajes activos).
    - Lógica de estado de navbar **server-side y localizada en `navbar.html`**, usando las relaciones inversas reales `perfil_proveedor` / `perfil_cliente` sobre `request.user`, con prioridad anónimo → proveedor → cliente → neutro (exactamente un estado por petición). **Sin** context processor, **sin** custom template tag, **sin** sistema de roles.
    - Estados: ANÓNIMO (Ingresar→`login`, Registrarse→`registro`, sin logout); PROVEEDOR, CLIENTE y NEUTRO (estado + logout como `<form method="post">` con `{% csrf_token %}` hacia `logout`, ocultando Ingresar/Registrarse).
    - _Requisitos: R5.3, R5.6, R5.7, R5.8, R5.9, R5.10_

  - [x] 7.3 Evolucionar `base.html` e integrar CSS/JS estáticos
    - En `apps/beauty_app/templates/base.html`: preservar `lang="es"`, los bloques `title`/`extra_css`/`content`/`extra_js` y la carga de `css/main.css` + `js/main.js`; incluir la navbar vía `{% include 'components/navbar.html' %}` y los mensajes vía `{% include 'components/messages.html' %}`.
    - Agregar el CSS de la navbar en `/static/css/` y el JS (p. ej. toggle del menú móvil) en `/static/js/`. **Sin** `style=""` ni `<script>` inline; sin frameworks externos ni CDN (`frontend-conventions`).
    - _Requisitos: R5.1, R5.2_

  - [x]* 7.4 Tests del shell visual
    - Render: R5.1/R5.2 (`base.html` conserva bloques, `lang="es"`, carga estáticos; navbar sin inline style/script).
    - Integración: R5.3 (bloque de mensajes muestra activos y nada cuando no hay); R5.4 (Home resoluble por `home`, sin catálogo); R5.6 (navbar anónimo: Ingresar + Registrarse, sin logout); R5.7 (proveedor: estado + logout, sin Ingresar/Registrarse); R5.8 (cliente: estado + logout); R5.9 (neutro/superusuario: autenticado neutro + logout); R5.10 (exactamente un estado por petición según prioridad).
    - Ejemplo: R5.5 (`home`, `login`, `logout`, `registro` resuelven por `reverse`).
    - _Requisitos: R5.1, R5.2, R5.3, R5.4, R5.5, R5.6, R5.7, R5.8, R5.9, R5.10_

- [x] 8. R6 — Escenario integral y verificación de no-regresión
  - [x] 8.1 Test del escenario integral
    - Test de flujo que ejecuta la secuencia `seed_demo` → registro → logout → login y verifica en cada paso que la navbar refleje el estado correcto: tras registro → cliente (autenticado); tras logout → anónimo; tras login → autenticado.
    - _Requisitos: R6.5_

  - [x] 8.2 Verificación de calidad y no-regresión
    - Esta tarea ASUME que las sub-tareas de testing 1.4, 2.4, 4.4, 5.6, 7.4 y 8.1 ya se ejecutaron y pasaron antes de este gate final.
    - Confirmar el venv: `.\venv\Scripts\python.exe --version`.
    - Ejecutar y mostrar el output textual completo de: `.\venv\Scripts\python.exe manage.py check` (salida 0, sin warnings), `.\venv\Scripts\python.exe manage.py makemigrations --check` (0 pendientes) y `.\venv\Scripts\python.exe manage.py test` (31 tests existentes + nuevos, 0 fallos / 0 errores).
    - Si cualquiera falla, considerar la fundación **no integrable** y no marcarla como aprobada.
    - _Requisitos: R6.1, R6.2, R6.3, R6.6_

## Notes

- El marcador `*` identifica trabajo de **testing**, pero **no** es opcional ni postergable: los tests de cada incremento son **obligatorios** para cerrar su Wave antes de avanzar a la siguiente. En particular, la Task 8.1 (escenario integral, R6.5) es **obligatoria**.
- **No** se usan property-based tests: toda la verificación es con `django.test.TestCase` / `Client`, conforme al diseño y a la Nota final de R6.
- Cada tarea referencia los requisitos específicos que satisface para trazabilidad; R1.7 es declarativo y queda documentado en el modelo, no verificado por test (R6.4).
- Los checkpoints (tareas 3 y 6) permiten validación incremental antes de avanzar.
- La secuencialidad de las Waves 0–6 es una DECISIÓN DE EJECUCIÓN para facilitar la auditoría y aislar regresiones, NO una dependencia arquitectónica real entre todos los bloques.
- La secuencia por bloques funcionales es la estrategia de ejecución predeterminada; una dependencia técnica real entre Waves tiene precedencia sobre ese agrupamiento y requiere detenerse, reportar y, una vez autorizada, ejecutarse anticipadamente sin alterar la trazabilidad del Requirement al que pertenece. Task 7.1 se ejecuta en Wave 2 por esta razón: los redirects de R2 requieren la named URL 'home'.
- Durante la ejecución de Wave 3 (R3) se detectó que la baseline no tenía `AUTH_PASSWORD_VALIDATORS` configurado (Django lo deja vacío por defecto, dejando R3.3 sin validadores activos). Se agregó la configuración estándar de validadores de contraseña de Django en `beautyfull/settings/base.py` como dependencia técnica real de Wave 3, siguiendo el mismo patrón que la dependencia de la named URL 'home' en Wave 2: detectada en ejecución, reportada y resuelta bajo autorización, sin alterar la trazabilidad de los Requirements.
- Se respetan los Steering del workspace (`naming-conventions`, `frontend-conventions`, `architecture`, `execution-conventions`); edición de texto siempre con herramientas nativas del IDE, PowerShell solo para `pip`/`manage.py`/`mkdir`/tests.
- Antes de realizar verificaciones funcionales contra la BD de desarrollo, comprobar que las migraciones requeridas por el código estén aplicadas mediante `showmigrations`/`migrate --plan`. Una migración inesperada debe detener la ejecución y reportarse antes de aplicar cambios.

## Diagrama de dependencias entre tareas (top-level)

La secuencialidad mostrada es una DECISIÓN DE EJECUCIÓN (auditoría y aislamiento de regresiones), NO una dependencia arquitectónica real entre todos los bloques.

```mermaid
graph TD
    W0[Wave 0: T0 Preflight READ-ONLY] --> W1[Wave 1: R1 Modelo + migración + admin + tests]
    W1 --> W2[Wave 2: R2 Autenticación nativa + Task 7.1 (Home, dependencia real) + tests + Checkpoint tarea 3]
    W2 --> W3[Wave 3: R3 Registro de clientes + tests]
    W3 --> W4[Wave 4: R4 seed_demo + tests + Checkpoint tarea 6]
    W4 --> W5[Wave 5: R5 Shell visual (navbar/base/estáticos) + tests]
    W5 --> W6[Wave 6: R6 Integral + gates finales]
```

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["0"] },
    { "id": 1, "tasks": ["1.1", "1.2", "1.3", "1.4"] },
    { "id": 2, "tasks": ["2.1", "2.2", "2.3", "7.1", "2.4", "3"] },
    { "id": 3, "tasks": ["4.1", "4.2", "4.3", "4.4"] },
    { "id": 4, "tasks": ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "6"] },
    { "id": 5, "tasks": ["7.2", "7.3", "7.4"] },
    { "id": 6, "tasks": ["8.1", "8.2"] }
  ]
}
```
