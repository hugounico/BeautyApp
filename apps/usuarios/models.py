from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'

    def __str__(self):
        return self.get_full_name() or self.username
