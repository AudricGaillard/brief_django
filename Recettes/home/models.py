from django.db import models

# Create your models here.
from django.db import models
from django.core import validators
from datetime import datetime
from accounts.models import Utilisateur


choix_difficulte={
    'facile':'Facile',
    'moyen':'Moyen',
    'difficile':'Difficile'
}

choix_visibillite={
    'brouillon':'Brouillon',
    'publiee':'Publiée'
}

choix_unite={
    'g':'Grammes',
    'kg':'Kilogrammes',
    'ml':'Mililitres',
    'cl':'Centilitres',
    'l':'Litres',
    'c. a soupe':'Cuillère à soupe',
    'c. a cafe':'Cuillère à café',
    'piece':'Pièce',
    'pincee':'Pincée' 
}

choix_role={
    'utilisateur':'Utilisateur',
    'gestionnaire':'Gestionnaire'
}

choix_regime={
    'vegetarien':'Végétarien',
    'vegan':'Vegan',
    'sans_gluten':'Sans gluten',
    'sans_lactose':'Sans lactose'
}

choix_etat={
    'prevue':'Prévue',
    'cuisinee':'Cuisinée',
    'annulee':'Annulée'
}

# Create your models here.
class Categorie(models.Model):
    nom = models.CharField(max_length=30)

    def __str__(self):
        return self.nom


class Recette(models.Model):
    titre = models.CharField(max_length=30, unique=True)
    categorie_id = models.ForeignKey(Categorie, on_delete=models.CASCADE)
    temps_preparation_min = models.PositiveIntegerField(validators=[validators.MinValueValidator(1)], help_text="Veuillez indiquez un temps au moins supérieur à 1 minute")
    temps_cuisson_min = models.PositiveIntegerField(default=0)
    portions = models.PositiveIntegerField(validators=[validators.MinValueValidator(1)], help_text='Veuillez mettre une valeur au moins supérieur à 1')
    difficulte = models.CharField(choices=choix_difficulte)
    etat_publication = models.CharField(choices=choix_visibillite)
    etapes = models.TextField(help_text="3 à 6 étapes. Veuillez les séparer avec '|'.")
    regimes_incompatibles=models.JSONField(choices=choix_regime, default=list)

    def __str__(self):
        return self.titre


class Ingredient(models.Model):
    recette_id = models.ForeignKey(Recette, on_delete=models.CASCADE)
    nom = models.CharField(max_length=30)
    quantite =  models.PositiveIntegerField(validators=[validators.MinValueValidator(1)])
    unite = models.CharField(choices=choix_unite)

    def __str__(self):
        return self.nom


class Planification(models.Model):
    utilisateur_id = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    recette_id = models.ForeignKey(Recette, on_delete=models.CASCADE)
    etat = models.CharField(choices=choix_etat)
    date_prevue = models.DateField(validators=[validators.MinValueValidator(datetime(2026,11,1,0,0,0)), validators.MaxValueValidator(datetime(2026,12,26,0,0,0))], help_text="Saisissez une date entre le 11 novembre 2026 et le 12 décembre 2026")
    convives = models.PositiveIntegerField(validators=[validators.MinValueValidator(1), validators.MaxValueValidator(50)], help_text="Saisissez un nombre entre 1 et 50")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateField(auto_now_add=True)

