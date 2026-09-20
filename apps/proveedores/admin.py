from django.contrib import admin

from .models import ProveedorProfesional


@admin.register(ProveedorProfesional)
class ProveedorProfesionalAdmin(admin.ModelAdmin):
    list_display = ['nombre_comercial', 'es_negocio', 'modalidad', 'activo']
    list_filter = ['activo', 'modalidad', 'es_negocio']
    search_fields = ['nombre_comercial', 'biografia']
