from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.categorias.models import Categoria


class CategoriaModelTest(TestCase):
    """Tests unitarios basados en ejemplos para el modelo Categoria.

    Cubre: creación válida, __str__, generación automática de slug,
    colisión de slug con sufijo incremental, unicidad de nombre/slug vía
    IntegrityError, y campo requerido / max_length vía full_clean().

    Requirements: 1.3, 1.4
    """

    def test_creacion_valida(self):
        categoria = Categoria.objects.create(nombre='Peluquería')

        self.assertEqual(categoria.nombre, 'Peluquería')
        self.assertTrue(categoria.activo)
        self.assertTrue(categoria.slug)
        self.assertIsNotNone(categoria.pk)

    def test_str_retorna_nombre(self):
        categoria = Categoria(nombre='Manicure')

        self.assertEqual(str(categoria), 'Manicure')

    def test_generacion_automatica_de_slug(self):
        categoria = Categoria.objects.create(nombre='Uñas Acrílicas')

        self.assertEqual(categoria.slug, 'unas-acrilicas')

    def test_slug_no_se_regenera_si_fue_asignado_manualmente(self):
        categoria = Categoria.objects.create(nombre='Depilación', slug='slug-manual')

        self.assertEqual(categoria.slug, 'slug-manual')

    def test_colision_de_slug_produce_sufijo_incremental(self):
        primera = Categoria.objects.create(nombre='Masajes')
        segunda = Categoria.objects.create(nombre='Masajes ')
        tercera = Categoria.objects.create(nombre=' Masajes')

        self.assertEqual(primera.slug, 'masajes')
        self.assertEqual(segunda.slug, 'masajes-2')
        self.assertEqual(tercera.slug, 'masajes-3')

    def test_unicidad_de_nombre_via_integrity_error(self):
        Categoria.objects.create(nombre='Spa')

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                # Slug distinto para aislar la violación de unicidad al nombre.
                Categoria.objects.create(nombre='Spa', slug='spa-alt')

    def test_unicidad_de_slug_via_integrity_error(self):
        Categoria.objects.create(nombre='Facial', slug='tratamiento')

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                # Nombre distinto para aislar la violación de unicidad al slug.
                Categoria.objects.create(nombre='Corporal', slug='tratamiento')

    def test_nombre_requerido_via_full_clean(self):
        categoria = Categoria(nombre='')

        with self.assertRaises(ValidationError) as ctx:
            categoria.full_clean()

        self.assertIn('nombre', ctx.exception.message_dict)

    def test_nombre_excede_max_length_via_full_clean(self):
        categoria = Categoria(nombre='x' * 101)

        with self.assertRaises(ValidationError) as ctx:
            categoria.full_clean()

        self.assertIn('nombre', ctx.exception.message_dict)

    def test_slug_excede_max_length_via_full_clean(self):
        categoria = Categoria(nombre='Categoria', slug='y' * 111)

        with self.assertRaises(ValidationError) as ctx:
            categoria.full_clean()

        self.assertIn('slug', ctx.exception.message_dict)
