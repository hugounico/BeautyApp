# Implementation Plan: data-model-core

## Overview

Esta spec implementa el modelo de datos central de BeautyFull: las cuatro apps de dominio (`usuarios`, `categorias`, `proveedores`, `servicios`) con sus modelos, migraciones y configuración del Django Admin para inspección manual. No incluye vistas, serializers, API ni lógica de negocio (salvo el `save()` de slug en `Categoria`, única excepción permitida por el Requirement 6.3).

El plan respeta el orden de dependencias definido en el diseño:

1. **`usuarios`** primero — define `AUTH_USER_MODEL`, es independiente y base de toda migración de `auth`.
2. **Reset manual de base de datos** (checkpoint irreversible) — DESPUÉS de definir `Usuario` + `AUTH_USER_MODEL`, ANTES de generar/aplicar migraciones.
3. **`categorias`** y **`proveedores`** — sin dependencias de dominio.
4. **`servicios`** último — depende de `categorias` y `proveedores` (referencias por string).

Cada tarea es incremental y se apoya en la anterior. Las tareas de código de las apps se preparan primero, luego el reset destruye el estado previo, y finalmente se generan y aplican todas las migraciones desde cero.

> **Entorno virtual obligatorio:** todas las tareas que ejecuten `python`, `pip`, `django-admin` o `manage.py` deben invocar el intérprete del venv con su ruta completa: `.\venv\Scripts\python.exe ...` y `.\venv\Scripts\django-admin.exe ...`. Al inicio de cualquier tarea que use el venv, confirmar `.\venv\Scripts\python.exe --version`. Separador de comandos en PowerShell: `;` (no `&&`). Edición de archivos de texto: SIEMPRE con herramientas nativas del IDE, NUNCA con PowerShell.

---

## Tasks

- [x] 1. Crear y registrar la app `usuarios`
  - Crear el directorio y scaffold de la app en `/apps/usuarios/` con `.\venv\Scripts\django-admin.exe startapp usuarios apps/usuarios` desde la raíz del repositorio.
  - Editar `apps/usuarios/apps.py`: clase `UsuariosConfig`, `name = 'apps.usuarios'`, `label = 'usuarios'`, `default_auto_field = 'django.db.models.BigAutoField'`.
  - Crear `apps/usuarios/urls.py` con únicamente `urlpatterns = []` (sin `path()` ni imports adicionales).
  - Registrar `'apps.usuarios'` en `INSTALLED_APPS` de `beautyfull/settings/base.py`, colocándola primero entre las apps de dominio.
  - _Requirements: 3.1, 6.1, 6.2, 6.5, 6.6_

- [x] 2. Definir el modelo `Usuario` y configurar `AUTH_USER_MODEL`
  - En `apps/usuarios/models.py`, definir `Usuario(AbstractUser)` sin campos adicionales, con `Meta` (`verbose_name = 'usuario'`, `verbose_name_plural = 'usuarios'`) y `__str__` retornando `self.get_full_name() or self.username`.
  - Agregar `AUTH_USER_MODEL = 'usuarios.Usuario'` en `beautyfull/settings/base.py`, cerca del bloque de configuración del proyecto.
  - Verificar que las tildes/minúsculas de `verbose_name` se conserven releyendo el archivo tras editar.
  - _Requirements: 3.2, 3.3, 3.6, 5.6, 6.1, 6.2, 6.4_

- [x] 3. **[TASK MANUAL — CHECKPOINT]** Reset de base de datos de desarrollo
  - ⚠️ **PASO MANUAL E IRREVERSIBLE — requiere confirmación explícita del desarrollador antes de ejecutar.** Destruye todos los datos de desarrollo en `db.sqlite3`. NO se automatiza silenciosamente.
  - **Precondición:** el modelo `Usuario` y `AUTH_USER_MODEL = 'usuarios.Usuario'` ya deben estar definidos (Task 2 completada). Este reset debe ocurrir ANTES de generar/aplicar cualquier migración de las 4 apps (Task 9).
  - Solicitar confirmación explícita del desarrollador. Solo tras el "sí" explícito, proceder con:
    - Eliminar el archivo `db.sqlite3`.
    - Eliminar todos los archivos de migración con nombre distinto a `__init__.py` en las apps bajo `/apps/` (p. ej. `apps/beauty_app/migrations/0001_initial.py` y equivalentes). Conservar cada `__init__.py`.
  - Motivo (del diseño): Django no permite cambiar el modelo de usuario una vez aplicadas las migraciones de `auth`; las migraciones de Spec 01 ya fueron aplicadas, por lo que el reset es obligatorio para adoptar el Custom User Model.
  - No ejecutar `makemigrations`/`migrate` aquí — eso ocurre en la Task 9, tras definir todas las apps.
  - **Trazabilidad del Requirement 3.12 (escenario defensivo NO ejecutado):** el Requirement 3.12 describe un escenario DEFENSIVO — ejecutar `migrate` con tablas de `auth` previas sin haber realizado el reset del Requirement 3.4. El orden del plan (Task 2 → Task 3 reset → Task 9 migrate) EVITA que ese escenario ocurra mediante el checkpoint obligatorio del Requirement 3.4. Esto NO equivale a haber verificado que Django produce exactamente el comportamiento de error descrito en 3.12 si alguien se salta el reset. NO se afirma que 3.12 esté "verificado", "probado" ni "satisfecho estructuralmente". El escenario NO se provocará artificialmente durante la implementación: construir deliberadamente el estado inconsistente que el reset busca evitar sería una prueba destructiva de bajo valor para el producto. Por lo tanto, 3.12 queda TRAZADO como escenario defensivo NO ejecutado de esta Spec, con esta justificación explícita — no como test automatizado aprobado.
  - _Requirements: 3.4, 3.12_

- [x] 4. Definir el modelo `Cliente`
  - En `apps/usuarios/models.py`, definir `Cliente` con: `usuario` (`OneToOneField(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='perfil_cliente')`), `telefono` (`CharField(max_length=20, blank=True, null=True)`), `preferencias` (`TextField(blank=True, validators=[MaxLengthValidator(2000)])`), `fecha_creacion` (`DateTimeField(auto_now_add=True)`).
  - `Meta`: `verbose_name = 'cliente'`, `verbose_name_plural = 'clientes'`, `ordering = ['usuario__username']`. `__str__` retorna `str(self.usuario)`.
  - Importar `MaxLengthValidator` desde `django.core.validators` y `settings` desde `django.conf`.
  - _Requirements: 3.5, 3.7, 6.1, 6.2_

- [x] 5. Configurar el Django Admin de la app `usuarios`
  - En `apps/usuarios/admin.py`, registrar `Usuario` con una clase `UsuarioAdmin(UserAdmin)` (heredando de `django.contrib.auth.admin.UserAdmin`): `list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']`, `list_filter = ['is_staff', 'is_active', 'is_superuser']`, `search_fields = ['username', 'email', 'first_name', 'last_name']`.
  - Registrar `Cliente` con `ClienteAdmin(admin.ModelAdmin)`: `list_display = ['usuario', 'telefono', 'fecha_creacion']`, `list_filter = []`, `search_fields = ['usuario__username', 'usuario__email', 'telefono']`.
  - _Requirements: 3.8, 3.9, 6.1, 6.2_

- [x] 6. Crear la app `categorias` con modelo `Categoria` y Admin
  - [x] 6.1 Crear y registrar la app `categorias`
    - Scaffold con `.\venv\Scripts\django-admin.exe startapp categorias apps/categorias`.
    - Editar `apps/categorias/apps.py`: `CategoriasConfig`, `name = 'apps.categorias'`, `label = 'categorias'`, `default_auto_field = 'django.db.models.BigAutoField'`.
    - Crear `apps/categorias/urls.py` con únicamente `urlpatterns = []`.
    - Registrar `'apps.categorias'` en `INSTALLED_APPS`.
    - _Requirements: 1.1, 6.1, 6.2, 6.5, 6.6_
  - [x] 6.2 Definir el modelo `Categoria` con generación de slug
    - Campos: `nombre` (`CharField(max_length=100, unique=True)`), `slug` (`SlugField(max_length=110, unique=True, blank=True)`), `activo` (`BooleanField(default=True)`).
    - `Meta`: `verbose_name = 'categoría'`, `verbose_name_plural = 'categorías'`, `ordering = ['nombre']`. `__str__` retorna `self.nombre`.
    - Sobrescribir `save()` (única lógica permitida, Req 6.3): si `slug` vacío, generar con `_generar_slug_unico()` usando `django.utils.text.slugify`, truncar a 110, y resolver colisiones con sufijo incremental (`-2`, `-3`, …) recortando el base para no exceder 110 caracteres, excluyendo la propia instancia (`exclude(pk=self.pk)`).
    - _Requirements: 1.2, 1.3, 1.5, 6.1, 6.2, 6.3, 6.4_
  - [x] 6.3 Configurar el Admin de `categorias`
    - Registrar `Categoria` con `CategoriaAdmin`: `list_display = ['nombre', 'slug', 'activo']`, `list_filter = ['activo']`, `search_fields = ['nombre', 'slug']`.
    - _Requirements: 1.6_

- [x] 7. Crear la app `proveedores` con modelo `ProveedorProfesional` y Admin
  - [x] 7.1 Crear y registrar la app `proveedores`
    - Scaffold con `.\venv\Scripts\django-admin.exe startapp proveedores apps/proveedores`.
    - Editar `apps/proveedores/apps.py`: `ProveedoresConfig`, `name = 'apps.proveedores'`, `label = 'proveedores'`, `default_auto_field = 'django.db.models.BigAutoField'`.
    - Crear `apps/proveedores/urls.py` con únicamente `urlpatterns = []`.
    - Registrar `'apps.proveedores'` en `INSTALLED_APPS`.
    - _Requirements: 4.1, 6.1, 6.2, 6.5, 6.6_
  - [x] 7.2 Definir `ModalidadChoices` y el modelo `ProveedorProfesional`
    - `ModalidadChoices(models.TextChoices)`: `A_DOMICILIO = 'a_domicilio', 'A domicilio'`; `EN_LOCAL = 'en_local', 'En local'`; `AMBOS = 'ambos', 'Ambos'`.
    - Campos: `nombre_comercial` (`CharField(max_length=150)`), `es_negocio` (`BooleanField(default=False)`), `modalidad` (`CharField(max_length=20, choices=ModalidadChoices.choices, default=ModalidadChoices.A_DOMICILIO)`), `ubicacion` (`CharField(max_length=255, blank=True, null=True)`), `biografia` (`TextField(max_length=500, blank=True)`), `activo` (`BooleanField(default=True)`).
    - `Meta`: `verbose_name = 'proveedor profesional'`, `verbose_name_plural = 'proveedores profesionales'`, `ordering = ['nombre_comercial']`. `__str__` retorna `self.nombre_comercial`.
    - _Requirements: 4.2, 4.3, 4.4, 6.1, 6.2, 6.4_
  - [x] 7.3 Configurar el Admin de `proveedores`
    - Registrar `ProveedorProfesional` con `ProveedorProfesionalAdmin`: `list_display = ['nombre_comercial', 'es_negocio', 'modalidad', 'activo']`, `list_filter = ['activo', 'modalidad', 'es_negocio']`, `search_fields = ['nombre_comercial', 'biografia']`.
    - _Requirements: 4.5_

- [x] 8. Crear la app `servicios` con modelo `Servicio` y Admin
  - [x] 8.1 Crear y registrar la app `servicios`
    - Scaffold con `.\venv\Scripts\django-admin.exe startapp servicios apps/servicios`.
    - Editar `apps/servicios/apps.py`: `ServiciosConfig`, `name = 'apps.servicios'`, `label = 'servicios'`, `default_auto_field = 'django.db.models.BigAutoField'`.
    - Crear `apps/servicios/urls.py` con únicamente `urlpatterns = []`.
    - Registrar `'apps.servicios'` en `INSTALLED_APPS`, al final (depende de `categorias` y `proveedores`).
    - _Requirements: 2.1, 6.1, 6.2, 6.5, 6.6_
  - [x] 8.2 Definir el modelo `Servicio`
    - Campos: `nombre` (`CharField(max_length=150)`), `descripcion` (`TextField(blank=True)`), `duracion_minutos` (`PositiveIntegerField(validators=[MinValueValidator(1)])`), `precio_base_clp` (`PositiveIntegerField(validators=[MinValueValidator(1)])`), `categoria` (`ForeignKey('categorias.Categoria', on_delete=PROTECT, related_name='servicios')`), `proveedores` (`ManyToManyField('proveedores.ProveedorProfesional', blank=True, related_name='servicios')`), `activo` (`BooleanField(default=True)`).
    - Usar referencias por string en `categoria` y `proveedores` para evitar imports cíclicos (Req 5.5). Importar `MinValueValidator` desde `django.core.validators`.
    - `Meta`: `verbose_name = 'servicio'`, `verbose_name_plural = 'servicios'`, `ordering = ['categoria', 'nombre']`. `__str__` retorna `self.nombre`.
    - _Requirements: 2.2, 2.3, 2.4, 5.5, 6.1, 6.2, 6.4_
  - [x] 8.3 Configurar el Admin de `servicios`
    - Registrar `Servicio` con `ServicioAdmin`: `list_display = ['nombre', 'categoria', 'duracion_minutos', 'precio_base_clp', 'activo']`, `list_filter = ['activo', 'categoria']`, `search_fields = ['nombre', 'descripcion']`.
    - _Requirements: 2.6_

- [x] 9. Generar y aplicar migraciones de las cuatro apps
  - **Precondición de inspección no destructiva (antes de `makemigrations`):** inspeccionar los directorios `migrations/` de todas las apps bajo `/apps/` y confirmar que, tras la Task 3, NO permanece ningún archivo de migración distinto de `__init__.py`. Si aparece algún archivo de migración inesperado, DETENERSE y reportarlo — NO eliminarlo automáticamente, NO continuar con `makemigrations` hasta resolver la inconsistencia.
  - Confirmar el venv: `.\venv\Scripts\python.exe --version`.
  - Ejecutar `.\venv\Scripts\python.exe manage.py makemigrations` (SIN restringir a nombres de apps específicos, para cubrir todas las apps afectadas por el reset de la Task 3 — incluida `apps.beauty_app` de Spec 01) y confirmar exit 0, sin errores en stderr. Verificar que `servicios.0001_initial` declara dependencia de `categorias.0001_initial` y `proveedores.0001_initial`, y que `usuarios.0001_initial` no depende de las otras tres.
  - Ejecutar `.\venv\Scripts\python.exe manage.py migrate` y confirmar que crea las tablas `usuarios_usuario`, `usuarios_cliente`, `categorias_categoria`, `proveedores_proveedorprofesional`, `servicios_servicio` y la intermedia `servicios_servicio_proveedores`, con exit 0.
  - Mostrar el output textual de ambos comandos antes de marcar completa la tarea.
  - _Requirements: 1.7, 1.8, 2.7, 2.8, 3.10, 3.11, 4.6, 4.7, 5.3_

- [x] 10. Escribir tests por modelo
  - [x] 10.1 Tests unitarios de `Categoria`
    - Creación válida; `__str__` retorna `nombre`; generación automática de slug al guardar; colisión de slug produce sufijo `-2`, `-3`; unicidad de `nombre` y `slug` vía `IntegrityError`; campo requerido y `max_length` de `nombre`/`slug` vía `full_clean()`.
    - _Requirements: 1.3, 1.4_
  - [ ]* 10.2 Property test — formato de slug válido
    - **Feature: data-model-core, Property 1: Para toda `Categoria` con `nombre` no vacío, el `slug` generado contiene exclusivamente letras minúsculas ASCII, dígitos y guiones, y su longitud no supera 110 caracteres.**
    - Usar `hypothesis` con mínimo 100 iteraciones.
    - **Validates: Requirements 1.3**
  - [ ]* 10.3 Property test — unicidad de slug bajo colisión
    - **Feature: data-model-core, Property 2: Para toda secuencia de `Categoria`s cuyos nombres producen el mismo slug base, todos los `slug` almacenados son distintos entre sí (sufijo incremental), respetando el límite de 110 caracteres.**
    - Usar `hypothesis` con mínimo 100 iteraciones.
    - **Validates: Requirements 1.3**
  - [x] 10.4 Tests unitarios de `Servicio`
    - Creación válida con `categoria`; `__str__` retorna `nombre`; `MinValueValidator(1)` rechaza `duracion_minutos = 0` y `precio_base_clp = 0` vía `full_clean()`; eliminar una `Categoria` con servicios asociados lanza `ProtectedError`; asociación M2M con proveedores.
    - _Requirements: 2.5_
  - [x] 10.5 Tests unitarios de `Usuario` y `Cliente`
    - `Usuario`: creación vía `create_user`; `__str__` retorna `get_full_name()` con nombre y `username` sin nombre.
    - `Cliente`: creación con `OneToOne` a `Usuario`; `__str__` delega a `str(self.usuario)`; `MaxLengthValidator(2000)` rechaza `preferencias` de más de 2000 caracteres vía `full_clean()`; `CASCADE` elimina el `Cliente` al borrar el `Usuario`.
    - _Requirements: 3.5_
  - [x] 10.6 Tests unitarios de `ProveedorProfesional`
    - Creación válida; `__str__` retorna `nombre_comercial`; `modalidad` fuera de `ModalidadChoices` rechazada vía `full_clean()`; `nombre_comercial` vacío o >150 caracteres rechazado vía `full_clean()`.
    - _Requirements: 4.8, 4.9_

- [x] 11. Verificación global del sistema
  - Confirmar el venv: `.\venv\Scripts\python.exe --version`.
  - Ejecutar `.\venv\Scripts\python.exe manage.py check` y confirmar cero issues (exit 0) con las cuatro apps registradas y sin errores de importación cíclica.
  - Ejecutar `.\venv\Scripts\python.exe manage.py makemigrations --check` y confirmar exit 0 (no genera migraciones nuevas).
  - Ejecutar `.\venv\Scripts\python.exe manage.py test` y confirmar 0 fallos y 0 errores, sin regresiones de Spec 01.
  - Confirmar `settings.AUTH_USER_MODEL == 'usuarios.Usuario'` (p. ej. vía `manage.py shell` o un test dedicado).
  - Verificar a nivel de sistema las convenciones de nombrado: clases (modelos, AppConfig, Admin) en PascalCase y archivos/apps/campos en snake_case.
  - Mostrar el output textual de cada comando antes de marcar completa la tarea.
  - **Reporte final de cierre de la verificación obligatoria** (como parte de esta task, incluir explícitamente):
    - resultado de `manage.py check`;
    - resultado de `manage.py makemigrations --check`;
    - resultado de `manage.py test`, incluyendo cantidad de tests ejecutados / passed / failed / skipped si el runner lo informa;
    - confirmación de `settings.AUTH_USER_MODEL == 'usuarios.Usuario'`;
    - cualquier desviación detectada respecto de Requirements o Design.
  - _Requirements: 5.1, 5.2, 5.4, 5.6, 6.1, 6.2_

---

## Notes

- Las tareas marcadas con `*` (10.2, 10.3) son property-based tests opcionales; la cobertura mínima obligatoria se cumple con los tests unitarios basados en ejemplos. Si se implementan, usar `hypothesis` con mínimo 100 iteraciones por propiedad y etiquetar cada test con **Feature: data-model-core, Property {número}: {texto}**, coherente con la sección Correctness Properties del diseño.
- La **Task 3 es manual e irreversible** (reset de base de datos): requiere confirmación explícita del desarrollador y está ubicada entre la definición de `Usuario` + `AUTH_USER_MODEL` (Task 2) y la generación de migraciones (Task 9), según el Requirement 3.4.
- **Requirement 3.12 — escenario defensivo NO ejecutado:** el Requirement 3.12 describe un escenario defensivo (ejecutar `migrate` con tablas de `auth` previas sin haber realizado el reset del Requirement 3.4). El orden del plan (Task 2 → Task 3 reset → Task 9 migrate) EVITA ese escenario mediante el checkpoint obligatorio del Requirement 3.4, pero esto NO equivale a haber verificado que Django produce exactamente el comportamiento de error descrito en 3.12 si alguien omite el reset. NO se afirma que 3.12 esté "verificado", "probado" ni "satisfecho estructuralmente". El escenario no se provocará artificialmente durante la implementación: construir deliberadamente el estado inconsistente que el reset busca evitar sería una prueba destructiva de bajo valor para el producto. Por lo tanto, 3.12 queda TRAZADO como escenario defensivo NO ejecutado, no como test automatizado aprobado.
- Cada tarea referencia los sub-requirements específicos que cubre para trazabilidad completa.
- Entorno virtual obligatorio con ruta completa (`.\venv\Scripts\python.exe`); edición de archivos de texto solo con herramientas nativas del IDE; verificación con evidencia (releer archivo / mostrar output) antes de reportar éxito.

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2"] },
    { "id": 2, "tasks": ["3"] },
    { "id": 3, "tasks": ["4", "5", "6.1", "6.2", "6.3", "7.1", "7.2", "7.3", "8.1"] },
    { "id": 4, "tasks": ["8.2", "8.3"] },
    { "id": 5, "tasks": ["9"] },
    { "id": 6, "tasks": ["10.1", "10.4", "10.5", "10.6"] },
    { "id": 7, "tasks": ["11"] },
    { "id": 8, "tasks": ["10.2", "10.3"], "optional": true, "note": "Property-based tests opcionales (hypothesis). Fuera del camino crítico; NO bloquean Task 11 ni el cierre de la verificación obligatoria." }
  ]
}
```
