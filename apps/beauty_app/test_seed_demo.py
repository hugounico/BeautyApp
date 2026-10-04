"""Tests del management command `seed_demo` (R4).

Marco: django.test.TestCase; el comando se invoca vía
`django.core.management.call_command`. Las contraseñas demo se proveen por
`os.environ` (python-decouple las lee desde el entorno cuando no hay archivo
`.env`), usando `unittest.mock.patch.dict`.

No se usan property-based tests (R6 Nota).
"""

import os
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.beauty_app.management.commands import seed_demo as seed_demo_mod
from apps.categorias.models import Categoria
from apps.proveedores.models import ProveedorProfesional
from apps.servicios.models import Servicio
from apps.usuarios.models import Cliente

Usuario = get_user_model()

CLIENTE_PWD = 'Demo-Cliente-2024!'
PROVEEDOR_PWD = 'Demo-Proveedor-2024!'

ENV_OK = {
    'DEMO_CLIENTE_PASSWORD': CLIENTE_PWD,
    'DEMO_PROVEEDOR_PASSWORD': PROVEEDOR_PWD,
}


def _run_seed(env=None):
    """Ejecuta seed_demo con un entorno controlado y devuelve el stdout."""
    env = ENV_OK if env is None else env
    out = StringIO()
    # clear=False: preserva el resto del entorno; sobreescribe/añade sólo las
    # claves provistas. Para los casos de "variable ausente" el llamador debe
    # eliminar la clave explícitamente.
    with mock.patch.dict(os.environ, env, clear=False):
        call_command('seed_demo', stdout=out)
    return out.getvalue()


def _marcado_nombre_comercial():
    """nombre_comercial del único proveedor con recibe_cuenta_demo=True."""
    marcados = [p for p in seed_demo_mod.PROVEEDORES if p['recibe_cuenta_demo']]
    assert len(marcados) == 1, 'Debe haber exactamente un proveedor marcado'
    return marcados[0]['nombre_comercial']


class SeedDemoDatasetTests(TestCase):
    """A — Dataset exacto; B — Relaciones; C — Credenciales."""

    def setUp(self):
        for clave in ('DEMO_CLIENTE_PASSWORD', 'DEMO_PROVEEDOR_PASSWORD'):
            os.environ.pop(clave, None)

    def test_dataset_exacto(self):
        # A — 3 categorías, 6 servicios (precio=20000), 3 proveedores,
        #     cliente_demo y proveedor_demo existen.
        _run_seed()

        self.assertEqual(Categoria.objects.count(), 3)
        self.assertEqual(Servicio.objects.count(), 6)
        self.assertTrue(
            all(s.precio_base_clp == 20000 for s in Servicio.objects.all())
        )
        self.assertEqual(ProveedorProfesional.objects.count(), 3)
        self.assertTrue(Usuario.objects.filter(username='cliente_demo').exists())
        self.assertTrue(Usuario.objects.filter(username='proveedor_demo').exists())

    def test_relaciones(self):
        # B — relaciones del dataset.
        _run_seed()

        # cliente_demo tiene Cliente asociado.
        cliente_user = Usuario.objects.get(username='cliente_demo')
        self.assertTrue(Cliente.objects.filter(usuario=cliente_user).exists())

        # proveedor_demo vinculado EXACTAMENTE al proveedor marcado.
        proveedor_user = Usuario.objects.get(username='proveedor_demo')
        proveedor = ProveedorProfesional.objects.get(usuario=proveedor_user)
        self.assertEqual(proveedor.nombre_comercial, _marcado_nombre_comercial())
        # Exactamente un proveedor con usuario vinculado.
        self.assertEqual(
            ProveedorProfesional.objects.filter(usuario__isnull=False).count(), 1
        )

        # Cada uno de los 6 servicios tiene >=1 proveedor.
        for servicio in Servicio.objects.all():
            self.assertGreaterEqual(servicio.proveedores.count(), 1)
        # Al menos un servicio con >=2 proveedores.
        self.assertTrue(
            any(s.proveedores.count() >= 2 for s in Servicio.objects.all())
        )

    def test_credenciales_check_password(self):
        # C — contraseñas verificadas vía check_password (no comparar hashes).
        _run_seed()

        cliente_user = Usuario.objects.get(username='cliente_demo')
        proveedor_user = Usuario.objects.get(username='proveedor_demo')
        self.assertTrue(cliente_user.check_password(CLIENTE_PWD))
        self.assertTrue(proveedor_user.check_password(PROVEEDOR_PWD))


class SeedDemoIdempotencyTests(TestCase):
    """D — Idempotencia; E — No-destrucción de datos ajenos."""

    def setUp(self):
        for clave in ('DEMO_CLIENTE_PASSWORD', 'DEMO_PROVEEDOR_PASSWORD'):
            os.environ.pop(clave, None)

    @staticmethod
    def _estado_logico():
        """Captura el estado lógico administrado por el dataset."""
        servicios = {
            s.nombre: {
                'precio': s.precio_base_clp,
                'proveedores': sorted(
                    p.nombre_comercial for p in s.proveedores.all()
                ),
            }
            for s in Servicio.objects.all()
        }
        proveedor_user = Usuario.objects.get(username='proveedor_demo')
        vinculado = ProveedorProfesional.objects.get(
            usuario=proveedor_user
        ).nombre_comercial
        return {
            'categorias': Categoria.objects.count(),
            'servicios': Servicio.objects.count(),
            'proveedores': ProveedorProfesional.objects.count(),
            'usuarios_demo': Usuario.objects.filter(
                username__in=['cliente_demo', 'proveedor_demo']
            ).count(),
            'servicios_detalle': servicios,
            'proveedor_vinculado': vinculado,
        }

    def test_idempotencia(self):
        # D — segunda ejecución no duplica y converge al mismo estado lógico.
        _run_seed()
        estado_1 = self._estado_logico()
        _run_seed()
        estado_2 = self._estado_logico()

        self.assertEqual(estado_1, estado_2)
        # Conteos absolutos: sin duplicados.
        self.assertEqual(Categoria.objects.count(), 3)
        self.assertEqual(Servicio.objects.count(), 6)
        self.assertEqual(ProveedorProfesional.objects.count(), 3)
        self.assertEqual(
            Usuario.objects.filter(
                username__in=['cliente_demo', 'proveedor_demo']
            ).count(),
            2,
        )

    def test_no_destruccion_de_registros_ajenos(self):
        # E — datos ajenos (no del dataset) permanecen intactos tras re-seed.
        _run_seed()

        categoria_ajena = Categoria.objects.create(nombre='Categoría Ajena')
        servicio_ajeno = Servicio.objects.create(
            nombre='Servicio Ajeno',
            categoria=categoria_ajena,
            duracion_minutos=45,
            precio_base_clp=99999,
        )
        usuario_ajeno = Usuario.objects.create(username='usuario_ajeno')

        _run_seed()

        self.assertTrue(Categoria.objects.filter(pk=categoria_ajena.pk).exists())
        servicio_ajeno.refresh_from_db()
        self.assertEqual(servicio_ajeno.precio_base_clp, 99999)
        self.assertTrue(Usuario.objects.filter(pk=usuario_ajeno.pk).exists())


class SeedDemoFailBeforeWriteTests(TestCase):
    """F — Fail-before-write: variable(s) de contraseña ausente(s)."""

    def setUp(self):
        for clave in ('DEMO_CLIENTE_PASSWORD', 'DEMO_PROVEEDOR_PASSWORD'):
            os.environ.pop(clave, None)

    def _assert_sin_escrituras(self):
        self.assertEqual(Categoria.objects.count(), 0)
        self.assertEqual(Servicio.objects.count(), 0)
        self.assertEqual(ProveedorProfesional.objects.count(), 0)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_falta_cliente_password(self):
        env = {'DEMO_PROVEEDOR_PASSWORD': PROVEEDOR_PWD}
        with mock.patch.dict(os.environ, env, clear=False):
            os.environ.pop('DEMO_CLIENTE_PASSWORD', None)
            with self.assertRaises(CommandError) as ctx:
                call_command('seed_demo')
        self.assertIn('DEMO_CLIENTE_PASSWORD', str(ctx.exception))
        self._assert_sin_escrituras()

    def test_falta_proveedor_password(self):
        env = {'DEMO_CLIENTE_PASSWORD': CLIENTE_PWD}
        with mock.patch.dict(os.environ, env, clear=False):
            os.environ.pop('DEMO_PROVEEDOR_PASSWORD', None)
            with self.assertRaises(CommandError) as ctx:
                call_command('seed_demo')
        self.assertIn('DEMO_PROVEEDOR_PASSWORD', str(ctx.exception))
        self._assert_sin_escrituras()

    def test_faltan_ambas_passwords(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('DEMO_CLIENTE_PASSWORD', None)
            os.environ.pop('DEMO_PROVEEDOR_PASSWORD', None)
            with self.assertRaises(CommandError) as ctx:
                call_command('seed_demo')
        # La primera variable leída es DEMO_CLIENTE_PASSWORD → se nombra esa.
        self.assertIn('DEMO_CLIENTE_PASSWORD', str(ctx.exception))
        self._assert_sin_escrituras()


class SeedDemoRollbackTests(TestCase):
    """G — Rollback total ante fallo luego de iniciar escrituras."""

    def setUp(self):
        for clave in ('DEMO_CLIENTE_PASSWORD', 'DEMO_PROVEEDOR_PASSWORD'):
            os.environ.pop(clave, None)

    def test_rollback_total_ante_fallo_tardio(self):
        # Forzar un fallo en un paso TARDÍO (cableado del M2M) después de que ya
        # se crearon categorías/servicios/proveedores dentro de la transacción.
        # Se parchea el descriptor M2M a nivel de clase para que el método
        # `set` del manager lance una excepción al cablear Servicio.proveedores.
        from django.db.models.fields.related_descriptors import (
            ManyToManyDescriptor,
        )

        def _boom(*args, **kwargs):
            raise RuntimeError('fallo inducido en cableado M2M')

        real_get = ManyToManyDescriptor.__get__

        def fake_get(descriptor, instance, cls=None):
            manager = real_get(descriptor, instance, cls)
            if manager is not None and hasattr(manager, 'set'):
                manager.set = _boom
            return manager

        with mock.patch.dict(os.environ, ENV_OK, clear=False), mock.patch.object(
            ManyToManyDescriptor, '__get__', fake_get
        ):
            with self.assertRaises(RuntimeError):
                call_command('seed_demo')

        # Rollback total: nada persistió de esa ejecución.
        self.assertEqual(Categoria.objects.count(), 0)
        self.assertEqual(Servicio.objects.count(), 0)
        self.assertEqual(ProveedorProfesional.objects.count(), 0)
        self.assertEqual(Usuario.objects.count(), 0)
