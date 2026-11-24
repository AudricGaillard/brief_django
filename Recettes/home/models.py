import datetime
from django.core import validators
from django.db import models
from accounts.models import Utilisateur


CHOIX_DIFFICULTE = [
    ("facile", "Facile"),
    ("moyen", "Moyen"),
    ("difficile", "Difficile"),
]

CHOIX_ETAT_PUBLICATION = [
    ("brouillon", "Brouillon"),
    ("publiee", "Publiée"),
]

CHOIX_UNITE = [
    ("g", "Grammes"),
    ("kg", "Kilogrammes"),
    ("ml", "Millilitres"),
    ("cl", "Centilitres"),
    ("l", "Litres"),
    ("c. à soupe", "Cuillère à soupe"),
    ("c. à café", "Cuillère à café"),
    ("pièce", "Pièce"),
    ("pincée", "Pincée"),
]

CHOIX_REGIME = [
    ("vegetarien", "Végétarien"),
    ("vegan", "Vegan"),
    ("sans_gluten", "Sans gluten"),
    ("sans_lactose", "Sans lactose"),
]

CHOIX_ETAT_PLANIFICATION = [
    ("prevue", "Prévue"),
    ("cuisinee", "Cuisinée"),
    ("annulee", "Annulée"),
]


class Categorie(models.Model):
    nom = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nom


class Recette(models.Model):
    titre = models.CharField(max_length=150, unique=True)
    categorie_id = models.ForeignKey(
        Categorie,
        on_delete=models.CASCADE,
        related_name="recettes",
    )
    temps_preparation_min = models.PositiveIntegerField(
        validators=[validators.MinValueValidator(1)],
        help_text="Indiquez un temps d'au moins 1 minute.",
    )
    temps_cuisson_min = models.PositiveIntegerField(
        default=0,
        validators=[validators.MinValueValidator(0)],
    )
    portions = models.PositiveIntegerField(
        validators=[validators.MinValueValidator(1)],
        help_text="Indiquez un nombre de portions d'au moins 1.",
    )
    difficulte = models.CharField(max_length=20, choices=CHOIX_DIFFICULTE)
    etat_publication = models.CharField(
        max_length=20,
        choices=CHOIX_ETAT_PUBLICATION,
        default="brouillon",
    )
    etapes = models.TextField(
        help_text="3 à 6 étapes séparées par '|'."
    )
    regimes_incompatibles = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.titre


class Ingredient(models.Model):
    recette_id = models.ForeignKey(
        Recette,
        on_delete=models.CASCADE,
        related_name="ingredients",
    )
    nom = models.CharField(max_length=120)
    quantite = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[validators.MinValueValidator(0.01)],
    )
    unite = models.CharField(max_length=20, choices=CHOIX_UNITE)

    def __str__(self):
        return f"{self.nom} ({self.quantite} {self.unite})"


class Planification(models.Model):
    utilisateur_id = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="planifications",
    )
    recette_id = models.ForeignKey(
        Recette,
        on_delete=models.CASCADE,
        related_name="planifications",
    )
    etat = models.CharField(
        max_length=20,
        choices=CHOIX_ETAT_PLANIFICATION,
        default="prevue",
    )
    date_prevue = models.DateField(
        validators=[
            validators.MinValueValidator(datetime.date(2026, 11, 1)),
            validators.MaxValueValidator(datetime.date(2026, 12, 20)),
        ],
        help_text="Date prévue entre le 2026-11-01 et le 2026-12-20.",
    )
    convives = models.PositiveIntegerField(
        validators=[
            validators.MinValueValidator(1),
            validators.MaxValueValidator(10),
        ],
        help_text="Nombre de convives entre 1 et 10.",
    )
    # Pas d'auto_now_add / auto_now pour préserver les dates du CSV et contrôler les mises à jour
    date_creation = models.DateTimeField()
    date_modification = models.DateTimeField()

    def __str__(self):
        return f"{self.utilisateur_id} - {self.recette_id} ({self.etat})"