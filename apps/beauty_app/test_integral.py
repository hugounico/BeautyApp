"""Escenario integral de la fundación (R6.5).

Ejercita la secuencia realista de un socio de demo:

    seed_demo -> registro -> logout -> login

y verifica en CADA transición que la navbar (renderizada server-side en Home)
refleje el estado de autenticación correcto, usando marcadores estables en el
HTML:

- `data-navbar-state="cliente"`  -> usuario autenticado con perfil de cliente.
- Enlaces *Ingresar* y *Registrarse* + ausencia de formulario de logout
  -> visitante anónimo.

Además, se cubre el camino con la cuenta sembrada `cliente_demo`: iniciar
sesión con la contraseña entregada a `seed_demo` y confirmar que renderiza el
estado de navbar de cliente de extremo a extremo.

Marco: `django.test.TestCase` + `Client`. No se usan property-based tests
(R6 Nota). El test crea sus propios datos dentro de la transacción de test
(invocando `seed_demo` con contraseñas provistas por `os.environ`): NO depende
de las filas de la BD de desarrollo (`db.sqlite3`), ya que el runner usa una BD
de test fresca.
"""

import os
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.categorias.models import Categoria
from apps.proveedores.models import ProveedorProfesional
from apps.servicios.models import Servicio
from apps.usuarios.models import Cliente

Usuario = get_user_model()

# Contraseñas que satisfacen los validadores activos de Django (R3.3 config).
# La de cliente_demo se entrega a seed_demo por entorno, de modo que
# check_password quede alineado al iniciar sesión con cliente_demo más abajo.
DEMO_CLIENTE_PASSWORD = 'Demo-Cli-Integral-2024!'
DEMO_PROVEEDOR_PASSWORD = 'Demo-Prov-Integral-2024!'

ENV_DEMO = {
    'DEMO_CLIENTE_PASSWORD': DEMO_CLIENTE_PASSWORD,
    'DEMO_PROVEEDOR_PASSWORD': DEMO_PROVEEDOR_PASSWORD,
}

# Credenciales del visitante nuevo que se registra durante el escenario.
# El password se mantiene DISÍMIL del username para no activar el
# UserAttributeSimilarityValidator de Django.
NUEVO_USERNAME = 'socio_nuevo'
NUEVO_PASSWORD = 'Zafiro-Lluvia-4821!'


class EscenarioIntegralTests(TestCase):
    """Escenario integral seed_demo -> registro -> logout -> login (R6.5)."""

    def setUp(self):
        # Partir siempre de un entorno sin las variables demo, para que el
        # control sobre ellas sea explícito en cada paso.
        for clave in ('DEMO_CLIENTE_PASSWORD', 'DEMO_PROVEEDOR_PASSWORD'):
            os.environ.pop(clave, None)
        self.home_url = reverse('home')
        self.registro_url = reverse('registro')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')

    # -- helpers -----------------------------------------------------------

    def _render_home(self):
        """GET a Home; devuelve la respuesta (contiene la navbar renderizada)."""
        respuesta = self.client.get(self.home_url)
        self.assertEqual(respuesta.status_code, 200)
        return respuesta

    def _assert_navbar_cliente(self, respuesta):
        """La navbar muestra el estado CLIENTE: marcador + logout, sin accesos
        de visitante anónimo."""
        self.assertContains(respuesta, 'data-navbar-state="cliente"')
        # Control de logout presente como formulario POST hacia 'logout'.
        self.assertContains(respuesta, 'action="%s"' % self.logout_url)
        self.assertContains(respuesta, 'method="post"')
        # No se muestran accesos de visitante anónimo.
        self.assertNotContains(respuesta, 'href="%s"' % self.login_url)
        self.assertNotContains(respuesta, 'href="%s"' % self.registro_url)

    def _assert_navbar_anonimo(self, respuesta):
        """La navbar muestra el estado ANÓNIMO: Ingresar + Registrarse, sin
        formulario de logout ni marcador de estado autenticado."""
        self.assertContains(respuesta, 'href="%s"' % self.login_url)
        self.assertContains(respuesta, 'href="%s"' % self.registro_url)
        # Sin control de logout.
        self.assertNotContains(respuesta, 'action="%s"' % self.logout_url)
        # Sin marcador de estado autenticado alguno.
        self.assertNotContains(respuesta, 'data-navbar-state=')

    def _run_seed_demo(self):
        """Invoca seed_demo con las contraseñas demo provistas por entorno."""
        out = StringIO()
        with mock.patch.dict(os.environ, ENV_DEMO, clear=False):
            call_command('seed_demo', stdout=out)
        return out.getvalue()

    # -- escenario ---------------------------------------------------------

    def test_escenario_integral_seed_registro_logout_login(self):
        # === Paso 1: seed_demo ===========================================
        # Sembrar el dataset de demo exactamente como lo vería un socio.
        self._run_seed_demo()

        # Evidencia del dataset sembrado (R4.1, R4.2, R4.4).
        self.assertEqual(Categoria.objects.count(), 3)
        self.assertEqual(Servicio.objects.count(), 6)
        self.assertEqual(ProveedorProfesional.objects.count(), 3)
        self.assertTrue(Usuario.objects.filter(username='cliente_demo').exists())
        self.assertTrue(Usuario.objects.filter(username='proveedor_demo').exists())

        # === Paso 2: registro ============================================
        # Un visitante NUEVO se registra; el registro crea Usuario+Cliente,
        # auto-login y redirige a home (R3.8). Un registro fresco crea un
        # Cliente, por lo que la navbar debe pasar al estado CLIENTE.
        respuesta_registro = self.client.post(
            self.registro_url,
            {
                'username': NUEVO_USERNAME,
                'password1': NUEVO_PASSWORD,
                'password2': NUEVO_PASSWORD,
            },
        )
        self.assertEqual(respuesta_registro.status_code, 302)
        self.assertEqual(respuesta_registro.url, self.home_url)
        # Auto-login: la sesión quedó autenticada con el nuevo usuario.
        self.assertIn('_auth_user_id', self.client.session)
        nuevo_usuario = Usuario.objects.get(username=NUEVO_USERNAME)
        self.assertEqual(
            int(self.client.session['_auth_user_id']), nuevo_usuario.pk
        )
        # Navbar tras registro -> CLIENTE.
        self._assert_navbar_cliente(self._render_home())

        # === Paso 3: logout ==============================================
        respuesta_logout = self.client.post(self.logout_url)
        self.assertEqual(respuesta_logout.status_code, 302)
        # Sesión limpiada.
        self.assertNotIn('_auth_user_id', self.client.session)
        # Navbar tras logout -> ANÓNIMO.
        self._assert_navbar_anonimo(self._render_home())

        # === Paso 4: login ===============================================
        # El socio vuelve a iniciar sesión con las MISMAS credenciales recién
        # registradas (flujo realista: registro -> logout -> login).
        respuesta_login = self.client.post(
            self.login_url,
            {'username': NUEVO_USERNAME, 'password': NUEVO_PASSWORD},
        )
        self.assertEqual(respuesta_login.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(
            int(self.client.session['_auth_user_id']), nuevo_usuario.pk
        )
        # Navbar tras login -> CLIENTE nuevamente.
        self._assert_navbar_cliente(self._render_home())

    def test_cliente_demo_sembrado_inicia_sesion_y_navbar_cliente(self):
        """La cuenta sembrada `cliente_demo` funciona de extremo a extremo:
        login con la contraseña entregada a seed_demo -> navbar CLIENTE."""
        # Sembrar con las contraseñas demo (misma contraseña que usaremos para
        # autenticar a cliente_demo, de modo que check_password alinee).
        self._run_seed_demo()

        cliente_demo = Usuario.objects.get(username='cliente_demo')
        # cliente_demo tiene su Cliente asociado (R4.4).
        self.assertTrue(Cliente.objects.filter(usuario=cliente_demo).exists())
        # La contraseña vigente corresponde a la entregada a seed_demo (R4.6).
        self.assertTrue(cliente_demo.check_password(DEMO_CLIENTE_PASSWORD))

        # Login real vía el formulario con esa contraseña.
        respuesta_login = self.client.post(
            self.login_url,
            {'username': 'cliente_demo', 'password': DEMO_CLIENTE_PASSWORD},
        )
        self.assertEqual(respuesta_login.status_code, 302)
        self.assertEqual(
            int(self.client.session['_auth_user_id']), cliente_demo.pk
        )
        # Home renderiza la navbar en estado CLIENTE para cliente_demo.
        self._assert_navbar_cliente(self._render_home())


class ProveedorDemoLoginRealTests(TestCase):
    """La cuenta sembrada `proveedor_demo` funciona de extremo a extremo vía
    el endpoint REAL de login (no force_login, no hacks de sesión ORM).

    Complementa la cobertura existente:
    - `NavbarProveedorTests` (test_shell_visual) usa force_login + ORM y un
      proveedor ad-hoc, NO la cuenta sembrada ni el endpoint real.
    - `EscenarioIntegralTests` ejercita el endpoint real pero sólo con
      cliente_demo / socio_nuevo, NO con proveedor_demo.

    Aquí: seed_demo -> login real como proveedor_demo con la contraseña
    entregada a seed_demo -> navbar en estado PROVEEDOR -> y el proveedor
    marcado (recibe_cuenta_demo=True) es 'Studio Aurora [DEMO]'.
    """

    def setUp(self):
        # Entorno limpio: el control sobre las variables demo es explícito.
        for clave in ('DEMO_CLIENTE_PASSWORD', 'DEMO_PROVEEDOR_PASSWORD'):
            os.environ.pop(clave, None)
        self.home_url = reverse('home')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.registro_url = reverse('registro')

    def _run_seed_demo(self):
        """Invoca seed_demo con las contraseñas demo provistas por entorno."""
        out = StringIO()
        with mock.patch.dict(os.environ, ENV_DEMO, clear=False):
            call_command('seed_demo', stdout=out)
        return out.getvalue()

    def _render_home(self):
        """GET a Home; devuelve la respuesta (contiene la navbar renderizada)."""
        respuesta = self.client.get(self.home_url)
        self.assertEqual(respuesta.status_code, 200)
        return respuesta

    def _assert_navbar_proveedor(self, respuesta):
        """La navbar muestra el estado PROVEEDOR: marcador estable + logout
        POST, sin accesos de visitante anónimo."""
        self.assertContains(respuesta, 'data-navbar-state="proveedor"')
        # Control de logout presente como formulario POST hacia 'logout'.
        self.assertContains(respuesta, 'action="%s"' % self.logout_url)
        self.assertContains(respuesta, 'method="post"')
        # No se muestran accesos de visitante anónimo.
        self.assertNotContains(respuesta, '>Ingresar<')
        self.assertNotContains(respuesta, '>Registrarse<')

    def test_proveedor_demo_login_real_navbar_proveedor_y_vinculo(self):
        # === Paso 1: seed_demo con contraseñas por entorno ================
        self._run_seed_demo()

        proveedor_demo = Usuario.objects.get(username='proveedor_demo')
        # La contraseña vigente corresponde a la entregada a seed_demo (R4.6),
        # de modo que el login real por endpoint alinee check_password.
        self.assertTrue(proveedor_demo.check_password(DEMO_PROVEEDOR_PASSWORD))

        # === Paso 2: login REAL vía el endpoint (POST a 'login') ==========
        # Sin force_login ni manipulación de sesión: autenticación de verdad.
        respuesta_login = self.client.post(
            self.login_url,
            {'username': 'proveedor_demo', 'password': DEMO_PROVEEDOR_PASSWORD},
        )
        self.assertEqual(respuesta_login.status_code, 302)
        # La sesión quedó autenticada como proveedor_demo.
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(
            int(self.client.session['_auth_user_id']), proveedor_demo.pk
        )

        # === Paso 3: navbar en estado PROVEEDOR ===========================
        self._assert_navbar_proveedor(self._render_home())

        # === Paso 4: el proveedor marcado está vinculado y es el esperado ==
        # proveedor_demo se vincula al proveedor con recibe_cuenta_demo=True,
        # cuyo nombre_comercial determinista es 'Studio Aurora [DEMO]' (R4.4).
        proveedor = ProveedorProfesional.objects.get(usuario=proveedor_demo)
        self.assertEqual(proveedor.nombre_comercial, 'Studio Aurora [DEMO]')
