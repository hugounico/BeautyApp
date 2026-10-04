from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from apps.usuarios.forms import RegistroClienteForm
from apps.usuarios.models import Cliente


class UsuarioLoginView(LoginView):
    """Login nativo de Django (R2).

    - Autentica por `username` con `AuthenticationForm` (credenciales válidas
      inician sesión; inválidas no la inician ni modifican la sesión previa,
      mostrando el error en español vía LANGUAGE_CODE='es-cl'). (R2.1–R2.3)
    - `redirect_authenticated_user=True`: un usuario ya autenticado que pide
      el login es redirigido al Destino_Por_Defecto sin ver el formulario. (R2.10)
    - El manejo seguro de `next` lo realiza `LoginView` mediante
      `url_has_allowed_host_and_scheme` contra los hosts del propio sitio:
      ruta interna segura → redirige allí; ausente/vacío/externo →
      `LOGIN_REDIRECT_URL` ('home'). (R2.7, R2.8)
    - La plantilla extiende `base.html`. (R2.11)
    """

    template_name = 'usuarios/login.html'
    redirect_authenticated_user = True


class UsuarioLogoutView(LogoutView):
    """Logout nativo de Django (R2).

    En Django moderno `LogoutView` acepta únicamente POST; un GET no cierra la
    sesión (R2.4, R2.5). Tras un POST con CSRF válido redirige a
    `LOGOUT_REDIRECT_URL` ('home'). (R2.9)
    """


class RegistroClienteView(FormView):
    """Registro público de clientes (R3).

    Crea ÚNICAMENTE un `Usuario` + su `Cliente` (related_name `perfil_cliente`),
    sin ningún `ProveedorProfesional` (R3.1, R3.5). El `Usuario` queda como
    cuenta no privilegiada: `UserCreationForm` no expone `is_staff` /
    `is_superuser` / grupos / permisos, de modo que se crean con sus valores
    por defecto (`is_staff=False`, `is_superuser=False`, sin grupos ni
    permisos) sin que la entrada del formulario pueda alterarlos (R3.5).

    Atomicidad (R3.6, R3.7): ninguna escritura ocurre antes de abrir
    `transaction.atomic()`. El `Usuario` se construye en memoria con
    `form.save(commit=False)` y recién dentro del bloque atómico se persiste el
    `Usuario` y se crea el `Cliente`. Si la creación del `Cliente` falla, el
    `INSERT` del `Usuario` se revierte en el mismo bloque: no quedan `Usuario`
    huérfanos ni `Cliente` sin `Usuario`. Ante el fallo se muestra un mensaje
    de error en español vía el framework de mensajes.

    Éxito (R3.8): `login()` automático del nuevo `Usuario`, redirección al
    Destino_Por_Defecto ('home') y mensaje de bienvenida en español.

    Datos inválidos / `username` duplicado (R3.9): re-render con errores en
    español, sin crear ningún registro (lo maneja `form_invalid`).

    Guarda de usuario autenticado (R2.10): si ya hay sesión, se redirige a
    'home' sin mostrar el formulario.
    """

    form_class = RegistroClienteForm
    template_name = 'usuarios/registro.html'
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Construir el Usuario en memoria; ninguna escritura todavía.
                usuario = form.save(commit=False)
                usuario.is_staff = False
                usuario.is_superuser = False
                usuario.save()
                # Crear el Cliente asociado dentro del mismo bloque atómico.
                Cliente.objects.create(
                    usuario=usuario,
                    telefono=form.cleaned_data.get('telefono') or None,
                    preferencias=form.cleaned_data.get('preferencias') or '',
                )
        except Exception:
            # Rollback total garantizado por transaction.atomic(). (R3.7)
            messages.error(
                self.request,
                'No se pudo completar el registro. Inténtalo nuevamente.',
            )
            return self.form_invalid(form)

        # Auto-login + mensaje de bienvenida en español. (R3.8)
        login(self.request, usuario)
        messages.success(
            self.request,
            'Te damos la bienvenida a BeautyFull. Tu cuenta fue creada.',
        )
        return redirect(self.success_url)
