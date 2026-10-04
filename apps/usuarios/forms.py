from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import MaxLengthValidator

Usuario = get_user_model()


class RegistroClienteForm(UserCreationForm):
    """Formulario de registro público de clientes (R3).

    Reutiliza la mecánica de `UserCreationForm` para el alta del `Usuario`:
    - `username` obligatorio; rechaza duplicados por la unicidad del modelo
      `Usuario` (R3.9).
    - `password1` / `password2` obligatorios: `UserCreationForm` aplica los
      validadores de contraseña activos del proyecto (R3.3) y exige que ambas
      coincidan, mostrando un error en español cuando no coinciden (R3.4).

    Agrega los campos OPCIONALES del `Cliente` (`telefono`, `preferencias`),
    que la vista persistirá en el `Cliente` asociado (R3.2). El formulario solo
    describe/valida datos: no crea el `Cliente` (eso ocurre atómicamente en la
    vista, R3.6).

    Mensajes en español: Django emite los mensajes de autenticación/validación
    en español vía `LANGUAGE_CODE='es-cl'`; adicionalmente se fija de forma
    explícita el mensaje de contraseñas no coincidentes para garantizar su
    visibilidad en español (R3.4).
    """

    # Campos opcionales del Cliente (coherentes con el modelo usuarios.Cliente).
    telefono = forms.CharField(
        max_length=20,
        required=False,
        label='Teléfono',
    )
    preferencias = forms.CharField(
        required=False,
        label='Preferencias',
        widget=forms.Textarea,
        validators=[MaxLengthValidator(2000)],
    )

    error_messages = {
        **UserCreationForm.error_messages,
        'password_mismatch': 'Las contraseñas no coinciden.',
    }

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username',)
