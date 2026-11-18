import csv
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from Recettes.models import Categorie, Recette, Utilisateur  # Utilisation des classes exactes

class Command(BaseCommand):
    

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


        # =
        # 3. CHARGEMENT DES UTILISATEURS
        # =

        chemin_utilisateurs = os.path.join(settings.BASE_DIR, 'donnees', 'recettes', 'utilisateurs.csv')
        with open(chemin_utilisateurs, mode='r', encoding='utf-8') as fichier:
            lecteur_csv = csv.DictReader(fichier)

            for ligne in lecteur_csv:
                # Verification de l'existence de l'utilisateur
                # Le brief precise que l'email sert souvent de nom d'utilisateur ou d'identifiant unique
                email = ligne['email']

                utilisateur, cree = Utilisateur.objects.get_or_create(
                    email=email,
                    defaults={
                        'username': email,  
                        'prenom': ligne['prenom'],
                        'nom': ligne['nom'],
                        'role': ligne['role'],
                        'regime': ligne.get('regime', '') 
                    }
                )

                if cree:
                    #  mot de passe securise exige : "demo1234"
                    utilisateur.set_password("demo1234")
                    utilisateur.save()
                    print(f"Utilisateur créé : {utilisateur.email} (rôle: {utilisateur.role})")

        self.stdout.write(self.style.SUCCESS("Utilisateurs chargés avec succès !"))





        self.stdout.write(self.style.SUCCESS("--- Chargement termine avec succes ! ---"))