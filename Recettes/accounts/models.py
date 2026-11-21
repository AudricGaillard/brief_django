from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

choix_regime={
    'vegetarien':'Végétarien',
    'vegan':'Vegan',
    'sans_gluten':'Sans gluten',
    'sans_lactose':'Sans lactose'
}

class Role(models.TextChoices):
    UTILISATEUR = "utilisateur", "Utilisateur"
    GESTIONNAIRE = "gestionnaire", "Gestionnaire"


class Utilisateur(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.UTILISATEUR,
    )
    regime = models.CharField(
        max_length=100,
        choices=choix_regime,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.username