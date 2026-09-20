from django.core.validators import MinValueValidator
from django.db import models


class Servicio(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    duracion_minutos = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    precio_base_clp = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    categoria = models.ForeignKey(
        'categorias.Categoria',
        on_delete=models.PROTECT,
        related_name='servicios',
    )
    proveedores = models.ManyToManyField(
        'proveedores.ProveedorProfesional',
        blank=True,
        related_name='servicios',
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'servicio'
        verbose_name_plural = 'servicios'
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return self.nombre
