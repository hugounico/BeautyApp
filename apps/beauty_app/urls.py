from django.urls import path

from apps.beauty_app.views import HomeView

urlpatterns = [
    # Home mínima: Destino_Por_Defecto resuelto por nombre. (R5.4, R5.5)
    path('', HomeView.as_view(), name='home'),
]
