from django.urls import path

from apps.usuarios.views import (
    RegistroClienteView,
    UsuarioLoginView,
    UsuarioLogoutView,
)

urlpatterns = [
    # Login nativo: GET muestra el formulario, POST autentica. (R2.1, R2.11, R5.5)
    path('ingresar/', UsuarioLoginView.as_view(), name='login'),
    # Logout nativo: solo POST con CSRF cierra la sesión. (R2.4, R2.6, R5.5)
    path('salir/', UsuarioLogoutView.as_view(), name='logout'),
    # Registro público de clientes: GET muestra el formulario, POST registra. (R3.10, R5.5)
    path('registro/', RegistroClienteView.as_view(), name='registro'),
]
