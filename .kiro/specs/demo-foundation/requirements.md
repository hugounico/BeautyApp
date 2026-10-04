# Requirements Document

## Introduction

Esta spec entrega la **fundación** que necesitan las specs futuras `catalog-ui` y `booking-flow`, sin anticipar su alcance. Cubre cinco piezas base sobre el proyecto BeautyFull (marketplace Django de servicios de belleza): identidad de proveedor, autenticación nativa, registro público de clientes, datos de demostración reproducibles y un shell visual base. Un sexto requerimiento asegura calidad y ausencia de regresión.

Todo el trabajo se rige por los Steering del workspace (`naming-conventions`, `frontend-conventions`, `architecture`, `execution-conventions`), que se **referencian** desde aquí y no se repiten. La baseline de modelos, settings, admin y templates ya fue verificada contra el código fuente y no debe contradecirse.

El alcance NO incluye (se dejan explícitamente para specs posteriores): catálogo/búsqueda, reservas y sus estados, disponibilidad, pagos/comisión, precio por proveedor u `OfertaProveedor`, mapas/GPS, reseñas, chat, notificaciones, wallet, APIs públicas, frameworks JS, CI/CD, AWS y PostgreSQL.

## Glossary

- **BeautyFull**: proyecto Django (paquete raíz `beautyfull`), marketplace de servicios de belleza.
- **Usuario**: modelo de usuario personalizado `usuarios.Usuario(AbstractUser)`, identificador de login `username`, configurado en `AUTH_USER_MODEL`.
- **Cliente**: modelo `usuarios.Cliente`, ligado a `Usuario` por `OneToOneField` requerido (`on_delete=CASCADE`, `related_name='perfil_cliente'`).
- **ProveedorProfesional**: modelo `proveedores.ProveedorProfesional`; hoy sin relación con `Usuario`.
- **Servicio**: modelo `servicios.Servicio`, ligado a proveedores por `ManyToManyField` existente (`related_name='servicios'`).
- **Categoria**: modelo `categorias.Categoria` (`nombre` único, `slug` auto, `activo`).
- **Sistema**: la aplicación BeautyFull en ejecución (vistas, modelos, comandos, admin).
- **Registro_Cliente**: flujo público de alta de un `Usuario` + `Cliente`.
- **Seed_Demo**: management command que genera/converge datos de demostración.
- **Destino_Por_Defecto**: ruta interna estable a la que el Sistema redirige tras login/logout cuando no hay un destino seguro solicitado.
- **Shell_Visual**: `base.html` evolucionado más el Home mínimo, navbar responsive y bloque de mensajes.

## Requirements

### Requirement 1: Identidad de Proveedor

**User Story:** Como administrador del marketplace, quiero poder asociar opcionalmente un `Usuario` a un `ProveedorProfesional`, para que un proveedor pueda iniciar sesión sin obligar a que todo proveedor tenga cuenta.

#### Acceptance Criteria

1. THE Sistema SHALL definir en `ProveedorProfesional` un `OneToOneField` hacia `AUTH_USER_MODEL` con `null=True`, `blank=True`, `on_delete=CASCADE` y un `related_name` propio cuyo valor sea distinto de `perfil_cliente`.
2. THE Sistema SHALL permitir crear y guardar un `ProveedorProfesional` sin `Usuario` asociado, quedando el campo con valor nulo sin generar error de validación.
3. IF se intenta asociar a un `ProveedorProfesional` un `Usuario` que ya está vinculado a otro `ProveedorProfesional`, THEN THE Sistema SHALL rechazar el guardado mediante un error de validación por unicidad del `OneToOneField`, conservando sin cambios el vínculo previo existente.
4. WHEN el `Usuario` asociado a un `ProveedorProfesional` es eliminado, THE Sistema SHALL eliminar en la misma operación el `ProveedorProfesional` asociado por `on_delete=CASCADE`, replicando el comportamiento del vínculo de `Cliente`.
5. THE `ProveedorProfesionalAdmin` SHALL exponer el campo `Usuario` como editable de modo que el administrador pueda asociarlo seleccionando un `Usuario` y desasociarlo dejando la selección vacía, persistiendo el valor nulo tras guardar.
6. WHEN se aplica la migración que introduce el vínculo, THE Sistema SHALL conservar todas las filas de `ProveedorProfesional` existentes con el campo `Usuario` en valor nulo, sin pérdida de datos y sin requerir un valor de relleno.
7. THE Sistema SHALL documentar como diferencia justificada frente a `Cliente` que el vínculo de proveedor es opcional (`null/blank`) mientras el de `Cliente` es requerido, conservando ambos `on_delete=CASCADE`.
8. THE Sistema SHALL abstenerse de introducir exclusión mutua entre `Cliente` y `ProveedorProfesional` y de crear un sistema de roles.

### Requirement 2: Autenticación nativa

**User Story:** Como persona usuaria registrada, quiero iniciar y cerrar sesión de forma segura, para acceder a las funciones que dependen de mi identidad.

#### Acceptance Criteria

1. WHEN se envían credenciales válidas en el formulario de login, THE Sistema SHALL autenticar al `Usuario` e iniciar su sesión.
2. IF las credenciales enviadas en el login son inválidas, THEN THE Sistema SHALL rechazar la autenticación, no iniciar sesión y mostrar en la página de login un mensaje de error visible redactado en español que indique que las credenciales son incorrectas.
3. IF la autenticación de login falla por credenciales inválidas, THEN THE Sistema SHALL preservar el estado de sesión previo de la persona usuaria sin crear ni modificar una sesión autenticada.
4. THE Sistema SHALL cerrar la sesión únicamente mediante una solicitud POST que incluya un token CSRF válido.
5. IF se solicita el cierre de sesión mediante una solicitud GET, THEN THE Sistema SHALL mantener la sesión activa sin cerrarla y sin modificar su estado.
6. THE control de logout de la interfaz SHALL implementarse como un formulario que envía una solicitud POST con token CSRF.
7. WHEN el login es exitoso y se recibió un parámetro `next` cuyo valor es una ruta relativa interna del propio sitio BeautyFull (sin esquema, sin host y sin apuntar a un dominio externo), THE Sistema SHALL redirigir a ese destino.
8. IF tras un login exitoso el parámetro `next` está ausente, vacío, o su valor no es una ruta relativa interna del propio sitio (incluye esquema, host, o apunta a un destino externo), THEN THE Sistema SHALL redirigir al Destino_Por_Defecto.
9. WHEN el cierre de sesión se completa mediante POST con token CSRF válido, THE Sistema SHALL redirigir al Destino_Por_Defecto, entendido como una ruta interna determinista configurada en el proyecto BeautyFull.
10. WHILE un `Usuario` ya está autenticado, IF solicita la vista de login o la vista de registro, THEN THE Sistema SHALL redirigir al Destino_Por_Defecto sin volver a mostrar dichos formularios.
11. THE plantilla de login SHALL extender `base.html`.

### Requirement 3: Registro público de clientes

**User Story:** Como visitante, quiero registrarme como cliente, para reservar servicios en el futuro.

#### Acceptance Criteria

1. THE Registro_Cliente SHALL crear únicamente cuentas de tipo cliente, compuestas por un registro `Usuario` y su registro `Cliente` asociado mediante la relación OneToOne (related_name `perfil_cliente`).
2. THE Registro_Cliente SHALL solicitar como campos obligatorios el `username` y la contraseña del `Usuario`, más la confirmación de contraseña, y como campos opcionales `telefono` y `preferencias` del `Cliente`.
3. WHEN el visitante envía el formulario de registro con las dos contraseñas iguales, THE Sistema SHALL validar la contraseña con los validadores de contraseña activos de Django configurados en el proyecto antes de crear cualquier registro.
4. IF la contraseña y su confirmación no coinciden, THEN THE Sistema SHALL rechazar el envío mostrando un mensaje de error en español que indique que las contraseñas no coinciden, sin crear ningún registro.
5. THE Registro_Cliente SHALL crear el `Usuario` con `is_staff=False`, `is_superuser=False` y sin permisos ni grupos asignados, y SHALL no crear ningún `ProveedorProfesional`.
6. WHEN el registro es válido, THE Sistema SHALL crear el `Usuario` y el `Cliente` de forma atómica dentro de una única transacción, estableciendo el campo `fecha_creacion` del `Cliente` de forma automática.
7. IF falla la creación del `Usuario` o del `Cliente` durante la transacción, THEN THE Sistema SHALL revertir la transacción completa, no dejar ningún `Usuario` huérfano ni ningún `Cliente` sin `Usuario`, y mostrar un mensaje de error en español.
8. WHEN el registro se completa con éxito, THE Sistema SHALL iniciar la sesión del `Usuario` automáticamente, redirigir al Destino_Por_Defecto y mostrar un mensaje de bienvenida en español.
9. IF los datos son inválidos o el `username` enviado ya existe en `Usuario`, THEN THE Sistema SHALL rechazar el envío mostrando errores en español que indiquen el motivo del rechazo, sin crear ningún registro.
10. THE plantilla de registro SHALL extender `base.html`.

### Requirement 4: Comando seed_demo

**User Story:** Como desarrollador, quiero un comando que genere datos de demostración reproducibles, para levantar un entorno consistente que consuman `catalog-ui` y `booking-flow`.

#### Acceptance Criteria

1. THE Seed_Demo SHALL crear exactamente 3 categorías de demostración —Peluquería, Manicure y Masajes— y exactamente 6 servicios de demostración, todos con `precio_base_clp` igual a 20000, distribuidos así: Peluquería con Corte Niño, Corte Adulto y Coloración; Manicure con Manicure Permanente; Masajes con Masaje Relajante y Masaje Descontracturante.
2. THE Seed_Demo SHALL crear exactamente 3 proveedores de demostración con datos ficticios cuyo nombre incluya un marcador estable que los identifique como demo.
3. THE Seed_Demo SHALL relacionar proveedores y servicios usando el `ManyToManyField` existente (`Servicio.proveedores`), de modo que cada uno de los 6 servicios tenga al menos 1 proveedor asociado y al menos 1 servicio tenga al menos 2 proveedores asociados.
4. THE Seed_Demo SHALL crear un `Usuario` `cliente_demo` con su `Cliente` asociado y un `Usuario` `proveedor_demo` asociado a exactamente uno de los 3 proveedores de demostración mediante el `OneToOneField` de R1, seleccionando como su proveedor asociado a exactamente uno de los 3 proveedores de demostración, mediante un criterio determinista y estable entre ejecuciones (el criterio concreto de selección se definirá en Design).
5. THE Seed_Demo SHALL identificar cada registro de demostración mediante claves naturales estables (para categorías, el campo único `Categoria.nombre`), de modo que dos ejecuciones distintas resuelvan el mismo registro.
6. WHEN el comando se ejecuta una segunda vez o más veces, THE Seed_Demo SHALL converger cada registro de demostración al estado aquí definido —incluyendo `precio_base_clp` igual a 20000 y la contraseña vigente en las variables de entorno— sin crear registros duplicados y sin crear ni modificar registros que no sean de demostración.
7. THE Seed_Demo SHALL ejecutar todas sus operaciones de escritura dentro de una única transacción atómica, de modo que ante un fallo en cualquier punto no persista ningún registro de la ejecución (rollback total).
8. THE Seed_Demo SHALL obtener las contraseñas de `cliente_demo` y `proveedor_demo` exclusivamente desde variables de entorno mediante el mecanismo `python-decouple` del proyecto, sin valor por defecto (fallback) y sin contraseñas escritas en el repositorio.
9. IF al iniciar la ejecución falta alguna de las variables de entorno de contraseña requeridas, THEN THE Seed_Demo SHALL terminar con error antes de ejecutar cualquier operación de escritura, indicando en el mensaje de error el nombre de la variable ausente y preservando la base de datos sin cambios.
10. THE Sistema SHALL documentar en `.env.example` los nombres de las variables de contraseña de demo de `cliente_demo` y `proveedor_demo`, sin incluir sus valores.
11. WHEN el comando finaliza con éxito, THE Seed_Demo SHALL imprimir un resumen que indique la cantidad de registros creados y la cantidad de registros actualizados.

### Requirement 5: Shell visual base

**User Story:** Como visitante, quiero una navegación base coherente y responsive, para orientarme en BeautyFull según mi estado de sesión.

#### Acceptance Criteria

1. THE Shell_Visual SHALL evolucionar `base.html` incorporando una navbar responsive mobile-first, con todo el CSS en archivos dentro de `/static/css/` y todo el JS en archivos dentro de `/static/js/`, sin estilos inline (`style=""`) ni etiquetas `<script>` inline en el HTML, conforme al Steering `frontend-conventions`, sin frameworks externos ni CDN salvo los que el Steering ya establezca.
2. THE Shell_Visual SHALL renderizar la navbar mediante renderizado server-side (Django Templates), preservando los bloques existentes de `base.html` (`title`, `extra_css`, `content`, `extra_js`) y la carga de `static css/main.css` y `js/main.js`, con el atributo de idioma `lang="es"`.
3. WHEN el sistema procesa una petición que renderiza una página que extiende `base.html`, THE Shell_Visual SHALL incluir un bloque que muestre todos los mensajes activos del framework de mensajes de Django presentes en la petición, y no mostrar ningún elemento de mensaje cuando no existan mensajes activos.
4. THE Sistema SHALL exponer una página Home accesible mediante la ruta con nombre `home`, sin contenido de catálogo (sin listados de servicios, categorías ni proveedores).
5. THE Sistema SHALL definir las rutas con nombre estables `home`, `login`, `logout` y `registro`, cada una resoluble por su nombre.
6. WHILE la persona visitante no está autenticada, THE navbar SHALL mostrar exactamente los accesos Ingresar (enlace a la ruta `login`) y Registrarse (enlace a la ruta `registro`), y no mostrar ningún control de logout ni estado de sesión.
7. WHILE el `Usuario` autenticado tiene un `ProveedorProfesional` asociado, THE navbar SHALL mostrar el estado de proveedor y el control de logout mediante formulario que envía POST con token CSRF hacia la ruta `logout`, y no mostrar los accesos Ingresar ni Registrarse.
8. WHILE el `Usuario` autenticado no tiene `ProveedorProfesional` pero sí un `Cliente` asociado, THE navbar SHALL mostrar el estado de cliente y el control de logout mediante formulario que envía POST con token CSRF hacia la ruta `logout`, y no mostrar los accesos Ingresar ni Registrarse.
9. WHILE el `Usuario` autenticado no tiene ni `ProveedorProfesional` ni `Cliente` asociado (por ejemplo, superusuario), THE navbar SHALL mostrar un estado autenticado neutro y el control de logout mediante formulario que envía POST con token CSRF hacia la ruta `logout`, y no mostrar los accesos Ingresar ni Registrarse.
10. THE Shell_Visual SHALL determinar el estado de la navbar aplicando en orden de prioridad las condiciones anónimo → proveedor → cliente → autenticado neutro, seleccionando exactamente uno de los cuatro estados por petición, sin introducir un sistema de roles nuevo.

### Requirement 6: Calidad y regresión

**User Story:** Como responsable del proyecto, quiero garantías de calidad y ausencia de regresión, para integrar la fundación con confianza.

#### Acceptance Criteria

1. WHEN se ejecuta la suite completa de tests, THE Sistema SHALL mantener en verde los 31 tests existentes, con 0 fallos y 0 errores, salvo cambio justificado y trazable a un requerimiento identificado de esta spec.
2. WHEN se ejecuta `manage.py check`, THE Sistema SHALL finalizar con código de salida 0 y sin reportar errores ni advertencias del sistema de checks.
3. WHEN se ejecuta `makemigrations --check`, THE Sistema SHALL finalizar con código de salida 0 e indicar que no existen migraciones pendientes por generar.
4. THE Sistema SHALL incluir al menos un test por cada criterio de aceptación verificable (comportamiento observable mediante assert) de R1 a R5, excluyendo los criterios declarativos o documentales que no describen un comportamiento verificable del Sistema (p. ej. R1.7). Un mismo test puede cubrir varios criterios relacionados cuando eso resulte en una suite más simple, siempre que la trazabilidad completa quede preservada. Casos mínimos cubiertos: proveedor sin `Usuario`, unicidad del `OneToOneField`, rollback de registro, login válido e inválido, logout válido, rechazo de logout mediante método GET, `next` seguro frente a destino externo, idempotencia de `seed_demo`, credenciales de demo ausentes, y estados de la navbar.
5. WHEN se ejecuta el escenario integral en la secuencia `seed_demo` → registro → logout → login, THE Sistema SHALL verificar en cada paso que la navbar refleja el estado de autenticación correspondiente (autenticado tras registro y tras login; no autenticado tras logout).
6. WHEN falla cualquiera de los criterios de verificación (tests existentes, `manage.py check`, `makemigrations --check`, tests nuevos o escenario integral), THE Sistema SHALL considerar la fundación como no integrable y preservar el estado del código sin marcarlo como aprobado.

> Nota: esta Spec no requiere property-based tests.
