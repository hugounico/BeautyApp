from django.conf import settings
from django.db import models


class ModalidadChoices(models.TextChoices):
    A_DOMICILIO = 'a_domicilio', 'A domicilio'
    EN_LOCAL = 'en_local', 'En local'
    AMBOS = 'ambos', 'Ambos'


class ProveedorProfesional(models.Model):
    """Proveedor de servicios de belleza.

    El vínculo con `Usuario` es OPCIONAL (null/blank): no todo proveedor
    necesita una cuenta. Difiere del vínculo de `Cliente`, que es REQUERIDO.
    Ambos usan on_delete=CASCADE. (R1.7, declarativo)
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='perfil_proveedor',
    )
    nombre_comercial = models.CharField(max_length=150)
    es_negocio = models.BooleanField(default=False)
    modalidad = models.CharField(
        max_length=20,
        choices=ModalidadChoices.choices,
        default=ModalidadChoices.A_DOMICILIO,
    )
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    biografia = models.TextField(max_length=500, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'proveedor profesional'
        verbose_name_plural = 'proveedores profesionales'
        ordering = ['nombre_comercial']

    def __str__(self):
        return self.nombre_comercial
