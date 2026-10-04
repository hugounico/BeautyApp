"""Tests del shell visual base (R5).

Cubren: carga de base.html, los cuatro estados de la navbar y su prioridad,
el carácter POST-only del logout en la UI, la integración del bloque de
mensajes, la herencia de base.html, y las referencias a los estáticos
css/main.css y js/main.js. Framework: django.test.TestCase + Client.
"""

from django.contrib.auth import get_user_model
from django.contrib.messages import constants as message_constants
from django.test import TestCase
from django.urls import reverse

from apps.proveedores.models import ProveedorProfesional
from apps.usuarios.models import Cliente

Usuario = get_user_model()


class RutasConNombreTests(TestCase):
    """R5.5: home, login, logout y registro resuelven por nombre."""

    def test_rutas_resuelven_por_nombre(self):
        self.assertEqual(reverse('home'), '/')
        self.assertEqual(reverse('login'), '/ingresar/')
        self.assertEqual(reverse('logout'), '/salir/')
        self.assertEqual(reverse('registro'), '/registro/')


class BaseHtmlRenderTests(TestCase):
    """R5.1, R5.2, R5.4: base.html carga, Home 200 y referencias a estáticos."""

    def test_home_responde_200(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)

    def test_home_extiende_base_html(self):
        resp = self.client.get(reverse('home'))
        self.assertTemplateUsed(resp, 'base.html')
        self.assertTemplateUsed(resp, 'beauty_app/home.html')

    def test_home_sin_catalogo(self):
        """R5.4: Home no lista servicios, categorías ni proveedores."""
        resp = self.client.get(reverse('home'))
        html = resp.content.decode('utf-8').lower()
        # No hay señales de catálogo embebido en el Home mínimo.
        self.assertNotIn('categoria', html)
        self.assertNotIn('precio', html)

    def test_base_referencia_estaticos_css_y_js(self):
        """R5.1/R5.2: la página renderizada referencia css/main.css y js/main.js."""
        resp = self.client.get(reverse('home'))
        html = resp.content.decode('utf-8')
        self.assertIn('css/main.css', html)
        self.assertIn('js/main.js', html)

    def test_base_declara_lang_es(self):
        resp = self.client.get(reverse('home'))
        self.assertIn('lang="es"', resp.content.decode('utf-8'))

    def test_base_no_tiene_estilos_ni_scripts_inline_prohibidos(self):
        """R5.1: sin style="" ni <script> inline (solo el <script src> permitido)."""
        resp = self.client.get(reverse('home'))
        html = resp.content.decode('utf-8')
        self.assertNotIn('style="', html)
        # El único <script> admisible es el que carga js/main.js por src.
        self.assertNotIn('<script>', html)


class NavbarAnonimoTests(TestCase):
    """R5.6: estado ANÓNIMO."""

    def test_anonimo_muestra_ingresar_y_registrarse_sin_logout(self):
        resp = self.client.get(reverse('home'))
        html = resp.content.decode('utf-8')
        self.assertIn(reverse('login'), html)
        self.assertIn(reverse('registro'), html)
        self.assertIn('Ingresar', html)
        self.assertIn('Registrarse', html)
        # Sin control de logout: no hay form POST a logout.
        self.assertNotIn('action="%s"' % reverse('logout'), html)


class NavbarClienteTests(TestCase):
    """R5.8: estado CLIENTE (perfil_cliente, sin perfil_proveedor)."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='cliente_nav', password='clave-segura-123'
        )
        Cliente.objects.create(usuario=self.usuario)
        self.client.force_login(self.usuario)

    def test_cliente_muestra_estado_y_logout_sin_accesos_anonimos(self):
        resp = self.client.get(reverse('home'))
        html = resp.content.decode('utf-8')
        self.assertIn('data-navbar-state="cliente"', html)
        self.assertIn('action="%s"' % reverse('logout'), html)
        self.assertNotIn('>Ingresar<', html)
        self.assertNotIn('>Registrarse<', html)


class NavbarProveedorTests(TestCase):
    """R5.7: estado PROVEEDOR (perfil_proveedor)."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='proveedor_nav', password='clave-segura-123'
        )
        ProveedorProfesional.objects.create(
            nombre_comercial='Studio Nav', usuario=self.usuario
        )
        self.client.force_login(self.usuario)

    def test_proveedor_muestra_estado_y_logout(self):
        resp = self.client.get(reverse('home'))
        html = resp.content.decode('utf-8')
        self.assertIn('data-navbar-state="proveedor"', html)
        self.assertIn('action="%s"' % reverse('logout'), html)
        self.assertNotIn('>Ingresar<', html)
        self.assertNotIn('>Registrarse<', html)


class NavbarNeutroTests(TestCase):
    """R5.9: estado NEUTRO (autenticado sin perfil, p. ej. superusuario)."""

    def setUp(self):
        self.usuario = Usuario.objects.create_superuser(
            username='admin_nav', password='clave-segura-123'
        )
        self.client.force_login(self.usuario)

    def test_neutro_muestra_estado_autenticado_y_logout(self):
        resp = self.client.get(reverse('home'))
        html = resp.content.decode('utf-8')
        self.assertIn('data-navbar-state="neutro"', html)
        self.assertIn('action="%s"' % reverse('logout'), html)
        self.assertNotIn('>Ingresar<', html)
        self.assertNotIn('>Registrarse<', html)


class NavbarPrioridadTests(TestCase):
    """R5.10: un usuario con AMBOS perfiles renderiza el estado PROVEEDOR."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='ambos_nav', password='clave-segura-123'
        )
        Cliente.objects.create(usuario=self.usuario)
        ProveedorProfesional.objects.create(
            nombre_comercial='Ambos Studio', usuario=self.usuario
        )
        self.client.force_login(self.usuario)

    def test_usuario_con_ambos_perfiles_prioriza_proveedor(self):
        resp = self.client.get(reverse('home'))
        html = resp.content.decode('utf-8')
        self.assertIn('data-navbar-state="proveedor"', html)
        # No debe mostrarse simultáneamente el estado cliente.
        self.assertNotIn('data-navbar-state="cliente"', html)
        self.assertNotIn('data-navbar-state="neutro"', html)


class LogoutPostOnlyTests(TestCase):
    """R2.4/R2.5/R2.6 (reconfirmado desde el shell): logout es POST-only."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='logout_nav', password='clave-segura-123'
        )
        Cliente.objects.create(usuario=self.usuario)

    def test_navbar_logout_es_form_post_con_csrf(self):
        self.client.force_login(self.usuario)
        resp = self.client.get(reverse('home'))
        html = resp.content.decode('utf-8')
        self.assertIn('<form class="navbar__logout" method="post"', html)
        self.assertIn('csrfmiddlewaretoken', html)

    def test_logout_via_get_no_cierra_sesion(self):
        self.client.force_login(self.usuario)
        resp = self.client.get(reverse('logout'))
        # GET no debe cerrar la sesión: el usuario sigue autenticado.
        self.assertNotEqual(resp.status_code, 302)
        home = self.client.get(reverse('home'))
        self.assertIn('action="%s"' % reverse('logout'), home.content.decode('utf-8'))


class MensajesIntegracionTests(TestCase):
    """R5.3: el bloque de mensajes muestra activos y nada cuando no hay."""

    def test_sin_mensajes_no_renderiza_contenedor(self):
        resp = self.client.get(reverse('home'))
        html = resp.content.decode('utf-8')
        self.assertNotIn('class="messages"', html)

    def test_mensaje_activo_se_renderiza_desde_base(self):
        """Un flujo que agrega un mensaje (registro exitoso) lo muestra tras seguir el redirect."""
        resp = self.client.post(
            reverse('registro'),
            data={
                'username': 'nuevo_cliente_msg',
                'password1': 'Clave-Segura-123',
                'password2': 'Clave-Segura-123',
            },
            follow=True,
        )
        html = resp.content.decode('utf-8')
        self.assertIn('class="messages"', html)
        self.assertIn('bienvenida', html.lower())


class MensajesRequestFactoryTests(TestCase):
    """R5.3 (unidad): el componente de mensajes renderiza items presentes."""

    def test_render_directo_de_mensajes(self):
        from django.template.loader import render_to_string
        from django.contrib.messages.storage.base import Message

        contexto = {
            'messages': [
                Message(message_constants.SUCCESS, 'Hola', extra_tags=''),
            ]
        }
        html = render_to_string('components/messages.html', contexto)
        self.assertIn('class="messages"', html)
        self.assertIn('Hola', html)

    def test_render_directo_sin_mensajes(self):
        from django.template.loader import render_to_string

        html = render_to_string('components/messages.html', {'messages': []})
        self.assertNotIn('class="messages"', html)
