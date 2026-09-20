from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.proveedores.models import ModalidadChoices, ProveedorProfesional


class ProveedorProfesionalModelTests(TestCase):
    """Tests unitarios basados en ejemplos para el modelo ProveedorProfesional.

    Cubre Requirements 4.8 y 4.9.
    """

    def test_creacion_valida(self):
        """Un ProveedorProfesional con datos válidos se crea y persiste correctamente."""
        proveedor = ProveedorProfesional.objects.create(
            nombre_comercial='Estudio de Belleza Aurora',
            es_negocio=True,
            modalidad=ModalidadChoices.EN_LOCAL,
            ubicacion='Av. Siempre Viva 123',
            biografia='Salón especializado en tratamientos capilares.',
        )

        self.assertIsNotNone(proveedor.pk)
        self.assertEqual(proveedor.nombre_comercial, 'Estudio de Belleza Aurora')
        self.assertTrue(proveedor.es_negocio)
        self.assertEqual(proveedor.modalidad, ModalidadChoices.EN_LOCAL)
        self.assertTrue(proveedor.activo)

    def test_creacion_valida_con_defaults(self):
        """Los defaults (es_negocio=False, modalidad=A_DOMICILIO, activo=True) se aplican."""
        proveedor = ProveedorProfesional.objects.create(
            nombre_comercial='Manicura a Domicilio',
        )

        self.assertFalse(proveedor.es_negocio)
        self.assertEqual(proveedor.modalidad, ModalidadChoices.A_DOMICILIO)
        self.assertTrue(proveedor.activo)

    def test_str_retorna_nombre_comercial(self):
        """__str__ retorna el nombre_comercial de la instancia."""
        proveedor = ProveedorProfesional.objects.create(
            nombre_comercial='Barbería El Corte',
        )

        self.assertEqual(str(proveedor), 'Barbería El Corte')

    def test_modalidad_fuera_de_choices_rechazada_via_full_clean(self):
        """Una modalidad fuera de ModalidadChoices es rechazada por full_clean() (Req 4.9)."""
        proveedor = ProveedorProfesional(
            nombre_comercial='Proveedor Inválido',
            modalidad='modalidad_inexistente',
        )

        with self.assertRaises(ValidationError) as contexto:
            proveedor.full_clean()

        self.assertIn('modalidad', contexto.exception.message_dict)

    def test_nombre_comercial_vacio_rechazado_via_full_clean(self):
        """Un nombre_comercial vacío es rechazado por full_clean() (Req 4.8)."""
        proveedor = ProveedorProfesional(
            nombre_comercial='',
            modalidad=ModalidadChoices.A_DOMICILIO,
        )

        with self.assertRaises(ValidationError) as contexto:
            proveedor.full_clean()

        self.assertIn('nombre_comercial', contexto.exception.message_dict)

    def test_nombre_comercial_muy_largo_rechazado_via_full_clean(self):
        """Un nombre_comercial de más de 150 caracteres es rechazado por full_clean() (Req 4.8)."""
        proveedor = ProveedorProfesional(
            nombre_comercial='a' * 151,
            modalidad=ModalidadChoices.A_DOMICILIO,
        )

        with self.assertRaises(ValidationError) as contexto:
            proveedor.full_clean()

        self.assertIn('nombre_comercial', contexto.exception.message_dict)
