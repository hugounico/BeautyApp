from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

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


Usuario = get_user_model()


class AutenticacionLoginTests(TestCase):
    """Tests de integración del login nativo (R2.1, R2.2, R2.3, R2.7, R2.8, R2.10, R2.11).

    Nota de alcance ('home'): la ruta con nombre `home` no existe hasta la Wave 5
    (task 7.1). Por eso las aserciones de redirección usan
    `fetch_redirect_response=False` y comprueban que el destino configurado es
    `settings.LOGIN_REDIRECT_URL` ('home'), sin seguir la redirección hasta un 200.
    """

    def setUp(self):
        self.password = 'Clave-Segura-123!'
        self.usuario = Usuario.objects.create_user(
            username='persona',
            password=self.password,
        )
        self.login_url = reverse('login')

    def test_login_valido_inicia_sesion(self):
        """R2.1: credenciales válidas autentican e inician sesión."""
        respuesta = self.client.post(
            self.login_url,
            {'username': 'persona', 'password': self.password},
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            int(self.client.session['_auth_user_id']),
            self.usuario.pk,
        )

    def test_login_invalido_muestra_error_en_espanol_y_no_inicia_sesion(self):
        """R2.2: credenciales inválidas re-renderizan con error en español y no inician sesión."""
        respuesta = self.client.post(
            self.login_url,
            {'username': 'persona', 'password': 'incorrecta'},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        # Mensaje de error en español provisto por la plantilla ante form.errors.
        self.assertContains(respuesta, 'incorrect')

    def test_login_fallido_preserva_sesion_previa(self):
        """R2.3: un login fallido no crea ni modifica una sesión autenticada."""
        # Sesión previa: autenticada.
        self.client.force_login(self.usuario)
        self.assertEqual(
            int(self.client.session['_auth_user_id']),
            self.usuario.pk,
        )
        # Intento de login con credenciales inválidas (otra identidad).
        otro = Usuario.objects.create_user(username='otro', password='Clave-Segura-123!')
        self.client.post(
            self.login_url,
            {'username': 'otro', 'password': 'mal'},
        )
        # La sesión previa permanece intacta.
        self.assertEqual(
            int(self.client.session['_auth_user_id']),
            self.usuario.pk,
        )
        self.assertNotEqual(
            int(self.client.session['_auth_user_id']),
            otro.pk,
        )

    def test_next_interno_seguro_redirige_alli(self):
        """R2.7: un `next` interno relativo seguro redirige a ese destino."""
        destino = reverse('login')  # ruta interna existente y segura
        respuesta = self.client.post(
            self.login_url + '?next=' + destino,
            {'username': 'persona', 'password': self.password},
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, destino)

    def test_next_externo_redirige_al_destino_por_defecto(self):
        """R2.8: un `next` externo (host/esquema ajeno) se ignora → LOGIN_REDIRECT_URL."""
        respuesta = self.client.post(
            self.login_url + '?next=https://malicioso.example.com/robar',
            {'username': 'persona', 'password': self.password},
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, reverse(settings.LOGIN_REDIRECT_URL))

    def test_next_ausente_redirige_al_destino_por_defecto(self):
        """R2.8: `next` ausente → LOGIN_REDIRECT_URL ('home')."""
        respuesta = self.client.post(
            self.login_url,
            {'username': 'persona', 'password': self.password},
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, reverse(settings.LOGIN_REDIRECT_URL))

    def test_usuario_autenticado_en_login_es_redirigido(self):
        """R2.10 (alcance login): un usuario ya autenticado que pide login es
        redirigido sin ver el formulario (redirect_authenticated_user=True).

        Nota de alcance ('registro'): la ruta `registro` no existe hasta la
        Wave 3 (task 4.x); la guarda equivalente para la vista de registro se
        cubrirá en los tests de la Wave 3.
        """
        self.client.force_login(self.usuario)
        respuesta = self.client.get(self.login_url)
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, reverse(settings.LOGIN_REDIRECT_URL))

    def test_plantilla_login_extiende_base(self):
        """R2.11: la plantilla de login extiende base.html (se verifica por el
        template usado y por marcadores propios de base.html en el render)."""
        respuesta = self.client.get(self.login_url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, 'usuarios/login.html')
        self.assertTemplateUsed(respuesta, 'base.html')
        # base.html define lang="es" y el doctype; su presencia confirma herencia.
        self.assertContains(respuesta, '<html lang="es">')


class AutenticacionLogoutTests(TestCase):
    """Tests de integración del logout nativo (R2.4, R2.5, R2.6, R2.9).

    Nota de alcance ('home'): igual que en login, las redirecciones usan
    `fetch_redirect_response=False` / comprobación del destino configurado,
    porque la ruta `home` no existe hasta la Wave 5.
    """

    def setUp(self):
        self.password = 'Clave-Segura-123!'
        self.usuario = Usuario.objects.create_user(
            username='persona',
            password=self.password,
        )
        self.logout_url = reverse('logout')

    def test_logout_post_cierra_sesion_y_redirige(self):
        """R2.4 / R2.6 / R2.9: POST con CSRF cierra la sesión y redirige a
        LOGOUT_REDIRECT_URL ('home')."""
        self.client.force_login(self.usuario)
        self.assertIn('_auth_user_id', self.client.session)

        respuesta = self.client.post(self.logout_url)

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, reverse(settings.LOGOUT_REDIRECT_URL))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_get_no_cierra_sesion(self):
        """R2.5: un GET a logout no cierra la sesión (LogoutView es POST-only)."""
        self.client.force_login(self.usuario)
        self.assertIn('_auth_user_id', self.client.session)

        respuesta = self.client.get(self.logout_url)

        # GET no está permitido: la sesión permanece activa.
        self.assertNotEqual(respuesta.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)


from unittest import mock

from django.contrib.messages import get_messages

from apps.proveedores.models import ProveedorProfesional
from apps.usuarios.forms import RegistroClienteForm


class RegistroClienteTests(TestCase):
    """Tests de integración del registro público de clientes (R3)."""

    def setUp(self):
        self.registro_url = reverse('registro')
        self.password = 'Clave-Segura-123!'
        self.datos_validos = {
            'username': 'nuevo_cliente',
            'password1': self.password,
            'password2': self.password,
        }

    def test_registro_valido_crea_usuario_y_cliente_no_privilegiado(self):
        """R3.1 / R3.5: un registro válido crea exactamente un Usuario + un
        Cliente, no privilegiado, sin grupos/permisos ni ProveedorProfesional."""
        respuesta = self.client.post(self.registro_url, self.datos_validos)
        self.assertEqual(respuesta.status_code, 302)

        self.assertEqual(Usuario.objects.count(), 1)
        self.assertEqual(Cliente.objects.count(), 1)
        self.assertEqual(ProveedorProfesional.objects.count(), 0)

        usuario = Usuario.objects.get(username='nuevo_cliente')
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertEqual(usuario.groups.count(), 0)
        self.assertEqual(usuario.user_permissions.count(), 0)
        # El Cliente queda ligado por el OneToOne perfil_cliente.
        self.assertEqual(usuario.perfil_cliente, Cliente.objects.get())
        # No existe vínculo de proveedor.
        self.assertFalse(hasattr(usuario, 'perfil_proveedor'))

    def test_password_rechazada_por_validadores_de_django(self):
        """R3.3: una contraseña débil (demasiado corta/común) es rechazada por
        los validadores activos de Django, en español, sin crear registros."""
        datos = {
            'username': 'cliente_debil',
            'password1': '123',
            'password2': '123',
        }
        respuesta = self.client.post(self.registro_url, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)
        self.assertEqual(Cliente.objects.count(), 0)
        # Mensaje de validador en español (p. ej. "demasiado corta"/"común").
        self.assertContains(respuesta, 'contraseña')

    def test_passwords_no_coinciden_error_en_espanol_sin_registros(self):
        """R3.4: contraseñas distintas → error en español, sin crear registros."""
        datos = {
            'username': 'cliente_mismatch',
            'password1': self.password,
            'password2': 'Otra-Clave-456!',
        }
        respuesta = self.client.post(self.registro_url, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)
        self.assertEqual(Cliente.objects.count(), 0)
        self.assertContains(respuesta, 'Las contraseñas no coinciden.')

    def test_creacion_atomica_y_fecha_creacion_automatica(self):
        """R3.6: Usuario + Cliente creados atómicamente; fecha_creacion auto."""
        respuesta = self.client.post(self.registro_url, self.datos_validos)
        self.assertEqual(respuesta.status_code, 302)
        cliente = Cliente.objects.get()
        # fecha_creacion fijada por auto_now_add.
        self.assertIsNotNone(cliente.fecha_creacion)

    def test_fallo_intermedio_revierte_transaccion_sin_huerfanos(self):
        """R3.7: un fallo durante la creación del Cliente revierte la
        transacción completa; no quedan Usuario huérfanos ni Cliente sin Usuario."""
        with mock.patch(
            'apps.usuarios.views.Cliente.objects.create',
            side_effect=Exception('fallo inducido'),
        ):
            respuesta = self.client.post(self.registro_url, self.datos_validos)

        # Re-render del formulario (no redirect) y rollback total.
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)
        self.assertEqual(Cliente.objects.count(), 0)
        # Mensaje de error en español vía framework de mensajes.
        mensajes = [str(m) for m in get_messages(respuesta.wsgi_request)]
        self.assertTrue(any('No se pudo completar el registro' in m for m in mensajes))

    def test_registro_exitoso_auto_login_redirect_y_mensaje_bienvenida(self):
        """R3.8: éxito → auto-login, redirect a 'home', mensaje de bienvenida."""
        respuesta = self.client.post(self.registro_url, self.datos_validos)
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, reverse('home'))
        # Sesión autenticada tras el registro.
        self.assertIn('_auth_user_id', self.client.session)
        usuario = Usuario.objects.get(username='nuevo_cliente')
        self.assertEqual(int(self.client.session['_auth_user_id']), usuario.pk)
        # Mensaje de bienvenida en español.
        mensajes = [str(m) for m in get_messages(respuesta.wsgi_request)]
        self.assertTrue(any('bienvenida' in m.lower() for m in mensajes))

    def test_username_duplicado_error_en_espanol_sin_registros(self):
        """R3.9: username ya existente → error en español, sin nuevos registros."""
        Usuario.objects.create_user(username='nuevo_cliente', password=self.password)
        self.assertEqual(Usuario.objects.count(), 1)

        respuesta = self.client.post(self.registro_url, self.datos_validos)
        self.assertEqual(respuesta.status_code, 200)
        # No se creó un segundo Usuario ni ningún Cliente.
        self.assertEqual(Usuario.objects.count(), 1)
        self.assertEqual(Cliente.objects.count(), 0)
        self.assertContains(respuesta, 'Ya existe')

    def test_datos_invalidos_sin_username_no_crea_registros(self):
        """R3.9: datos inválidos (username vacío) → re-render, sin registros."""
        datos = {
            'username': '',
            'password1': self.password,
            'password2': self.password,
        }
        respuesta = self.client.post(self.registro_url, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)
        self.assertEqual(Cliente.objects.count(), 0)

    def test_form_expone_campos_obligatorios_y_opcionales(self):
        """R3.2: el form expone username, password1, password2 (obligatorios) y
        telefono, preferencias (opcionales)."""
        form = RegistroClienteForm()
        for campo in ('username', 'password1', 'password2', 'telefono', 'preferencias'):
            self.assertIn(campo, form.fields)
        self.assertTrue(form.fields['username'].required)
        self.assertTrue(form.fields['password1'].required)
        self.assertTrue(form.fields['password2'].required)
        self.assertFalse(form.fields['telefono'].required)
        self.assertFalse(form.fields['preferencias'].required)

    def test_campos_opcionales_se_persisten_en_cliente(self):
        """R3.2: telefono y preferencias opcionales se guardan en el Cliente."""
        datos = dict(self.datos_validos)
        datos['telefono'] = '+56912345678'
        datos['preferencias'] = 'Prefiere horarios de tarde.'
        respuesta = self.client.post(self.registro_url, datos)
        self.assertEqual(respuesta.status_code, 302)
        cliente = Cliente.objects.get()
        self.assertEqual(cliente.telefono, '+56912345678')
        self.assertEqual(cliente.preferencias, 'Prefiere horarios de tarde.')

    def test_plantilla_registro_extiende_base(self):
        """R3.10: la plantilla de registro extiende base.html."""
        respuesta = self.client.get(self.registro_url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, 'usuarios/registro.html')
        self.assertTemplateUsed(respuesta, 'base.html')
        self.assertContains(respuesta, '<html lang="es">')

    def test_usuario_autenticado_en_registro_es_redirigido(self):
        """R2.10 (guarda de registro): un usuario ya autenticado que pide la
        vista de registro es redirigido a 'home' sin ver el formulario."""
        usuario = Usuario.objects.create_user(username='ya_logueado', password=self.password)
        self.client.force_login(usuario)
        respuesta = self.client.get(self.registro_url)
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, reverse('home'))
