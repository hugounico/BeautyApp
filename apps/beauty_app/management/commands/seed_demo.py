from decouple import UndefinedValueError, config
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.categorias.models import Categoria
from apps.proveedores.models import ProveedorProfesional
from apps.servicios.models import Servicio
from apps.usuarios.models import Cliente

Usuario = get_user_model()


# ---------------------------------------------------------------------------
# Definición en-Python del dataset de demostración (R4).
#
# Toda la "forma" del dataset vive aquí, de forma declarativa y estable entre
# ejecuciones. Las claves naturales usadas para converger (upsert) son:
#   - Categoria            -> nombre
#   - Servicio             -> (categoria, nombre)
#   - ProveedorProfesional -> nombre_comercial  (el marcador "[DEMO]" es parte
#                             del valor real de nombre_comercial, NO un campo)
#   - Usuario demo         -> username
#
# El marcador `recibe_cuenta_demo=True` existe EXCLUSIVAMENTE en esta estructura
# en-Python; NO es un campo de modelo ni una migración. Indica, de forma
# determinista y estable, cuál de los 3 proveedores recibe la cuenta
# `proveedor_demo`. (R4.4)
# ---------------------------------------------------------------------------

CATEGORIAS = ['Peluquería', 'Manicure', 'Masajes']

PRECIO_DEMO = 20000
DURACION_DEMO = 60  # minutos; válido (>=1) para todos los servicios demo.

# (categoria_nombre, servicio_nombre)
SERVICIOS = [
    ('Peluquería', 'Corte Niño'),
    ('Peluquería', 'Corte Adulto'),
    ('Peluquería', 'Coloración'),
    ('Manicure', 'Manicure Permanente'),
    ('Masajes', 'Masaje Relajante'),
    ('Masajes', 'Masaje Descontracturante'),
]

# Exactamente 3 proveedores demo. El marcador "[DEMO]" es parte real del
# nombre_comercial. Exactamente UNA entrada tiene recibe_cuenta_demo=True.
PROVEEDORES = [
    {'nombre_comercial': 'Studio Aurora [DEMO]', 'recibe_cuenta_demo': True},
    {'nombre_comercial': 'Bella Manos [DEMO]', 'recibe_cuenta_demo': False},
    {'nombre_comercial': 'Relax Zen [DEMO]', 'recibe_cuenta_demo': False},
]

# Cableado M2M determinista: cada servicio recibe >=1 proveedor y al menos un
# servicio recibe >=2 proveedores. No depende del orden de ningún QuerySet.
#   servicio_nombre -> lista de nombre_comercial de proveedores
SERVICIO_PROVEEDORES = {
    'Corte Niño': ['Studio Aurora [DEMO]'],
    'Corte Adulto': ['Studio Aurora [DEMO]', 'Bella Manos [DEMO]'],  # >=2
    'Coloración': ['Studio Aurora [DEMO]'],
    'Manicure Permanente': ['Bella Manos [DEMO]'],
    'Masaje Relajante': ['Relax Zen [DEMO]'],
    'Masaje Descontracturante': ['Relax Zen [DEMO]'],
}

CLIENTE_DEMO_USERNAME = 'cliente_demo'
PROVEEDOR_DEMO_USERNAME = 'proveedor_demo'


class Command(BaseCommand):
    """Management command `seed_demo` (R4).

    Genera/converge un dataset de demostración reproducible e idempotente.

    Fail-before-write (R4.8, R4.9): al inicio de `handle()`, antes de cualquier
    escritura y antes de abrir la transacción, se leen las contraseñas demo
    desde el entorno vía python-decouple SIN fallback. Si falta alguna, se
    aborta con `CommandError` nombrando la variable, dejando la BD intacta.

    Atomicidad (R4.7): todas las escrituras ocurren dentro de un único
    `with transaction.atomic():`; ante cualquier excepción se revierte toda la
    ejecución (rollback total) y la excepción se propaga.

    Convergencia (R4.5, R4.6): upsert por claves naturales; administra sólo sus
    propias claves; nunca borra registros ajenos; converge sólo los campos que
    el dataset define.
    """

    help = 'Genera/converge datos de demostración reproducibles (R4).'

    def handle(self, *args, **options):
        # -------------------------------------------------------------------
        # 5.2 — Fail-before-write: leer credenciales desde entorno SIN fallback,
        # ANTES de cualquier escritura y ANTES de abrir la transacción. (R4.8/R4.9)
        # -------------------------------------------------------------------
        cliente_password = self._leer_password_requerida('DEMO_CLIENTE_PASSWORD')
        proveedor_password = self._leer_password_requerida('DEMO_PROVEEDOR_PASSWORD')

        # Contadores de resumen (R4.11).
        creados = {'categorias': 0, 'servicios': 0, 'proveedores': 0, 'usuarios': 0}
        actualizados = {'categorias': 0, 'servicios': 0, 'proveedores': 0, 'usuarios': 0}

        # -------------------------------------------------------------------
        # 5.5 — Toda la escritura dentro de una única transacción atómica. (R4.7)
        # -------------------------------------------------------------------
        with transaction.atomic():
            # --- Categorías (upsert por nombre) ---
            categorias_por_nombre = {}
            for nombre in CATEGORIAS:
                categoria, created = Categoria.objects.get_or_create(nombre=nombre)
                categorias_por_nombre[nombre] = categoria
                self._contar(creados, actualizados, 'categorias', created)

            # --- Servicios (upsert por (categoria, nombre)) ---
            servicios_por_nombre = {}
            for categoria_nombre, servicio_nombre in SERVICIOS:
                categoria = categorias_por_nombre[categoria_nombre]
                servicio, created = Servicio.objects.update_or_create(
                    categoria=categoria,
                    nombre=servicio_nombre,
                    defaults={
                        'precio_base_clp': PRECIO_DEMO,
                        'duracion_minutos': DURACION_DEMO,
                    },
                )
                servicios_por_nombre[servicio_nombre] = servicio
                self._contar(creados, actualizados, 'servicios', created)

            # --- Proveedores (upsert por nombre_comercial) ---
            proveedores_por_nombre = {}
            proveedor_marcado = None
            for entrada in PROVEEDORES:
                nombre_comercial = entrada['nombre_comercial']
                proveedor, created = ProveedorProfesional.objects.get_or_create(
                    nombre_comercial=nombre_comercial,
                )
                proveedores_por_nombre[nombre_comercial] = proveedor
                self._contar(creados, actualizados, 'proveedores', created)
                if entrada['recibe_cuenta_demo']:
                    proveedor_marcado = proveedor

            # --- Cableado M2M Servicio.proveedores (converge el set) ---
            for servicio_nombre, nombres_prov in SERVICIO_PROVEEDORES.items():
                servicio = servicios_por_nombre[servicio_nombre]
                proveedores = [proveedores_por_nombre[n] for n in nombres_prov]
                servicio.proveedores.set(proveedores)

            # --- Usuario cliente_demo + Cliente asociado ---
            cliente_user, created = Usuario.objects.get_or_create(
                username=CLIENTE_DEMO_USERNAME,
            )
            cliente_user.set_password(cliente_password)
            cliente_user.save()
            self._contar(creados, actualizados, 'usuarios', created)
            Cliente.objects.get_or_create(usuario=cliente_user)

            # --- Usuario proveedor_demo vinculado al proveedor marcado (R4.4) ---
            proveedor_user, created = Usuario.objects.get_or_create(
                username=PROVEEDOR_DEMO_USERNAME,
            )
            proveedor_user.set_password(proveedor_password)
            proveedor_user.save()
            self._contar(creados, actualizados, 'usuarios', created)
            # Vincular por el OneToOneField de R1 (perfil_proveedor) al
            # proveedor marcado con recibe_cuenta_demo=True.
            if proveedor_marcado.usuario_id != proveedor_user.pk:
                proveedor_marcado.usuario = proveedor_user
                proveedor_marcado.save()

        # -------------------------------------------------------------------
        # 5.5 — Resumen en español (sin secretos ni hashes). (R4.11)
        # -------------------------------------------------------------------
        self.stdout.write('Resumen de seed_demo:')
        for clave in ('categorias', 'servicios', 'proveedores', 'usuarios'):
            self.stdout.write(
                f'  {clave}: creados={creados[clave]}, '
                f'actualizados={actualizados[clave]}'
            )
        self.stdout.write(
            self.style.SUCCESS('seed_demo completado correctamente.')
        )

    def _leer_password_requerida(self, nombre_variable):
        """Lee una variable de contraseña obligatoria desde el entorno.

        Sin fallback: si la variable no está definida, python-decouple lanza
        `UndefinedValueError`; se traduce a `CommandError` nombrando la
        variable ausente, antes de cualquier escritura. (R4.8, R4.9)
        """
        try:
            return config(nombre_variable)
        except UndefinedValueError:
            raise CommandError(
                f'Falta la variable de entorno requerida: {nombre_variable}. '
                'Defínela antes de ejecutar seed_demo. No se escribió nada en '
                'la base de datos.'
            )

    @staticmethod
    def _contar(creados, actualizados, clave, created):
        if created:
            creados[clave] += 1
        else:
            actualizados[clave] += 1
