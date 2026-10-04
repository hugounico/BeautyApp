from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Home mínima del shell visual (R5.4).

    Página de inicio con contenido global, sin catálogo (sin listados de
    servicios, categorías ni proveedores). Extiende `base.html`. Es el
    `Destino_Por_Defecto` resuelto por la ruta con nombre `home`, usado por
    `LOGIN_REDIRECT_URL` / `LOGOUT_REDIRECT_URL`. (R5.4, R5.5)
    """

    template_name = 'beauty_app/home.html'
