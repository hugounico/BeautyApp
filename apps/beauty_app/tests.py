from django.test import TestCase


class SmokeTest(TestCase):
    def test_django_setup_completes_without_exception(self):
        """Verifica que django.setup() se completa sin errores.

        Como el test runner ya invoca django.setup() antes de ejecutar
        los tests, si llegamos aquí sin excepción, la configuración es válida.
        """
        # django.setup() ya fue invocado por el test runner.
        # Verificamos que las apps están cargadas correctamente.
        from django.apps import apps
        self.assertTrue(apps.is_installed('apps.beauty_app'))
