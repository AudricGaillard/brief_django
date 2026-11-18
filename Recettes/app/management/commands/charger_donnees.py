import csv
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from Recettes.models import Categorie, Recette  # Utilisation des classes exactes

class Command(BaseCommand):
    help = "Charge les catégories et les recettes depuis les fichiers CSV."

    def handle(self):
        self.stdout.write("--- Debut du chargement des donnees ---")

        # ==========================================
        # 1. CHARGEMENT DES CATEGORIES
        # ==========================================

        chemin_categories = os.path.join(settings.BASE_DIR, 'donnees', 'recettes', 'categories.csv')
        
        with open(chemin_categories, mode='r', encoding='utf-8') as fichier:
            lecteur_csv = csv.DictReader(fichier)
            for ligne in lecteur_csv:
                categorie, cree = Categorie.objects.get_or_create(
                    identifiant=ligne['identier'],
                    defaults={'nom': ligne['nom']}
                )
                if cree:
                    print(f"Catégorie ajoutée : {categorie.nom}")
        
        self.stdout.write(self.style.SUCCESS("Catégories chargées avec succès !"))

        # ==========================================
        # 2. CHARGEMENT DES RECETTES (OBJETS)
        # ==========================================

        chemin_recettes = os.path.join(settings.BASE_DIR, 'donnees', 'recettes', 'objets.csv')

        with open(chemin_recettes, mode='r', encoding='utf-8') as fichier:
            lecteur_csv = csv.DictReader(fichier)
            
            for ligne in lecteur_csv:
                # On recupere la Categorie liee grace à la cle etrangere (categorie_identier)'
                try:
                    categorie_associee = Categorie.objects.get(identifiant=ligne['categorie_identier'])
                except Categorie.DoesNotExist:
                    print(f"La catégorie '{ligne['categorie_identier']}' est introuvable pour la recette '{ligne['titre']}'.")
                    continue 

                # Insertion ou récupération de la recette (idempotence)
                recette, cree = Recette.objects.get_or_create(
                    identifiant=ligne['identier'],
                    defaults={
                        'titre': ligne['titre'],
                        'categorie': categorie_associee,
                        'temps_preparation_min': int(ligne['temps_preparation_min']),
                        'temps_cuisson_min': int(ligne['temps_cuisson_min']),
                        'portions': int(ligne['portions']),
                        'difficulte': ligne['difficulte'],
                        'etat_publication': ligne['etat_publication'],
                        'etapes': ligne['etapes'],
                        'regimes_incompatibles': ligne.get('regimes_incompatibles', '')
                    }
                )

                if cree:
                    print(f"Recette ajoutée : {recette.titre}")

        self.stdout.write(self.style.SUCCESS("Recettes chargees avec succes !"))
        self.stdout.write(self.style.SUCCESS("--- Chargement termine avec succes ! ---"))