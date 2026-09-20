from django.db import models
from django.utils.text import slugify


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generar_slug_unico()
        super().save(*args, **kwargs)

    def _generar_slug_unico(self):
        base = slugify(self.nombre)[:110]
        slug = base
        contador = 2
        qs = Categoria.objects.exclude(pk=self.pk)
        while qs.filter(slug=slug).exists():
            sufijo = f'-{contador}'
            slug = f'{base[:110 - len(sufijo)]}{sufijo}'
            contador += 1
        return slug
