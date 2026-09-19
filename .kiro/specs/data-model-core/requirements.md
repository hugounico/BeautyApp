# Requirements Document

## Introduction

Este spec define el modelo de datos central de BeautyFull: las cuatro apps de dominio que sirven de base para el flujo MVP completo (Cliente → selección de servicio → ubicación/fecha → profesional → reserva → pago → servicio completado → comisión → cashback → evaluación).

El alcance es exclusivamente **modelos Django, migraciones y configuración del Django Admin** para inspección manual. No incluye vistas, serializers, API REST, lógica de negocio ni templates de cara al usuario.

Las cuatro apps nuevas son: `categorias`, `servicios`, `usuarios` y `proveedores`. Cada una vive en `/apps/<nombre>/` y se registra en `INSTALLED_APPS` como `'apps.<nombre>'`.

---

## Glossary

- **Sistema**: la aplicación Django BeautyFull en su conjunto.
- **Categoria**: clasificación temática de servicios de belleza (ej: "Manicure", "Masajes", "Peluquería").
- **Servicio**: prestación concreta ofrecida dentro de una Categoria (ej: "Manicure gel").
- **Usuario**: cuenta de autenticación basada en `AbstractUser` de Django; es la identidad de acceso al sistema.
- **Cliente**: perfil de reservas asociado uno-a-uno a un Usuario; almacena datos específicos del flujo de citas.
- **ProveedorProfesional**: persona o negocio que ofrece servicios; puede atender a domicilio, en local, o ambas modalidades.
- **App Django**: paquete Python bajo `/apps/` con `AppConfig.name = 'apps.<nombre>'` y `AppConfig.label = '<nombre>'`.
- **Django Admin**: interfaz de administración integrada de Django, accesible en `/admin/`.
- **AbstractUser**: clase base de Django para modelos de usuario personalizados; extiende los campos de autenticación estándar sin perder las funcionalidades del sistema de auth.
- **slug**: identificador URL-amigable derivado del nombre, compuesto solo de letras minúsculas, números y guiones.
- **CLP**: peso chileno; precio sin decimales.
- **modalidad**: tipo de atención que ofrece un ProveedorProfesional (`a_domicilio`, `en_local`, `ambos`).

---

## Decisiones de Diseño Transversales

Esta sección documenta las cuatro decisiones de arquitectura que afectan a múltiples requirements. Se incluyen aquí para que queden registradas antes de los requisitos específicos.

### Decisión 1 — Categorias: estructura plana vs. jerárquica

**Opción A — Plana**: cada `Categoria` es independiente; no hay relación padre/hijo.

**Opción B — Jerárquica**: `Categoria` tiene un `ForeignKey` autorreferencial opcional (`padre`) que permite sub-categorías (ej: "Uñas" → "Gel", "Acrílico").

**Recomendación: Opción A — Plana**, por las siguientes razones:
- El MVP no requiere filtrado por sub-categoría ni navegación de árbol.
- Una jerarquía autorreferencial complica las consultas (ORM recursivo) y el Admin sin beneficio inmediato.
- Si en el futuro se necesita jerarquía, migrar de plana a autorreferencial es una operación menor (agregar un campo nullable). El camino inverso (eliminar jerarquía ya usada) es más costoso.

### Decisión 2 — Usuarios y Clientes: Custom User Model (AbstractUser) vs. OneToOne a `auth.User`

**Opción A — AbstractUser**: se crea `apps.usuarios.Usuario` como Custom User Model (`AUTH_USER_MODEL = 'usuarios.Usuario'`). El modelo `Cliente` tiene un `OneToOneField` a `Usuario`.

**Opción B — OneToOne a `auth.User` por defecto**: se usa `django.contrib.auth.User` sin modificar; `Cliente` extiende con `OneToOneField`.

**Recomendación: Opción A — AbstractUser**, por las siguientes razones:
- Django recomienda explícitamente definir un Custom User Model desde el inicio de cualquier proyecto; cambiarlo después de crear las primeras migraciones es significativamente más costoso.
- Permite agregar campos de autenticación en el futuro (ej: campo de teléfono como username, login con email) sin workarounds.
- La Opción B bloquea esas extensiones y genera deuda técnica confirmada.

**⚠️ Costo obligatorio a declarar — Reset de base de datos de desarrollo:**
Adoptar `AbstractUser` implica definir `AUTH_USER_MODEL` antes de ejecutar la primera migración de `django.contrib.auth`. Como las migraciones de Spec 01 ya fueron ejecutadas en `db.sqlite3`, adoptar esta opción **requiere**:
1. Eliminar `db.sqlite3`.
2. Eliminar todos los archivos de migración existentes (en `apps/beauty_app/migrations/` y cualquier otra app).
3. Volver a ejecutar `manage.py migrate` desde cero.

Este costo es **aceptable en desarrollo** (la base SQLite es desechable). En producción, este tipo de cambio requeriría una migración de datos cuidadosa. Como el proyecto no tiene entorno de producción activo, la decisión se toma con pleno conocimiento del trade-off.

### Decisión 3 — ProveedorProfesional: entidad única con flag vs. dos entidades separadas

**Opción A — Entidad única con flag**: un solo modelo `ProveedorProfesional` con campo booleano `es_negocio` que distingue entre profesional independiente y negocio/local.

**Opción B — Dos entidades separadas**: `ProfesionalIndependiente` y `NegocioLocal` como modelos distintos con herencia de tabla concreta o abstracta.

**Recomendación: Opción A — Entidad única con flag**, por las siguientes razones:
- En el MVP, ambos tipos comparten prácticamente todos los campos (nombre comercial, modalidad, ubicación, estado activo).
- Una sola entidad simplifica la relación ManyToMany con `Servicio` y la asignación futura de agenda.
- Escalar a múltiples empleados por negocio se puede resolver con una relación futura `ProveedorProfesional.empleados` (ForeignKey autorreferencial o app `agenda`) sin romper el modelo base.
- La Opción B introduce complejidad prematura y dificulta queries polimórficos en el MVP.

### Decisión 4 — Precio y duración por servicio: valor único vs. por proveedor (diferida)

El `ManyToManyField` simple entre `Servicio` y `ProveedorProfesional` (Requirement 2, criterio 3) asume que el precio base y la duración estimada son únicos por servicio, compartidos por todos los proveedores que lo ofrecen.

**Simplificación deliberada del MVP**: en la práctica, cada proveedor podría fijar su propio precio o duración para el mismo servicio. Modelar esto requeriría un modelo intermedio explícito (`through='OfertaProveedor'`) con campos `precio` y `duracion` propios por relación proveedor-servicio.

**Decisión**: NO se implementa el modelo intermedio en esta spec. El `ManyToManyField` simple es suficiente para el MVP. La evolución a `through='OfertaProveedor'` con precio/duración por proveedor queda **pendiente para un spec futuro de tarifas/ofertas**. Se documenta aquí para que la decisión no se pierda y no se descubra como efecto secundario más adelante.

---

## Requirements

### Requirement 1: App `categorias` y modelo `Categoria`

**User Story:** Como administrador del sistema, quiero gestionar categorías de servicios con nombre único y estado activo, para poder organizar el catálogo de servicios en clasificaciones temáticas reconocibles por clientes y proveedores.

#### Acceptance Criteria

1. THE Sistema SHALL crear la app `categorias` en `/apps/categorias/` con `AppConfig.name = 'apps.categorias'` y `AppConfig.label = 'categorias'`, y registrarla en `INSTALLED_APPS` de `beautyfull/settings/base.py`.

2. THE Sistema SHALL definir el modelo `Categoria` en `apps/categorias/models.py` con los campos: `nombre` (CharField, único, max 100 caracteres), `slug` (SlugField, único, max 110 caracteres), `activo` (BooleanField, default `True`), y los metadatos `verbose_name = 'Categoría'`, `verbose_name_plural = 'Categorías'`, `ordering = ['nombre']`.

3. WHEN el administrador guarda una `Categoria` con un `nombre` no vacío y sin `slug` previo asignado manualmente, THE Sistema SHALL generar y almacenar automáticamente el `slug` derivado del `nombre`, compuesto exclusivamente por letras minúsculas ASCII, dígitos y guiones, con longitud máxima de 110 caracteres, garantizando unicidad mediante sufijo numérico incremental (`-2`, `-3`, …) en caso de colisión.

4. IF el `nombre` de una `Categoria` supera 100 caracteres o está vacío, THEN THE Sistema SHALL rechazar el guardado con un error de validación indicando que el campo `nombre` es requerido y tiene un máximo de 100 caracteres.

5. THE Sistema SHALL implementar el método `__str__` del modelo `Categoria` retornando el campo `nombre`.

6. THE Sistema SHALL registrar el modelo `Categoria` en el Django Admin de la app `categorias` con `list_display = ['nombre', 'slug', 'activo']`, `list_filter = ['activo']` y `search_fields = ['nombre', 'slug']`.

7. WHEN se ejecuta `manage.py makemigrations categorias`, THE Sistema SHALL generar el archivo de migración inicial `0001_initial.py` sin errores.

8. WHEN se ejecuta `manage.py migrate`, THE Sistema SHALL aplicar la migración de `categorias` y crear la tabla `categorias_categoria` en la base de datos sin errores.

---

### Requirement 2: App `servicios` y modelo `Servicio`

**User Story:** Como administrador del sistema, quiero definir servicios con duración, precio base y categoría asociada, para construir el catálogo que clientes y proveedores usarán en el flujo de reservas.

#### Acceptance Criteria

1. THE Sistema SHALL crear la app `servicios` en `/apps/servicios/` con `AppConfig.name = 'apps.servicios'` y `AppConfig.label = 'servicios'`, y registrarla en `INSTALLED_APPS` de `beautyfull/settings/base.py`.

2. THE Sistema SHALL definir el modelo `Servicio` en `apps/servicios/models.py` con los campos: `nombre` (CharField, max 150 caracteres), `descripcion` (TextField, blank permitido), `duracion_minutos` (PositiveIntegerField, valor mínimo 1), `precio_base_clp` (PositiveIntegerField, valor mínimo 1), `categoria` (ForeignKey a `categorias.Categoria`, `on_delete=PROTECT`), `activo` (BooleanField, default `True`), y los metadatos `verbose_name = 'Servicio'`, `verbose_name_plural = 'Servicios'`, `ordering = ['categoria', 'nombre']`.

3. THE Sistema SHALL definir en el modelo `Servicio` un campo `proveedores` (ManyToManyField a `proveedores.ProveedorProfesional`, `blank=True`, `related_name='servicios'`) que representa qué proveedores ofrecen cada servicio.

4. THE Sistema SHALL implementar el método `__str__` del modelo `Servicio` retornando el campo `nombre`.

5. IF se intenta eliminar una `Categoria` que tiene `Servicio`s asociados, THEN THE Sistema SHALL lanzar `ProtectedError` e impedir la eliminación, preservando la integridad referencial.

6. THE Sistema SHALL registrar el modelo `Servicio` en el Django Admin de la app `servicios` con `list_display = ['nombre', 'categoria', 'duracion_minutos', 'precio_base_clp', 'activo']`, `list_filter = ['activo', 'categoria']` y `search_fields = ['nombre', 'descripcion']`.

7. WHEN se ejecuta `manage.py makemigrations servicios`, THE Sistema SHALL generar el archivo de migración inicial `0001_initial.py` con código de salida 0 y sin mensajes de error en stderr.

8. WHEN se ejecuta `manage.py migrate`, THE Sistema SHALL aplicar la migración de `servicios` y crear las tablas `servicios_servicio` y `servicios_servicio_proveedores` en la base de datos, con código de salida 0 y sin mensajes de error en stderr.

---

### Requirement 3: App `usuarios`, modelo `Usuario` y modelo `Cliente`

**User Story:** Como administrador del sistema, quiero un modelo de autenticación extensible y un perfil de cliente separado, para poder gestionar identidades de acceso y datos de reservas de forma independiente, sin comprometer la capacidad de extender el sistema de autenticación en el futuro.

#### Acceptance Criteria

1. THE Sistema SHALL crear la app `usuarios` en `/apps/usuarios/` con `AppConfig.name = 'apps.usuarios'` y `AppConfig.label = 'usuarios'`, y registrarla en `INSTALLED_APPS` de `beautyfull/settings/base.py`.

2. THE Sistema SHALL definir el modelo `Usuario` en `apps/usuarios/models.py` heredando de `django.contrib.auth.models.AbstractUser`, sin campos adicionales en esta versión, con los metadatos `verbose_name = 'Usuario'` y `verbose_name_plural = 'Usuarios'`.

3. THE Sistema SHALL configurar `AUTH_USER_MODEL = 'usuarios.Usuario'` en `beautyfull/settings/base.py` para que todo el sistema de autenticación de Django use el modelo personalizado.

4. WHEN se adopte `AUTH_USER_MODEL = 'usuarios.Usuario'` en un proyecto con migraciones previas ya aplicadas, THE desarrollador SHALL ejecutar manualmente y previa confirmación explícita el procedimiento de reset de base de datos de desarrollo: (a) eliminar el archivo `db.sqlite3`; (b) eliminar todos los archivos de migración con nombre distinto a `__init__.py` en las apps bajo `/apps/`; (c) ejecutar `manage.py makemigrations` seguido de `manage.py migrate` desde cero. Este paso es irreversible (destruye los datos de desarrollo) y por lo tanto NO SHALL automatizarse silenciosamente: SHALL representarse como una task manual explícita y separada en la fase de Tasks, con un checkpoint de confirmación previo, distinta de las tasks automatizables.

5. THE Sistema SHALL definir el modelo `Cliente` en `apps/usuarios/models.py` con los campos: `usuario` (OneToOneField a `settings.AUTH_USER_MODEL`, `on_delete=CASCADE`, `related_name='perfil_cliente'`), `telefono` (CharField, `max_length=20`, `blank=True`, `null=True`), `preferencias` (TextField, `blank=True`, con `validators=[MaxLengthValidator(2000)]` para limitar a un máximo de 2000 caracteres; la validación del límite ocurre a nivel de `full_clean()` y formularios de Django, no a nivel de base de datos, ya que TextField no impone límite en la columna), `fecha_creacion` (DateTimeField, `auto_now_add=True`), y los metadatos `verbose_name = 'Cliente'`, `verbose_name_plural = 'Clientes'`, `ordering = ['usuario__username']`.

6. THE Sistema SHALL implementar el método `__str__` del modelo `Usuario` retornando `self.get_full_name() or self.username`, de modo que si `get_full_name()` retorna cadena vacía o `None`, se use `username` como valor de retorno.

7. THE Sistema SHALL implementar el método `__str__` del modelo `Cliente` retornando `str(self.usuario)`, delegando la representación al `__str__` del modelo `Usuario` asociado.

8. THE Sistema SHALL registrar el modelo `Usuario` en el Django Admin de la app `usuarios` mediante una clase que herede de `UserAdmin` de `django.contrib.auth.admin`, con `list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']`, `list_filter = ['is_staff', 'is_active', 'is_superuser']` y `search_fields = ['username', 'email', 'first_name', 'last_name']`.

9. THE Sistema SHALL registrar el modelo `Cliente` en el Django Admin de la app `usuarios` mediante una clase que herede de `ModelAdmin`, con `list_display = ['usuario', 'telefono', 'fecha_creacion']`, `list_filter = []` y `search_fields = ['usuario__username', 'usuario__email', 'telefono']`.

10. WHEN se ejecuta `manage.py makemigrations usuarios`, THE Sistema SHALL generar el archivo `apps/usuarios/migrations/0001_initial.py` sin errores ni advertencias en la salida estándar.

11. WHEN se ejecuta `manage.py migrate`, THE Sistema SHALL aplicar todas las migraciones pendientes y crear las tablas `usuarios_usuario` y `usuarios_cliente` en la base de datos, sin errores en la salida estándar, verificable mediante `manage.py inspectdb` que muestre ambas tablas.

12. IF `manage.py migrate` se ejecuta con tablas de `auth` previas existentes en la base de datos sin haber realizado el paso del criterio 4, THEN THE Sistema SHALL retornar un error indicando conflicto de tablas sin modificar el estado de la base de datos.

---

### Requirement 4: App `proveedores` y modelo `ProveedorProfesional`

**User Story:** Como administrador del sistema, quiero registrar proveedores profesionales con modalidad de atención y estado activo, para poder asignarles servicios y construir la base del flujo de reservas sin bloquear la futura gestión de agenda ni la escalabilidad a negocios con múltiples empleados.

#### Acceptance Criteria

1. THE Sistema SHALL crear la app `proveedores` en `/apps/proveedores/` con `AppConfig.name = 'apps.proveedores'` y `AppConfig.label = 'proveedores'`, y registrarla en `INSTALLED_APPS` de `beautyfull/settings/base.py`.

2. THE Sistema SHALL definir en `apps/proveedores/models.py` las opciones de modalidad como una clase de choices `ModalidadChoices` (o equivalente con `TextChoices`) con los valores: `A_DOMICILIO = 'a_domicilio'`, `EN_LOCAL = 'en_local'`, `AMBOS = 'ambos'`.

3. THE Sistema SHALL definir el modelo `ProveedorProfesional` en `apps/proveedores/models.py` con los campos: `nombre_comercial` (CharField, max 150 caracteres, no vacío), `es_negocio` (BooleanField, default `False`), `modalidad` (CharField, max 20 caracteres, choices `ModalidadChoices`, default `ModalidadChoices.A_DOMICILIO`), `ubicacion` (CharField, max 255 caracteres, blank y null permitidos), `biografia` (TextField, max 500 caracteres, blank permitido), `activo` (BooleanField, default `True`), y los metadatos `verbose_name = 'Proveedor Profesional'`, `verbose_name_plural = 'Proveedores Profesionales'`, `ordering = ['nombre_comercial']`.

4. THE Sistema SHALL implementar el método `__str__` del modelo `ProveedorProfesional` retornando el campo `nombre_comercial`.

5. THE Sistema SHALL registrar el modelo `ProveedorProfesional` en el Django Admin de la app `proveedores` con `list_display = ['nombre_comercial', 'es_negocio', 'modalidad', 'activo']`, `list_filter = ['activo', 'modalidad', 'es_negocio']` y `search_fields = ['nombre_comercial', 'biografia']`.

6. WHEN se ejecuta `manage.py makemigrations proveedores`, THE Sistema SHALL generar el archivo de migración `apps/proveedores/migrations/0001_initial.py` con código de salida igual a 0.

7. WHEN se ejecuta `manage.py migrate`, THE Sistema SHALL aplicar la migración `proveedores.0001_initial` (estado aplicado), creando la tabla `proveedores_proveedorprofesional` con todas las columnas definidas en el modelo, y retornar código de salida igual a 0.

8. IF se intenta guardar un `ProveedorProfesional` con `nombre_comercial` vacío o con más de 150 caracteres, THEN THE Sistema SHALL rechazar el guardado con un error de validación que identifique el campo `nombre_comercial` como no válido.

9. IF se intenta guardar un `ProveedorProfesional` con un valor de `modalidad` que no pertenezca a `ModalidadChoices`, THEN THE Sistema SHALL rechazar el guardado con un error de validación indicando que el valor no es una opción válida.

---

### Requirement 5: Integridad del sistema y verificación global

**User Story:** Como desarrollador, quiero que el proyecto Django arranque limpio con las cuatro apps nuevas instaladas y todas sus migraciones aplicadas, para confirmar que el modelo de datos central es coherente y no introduce regresiones en la configuración de Spec 01.

#### Acceptance Criteria

1. WHEN se ejecuta `manage.py check`, THE Sistema SHALL reportar cero issues con las apps `categorias`, `proveedores`, `servicios` y `usuarios` registradas en `INSTALLED_APPS`, retornando código de salida 0.

2. WHEN se ejecuta `manage.py makemigrations --check` para las apps `categorias`, `proveedores`, `servicios` y `usuarios`, THE Sistema SHALL retornar código de salida 0 y no generar ningún archivo de migración nuevo en ninguna de esas apps, confirmando que todos los modelos tienen su migración generada y actualizada.

3. WHEN se ejecuta `manage.py migrate`, THE Sistema SHALL aplicar todas las migraciones de las cuatro apps respetando las dependencias declaradas en el campo `dependencies` de cada archivo de migración: `servicios.0001_initial` deberá declarar dependencia de `categorias.0001_initial` y `proveedores.0001_initial`; `usuarios.0001_initial` no deberá declarar dependencia de ninguna de las otras tres apps.

4. WHEN se ejecuta `manage.py test`, THE Sistema SHALL completar con 0 fallos y 0 errores, y ningún test que pasaba antes de aplicar este spec deberá fallar después de aplicarlo.

5. THE Sistema SHALL garantizar que el modelo `Servicio` puede referirse a `ProveedorProfesional` y `Categoria` usando strings de referencia en los ForeignKey y ManyToManyField (`'proveedores.ProveedorProfesional'`, `'categorias.Categoria'`), de modo que `manage.py check` reporte cero errores de importación cíclica.

6. WHEN se ejecuta `manage.py check` o se inspecciona la configuración del proyecto, THE Sistema SHALL confirmar que `settings.AUTH_USER_MODEL == 'usuarios.Usuario'`, verificando así que el modelo de usuario personalizado está correctamente configurado en `beautyfull/settings/base.py` y que no se usa `auth.User` por defecto. No se requiere lógica de excepción custom.

---

### Requirement 6: Convenciones de código y estructura de archivos

**User Story:** Como equipo de desarrollo, quiero que todas las apps nuevas sigan las convenciones establecidas en los steering files del proyecto, para mantener consistencia y legibilidad en la base de código.

#### Acceptance Criteria

1. THE Sistema SHALL nombrar todas las clases de modelos, AppConfig y clases de Admin en PascalCase (`Categoria`, `Servicio`, `Usuario`, `Cliente`, `ProveedorProfesional`, `CategoriasConfig`, `ServiciosConfig`, `UsuariosConfig`, `ProveedoresConfig`).

2. THE Sistema SHALL nombrar todos los archivos, directorios de apps y campos de modelos en snake_case (`models.py`, `admin.py`, `nombre_comercial`, `precio_base_clp`, `duracion_minutos`).

3. THE Sistema SHALL mantener los modelos libres de lógica de negocio y métodos complejos: solo campos, metadatos Django (`verbose_name`, `ordering`, `Meta`) y relaciones (`ForeignKey`, `ManyToManyField`, `OneToOneField`). Los métodos permitidos en esta spec son: (a) `__str__` en todos los modelos, cuya implementación SHALL retornar una cadena no vacía que identifique la instancia; y (b) exclusivamente en el modelo `Categoria`, un método `save()` sobrescrito (o una señal `pre_save` dedicada) cuyo único propósito SHALL ser la generación automática del `slug` descrita en el Requirement 1, criterio 3. THE Sistema SHALL NOT incluir ninguna otra lógica de negocio en los modelos (cálculos, validaciones cruzadas entre modelos, efectos secundarios, etc.); la generación del slug de `Categoria` es la única excepción permitida en esta spec.

4. THE Sistema SHALL incluir `verbose_name` y `verbose_name_plural` en la clase `Meta` de cada modelo, con valores en español, con tildes correctas, en minúsculas, y sin exceder 50 caracteres por campo.

5. WHEN se crea una app nueva, THE Sistema SHALL incluir un archivo `urls.py` que contenga únicamente la variable `urlpatterns` asignada a una lista vacía, sin incluir ningún `path()` ni importación adicional.

6. THE Sistema SHALL incluir las cuatro apps nuevas en `INSTALLED_APPS` de `beautyfull/settings/base.py` usando la ruta de importación completa: `'apps.categorias'`, `'apps.servicios'`, `'apps.usuarios'`, `'apps.proveedores'`.

**Nota de revisión manual (fuera de los Acceptance Criteria formales):** Durante la revisión de código, el revisor SHALL verificar manualmente que las clases de modelos, AppConfig y Admin usan PascalCase, y que archivos, directorios de apps y campos de modelos usan snake_case. Esta verificación es un checklist humano, no un criterio automatizable.
