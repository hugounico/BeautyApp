from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Cliente, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'telefono', 'fecha_creacion']
    list_filter = []
    search_fields = ['usuario__username', 'usuario__email', 'telefono']
