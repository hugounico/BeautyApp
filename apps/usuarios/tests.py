from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.usuarios.models import Cliente


class UsuarioModelTest(TestCase):
    """Tests unitarios del modelo Usuario (Custom User Model)."""

    def test_creacion_via_create_user(self):
        usuario_model = get_user_model()
        usuario = usuario_model.objects.create_user(
            username='ana',
            password='clave-segura-123',
        )
        self.assertEqual(usuario.username, 'ana')
        self.assertTrue(usuario.check_password('clave-segura-123'))
        self.assertEqual(usuario_model.objects.count(), 1)

    def test_str_retorna_nombre_completo_cuando_hay_nombre(self):
        usuario_model = get_user_model()
        usuario = usuario_model.objects.create_user(
            username='ana',
            password='clave-segura-123',
            first_name='Ana',
            last_name='Pérez',
        )
        self.assertEqual(str(usuario), 'Ana Pérez')
        self.assertEqual(str(usuario), usuario.get_full_name())

    def test_str_retorna_username_cuando_no_hay_nombre(self):
        usuario_model = get_user_model()
        usuario = usuario_model.objects.create_user(
            username='sinnombre',
            password='clave-segura-123',
        )
        self.assertEqual(usuario.get_full_name(), '')
        self.assertEqual(str(usuario), 'sinnombre')


class ClienteModelTest(TestCase):
    """Tests unitarios del modelo Cliente (perfil de reservas)."""

    def setUp(self):
        usuario_model = get_user_model()
        self.usuario = usuario_model.objects.create_user(
            username='cliente1',
            password='clave-segura-123',
            first_name='Carla',
            last_name='Soto',
        )

    def test_creacion_one_to_one_con_usuario(self):
        cliente = Cliente.objects.create(usuario=self.usuario)
        self.assertEqual(cliente.usuario, self.usuario)
        self.assertEqual(self.usuario.perfil_cliente, cliente)
        self.assertEqual(Cliente.objects.count(), 1)

    def test_str_delega_a_str_del_usuario(self):
        cliente = Cliente.objects.create(usuario=self.usuario)
        self.assertEqual(str(cliente), str(self.usuario))
        self.assertEqual(str(cliente), 'Carla Soto')

    def test_preferencias_menor_o_igual_a_2000_es_valido(self):
        cliente = Cliente(usuario=self.usuario, preferencias='x' * 2000)
        # No debe lanzar ValidationError en el límite exacto.
        cliente.full_clean()

    def test_preferencias_mayor_a_2000_rechazado_por_full_clean(self):
        cliente = Cliente(usuario=self.usuario, preferencias='x' * 2001)
        with self.assertRaises(ValidationError) as contexto:
            cliente.full_clean()
        self.assertIn('preferencias', contexto.exception.error_dict)

    def test_cascade_elimina_cliente_al_borrar_usuario(self):
        Cliente.objects.create(usuario=self.usuario)
        self.assertEqual(Cliente.objects.count(), 1)
        self.usuario.delete()
        self.assertEqual(Cliente.objects.count(), 0)
