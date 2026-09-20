from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

from apps.categorias.models import Categoria
from apps.proveedores.models import ProveedorProfesional

from .models import Servicio


class ServicioModelTests(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre='Peluquería')

    def test_creacion_valida_con_categoria(self):
        servicio = Servicio.objects.create(
            nombre='Corte de cabello',
            duracion_minutos=30,
            precio_base_clp=10000,
            categoria=self.categoria,
        )

        self.assertEqual(servicio.categoria, self.categoria)
        self.assertEqual(servicio.duracion_minutos, 30)
        self.assertEqual(servicio.precio_base_clp, 10000)
        self.assertTrue(servicio.activo)

    def test_str_retorna_nombre(self):
        servicio = Servicio.objects.create(
            nombre='Manicure',
            duracion_minutos=45,
            precio_base_clp=8000,
            categoria=self.categoria,
        )

        self.assertEqual(str(servicio), 'Manicure')

    def test_duracion_minutos_cero_rechazada_via_full_clean(self):
        servicio = Servicio(
            nombre='Servicio inválido',
            duracion_minutos=0,
            precio_base_clp=5000,
            categoria=self.categoria,
        )

        with self.assertRaises(ValidationError) as ctx:
            servicio.full_clean()
        self.assertIn('duracion_minutos', ctx.exception.error_dict)

    def test_precio_base_clp_cero_rechazado_via_full_clean(self):
        servicio = Servicio(
            nombre='Servicio inválido',
            duracion_minutos=30,
            precio_base_clp=0,
            categoria=self.categoria,
        )

        with self.assertRaises(ValidationError) as ctx:
            servicio.full_clean()
        self.assertIn('precio_base_clp', ctx.exception.error_dict)

    def test_eliminar_categoria_con_servicios_lanza_protected_error(self):
        Servicio.objects.create(
            nombre='Corte de cabello',
            duracion_minutos=30,
            precio_base_clp=10000,
            categoria=self.categoria,
        )

        with self.assertRaises(ProtectedError):
            self.categoria.delete()

    def test_asociacion_m2m_con_proveedores(self):
        servicio = Servicio.objects.create(
            nombre='Corte de cabello',
            duracion_minutos=30,
            precio_base_clp=10000,
            categoria=self.categoria,
        )
        proveedor_1 = ProveedorProfesional.objects.create(
            nombre_comercial='Estilista A'
        )
        proveedor_2 = ProveedorProfesional.objects.create(
            nombre_comercial='Estilista B'
        )

        servicio.proveedores.add(proveedor_1, proveedor_2)

        self.assertEqual(servicio.proveedores.count(), 2)
        self.assertIn(servicio, proveedor_1.servicios.all())
        self.assertIn(servicio, proveedor_2.servicios.all())
