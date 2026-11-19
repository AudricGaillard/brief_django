import csv
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

# Remplacez 'mon_app' par le nom exact de l'application qui contient models.py
from Recettes.models import Categorie, Ingredient, Planification, Recette, Utilisateur


class Command(BaseCommand):
    """
    Commande  Django permettant de charger les fichiers CSV
    dans la base SQLite sans créer de doublons.
    """

    

    def handle(self):
        """
        Point d'entree execute lors de l'appel : python manage.py charger_donnees
        """
        self.stdout.write(self.style.SUCCESS("=== Début du chargement des données ==="))

        
        # Les modeles utilisent l'ID auto-incremente de Django 
        # et non l'identifiant du CSV, on garde en mémoire le lien :
        # ancien_id_csv -> objet_django_en_base
        categories_par_csv_id = {}
        recettes_par_csv_id = {}
        utilisateurs_par_csv_id = {}

        # =====================================================================
        # 1. CHARGEMENT DES CATÉGORIES (categories.csv)
        # =====================================================================
        chemin_categories = os.path.join(
            settings.BASE_DIR, "donnees", "recettes", "categories.csv"
        )
        self.stdout.write("Chargement des catégories...")

        with open(chemin_categories, mode="r", encoding="utf-8") as fichier:
            lecteur = csv.DictReader(fichier)

            for ligne in lecteur:
                # Dans le CSV, la colonne d'identifiant s'appelle 'identier'
                csv_id = ligne["identier"].strip()
                nom_categorie = ligne["nom"].strip()

                # get_or_create evite de creer deux fois la meme categorie si on relance la commande
                categorie, cree = Categorie.objects.get_or_create(
                    nom=nom_categorie
                )

                # On memorise cette categorie sous son ancien ID CSV pour les recettes
                categories_par_csv_id[csv_id] = categorie

                if cree:
                    self.stdout.write(f"  + Catégorie créée : {categorie.nom}")

        # =====================================================================
        # 2. CHARGEMENT DES RECETTES (objets.csv)
        # =====================================================================
        chemin_recettes = os.path.join(
            settings.BASE_DIR, "donnees", "recettes", "objets.csv"
        )
        self.stdout.write("Chargement des recettes...")

        with open(chemin_recettes, mode="r", encoding="utf-8") as fichier:
            lecteur = csv.DictReader(fichier)

            for ligne in lecteur:
                csv_id = ligne["identier"].strip()
                csv_cat_id = ligne["categorie_identier"].strip()

                # On retrouve l'objet Categorie correspondant grece à notre dictionnaire
                categorie_obj = categories_par_csv_id.get(csv_cat_id)
                if not categorie_obj:
                    # Sécurite : si la categorie n'a pas ete trouvee, on signale et on passe à la suite
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ! Catégorie CSV '{csv_cat_id}' introuvable pour la recette '{ligne['titre']}'."
                        )
                    )
                    continue

                # Dans le CSV, regimes_incompatibles est une chaîne separee par ';'
                # Dans models.py, c'est un JSONField avec default=list -> on convertit donc en liste Python
                regimes_bruts = ligne.get("regimes_incompatibles", "")
                liste_regimes = [
                    r.strip() for r in regimes_bruts.split(";") if r.strip()
                ]

                # get_or_create base sur 'titre' (qui est unique dans models.py)
                recette, cree = Recette.objects.get_or_create(
                    titre=ligne["titre"].strip(),
                    defaults={
                        # Dans ce models.py, le ForeignKey s'appelle 'categorie_id',
                        # mais en ORM Django on lui affecte bien l'instance Categorie
                        "categorie_id": categorie_obj,
                        "temps_preparation_min": int(ligne["temps_preparation_min"]),
                        "temps_cuisson_min": int(ligne.get("temps_cuisson_min") or 0),
                        "portions": int(ligne["portions"]),
                        "difficulte": ligne["difficulte"].strip(),
                        "etat_publication": ligne["etat_publication"].strip(),
                        "etapes": ligne["etapes"].strip(),
                        "regimes_incompatibles": liste_regimes,
                    },
                )

                # On garde le lien ancien ID CSV -> objet Recette pour les ingrédients et planifications
                recettes_par_csv_id[csv_id] = recette

                if cree:
                    self.stdout.write(f"  + Recette créée : {recette.titre}")

        # =====================================================================
        # 3. CHARGEMENT DES INGRÉDIENTS (ingredients.csv)
        # =====================================================================
        chemin_ingredients = os.path.join(
            settings.BASE_DIR, "donnees", "recettes", "ingredients.csv"
        )
        self.stdout.write("Chargement des ingrédients...")

        with open(chemin_ingredients, mode="r", encoding="utf-8") as fichier:
            lecteur = csv.DictReader(fichier)

            for ligne in lecteur:
                csv_recette_id = ligne["recette_identier"].strip()
                recette_obj = recettes_par_csv_id.get(csv_recette_id)

                if not recette_obj:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ! Recette CSV '{csv_recette_id}' introuvable pour l'ingrédient '{ligne['nom']}'."
                        )
                    )
                    continue

                nom_ingredient = ligne["nom"].strip()
                # Conversion  (ex: "2" ou "2.0" -> entier positif)
                quantite_val = int(float(ligne["quantite"]))
                unite_val = ligne["unite"].strip()

                # On verifie si cet ingredient existe deje pour cette recette afin d'éviter les doublons
                ingredient, cree = Ingredient.objects.get_or_create(
                    recette_id=recette_obj,
                    nom=nom_ingredient,
                    defaults={
                        "quantite": quantite_val,
                        "unite": unite_val,
                    },
                )

                if cree:
                    self.stdout.write(
                        f"  + Ingrédient ajouté : {ingredient.nom} ({recette_obj.titre})"
                    )

        # =====================================================================
        # 4. CHARGEMENT DES UTILISATEURS (utilisateurs.csv)
        # =====================================================================
        chemin_utilisateurs = os.path.join(
            settings.BASE_DIR, "donnees", "recettes", "utilisateurs.csv"
        )
        self.stdout.write("Chargement des utilisateurs...")

        with open(chemin_utilisateurs, mode="r", encoding="utf-8") as fichier:
            lecteur = csv.DictReader(fichier)

            for ligne in lecteur:
                csv_id = ligne["identier"].strip()
                email = ligne["email"].strip().lower()

                # On separe "prenom, nom" si la colonne s'appelle 'prenom, nom',
                # ou on lit 'prenom' et 'nom' si ce sont deux colonnes distinctes
                if "prenom, nom" in ligne and ligne["prenom, nom"]:
                    parties = ligne["prenom, nom"].split(",", 1)
                    prenom = parties[0].strip()
                    nom = parties[1].strip() if len(parties) > 1 else ""
                else:
                    prenom = ligne.get("prenom", "").strip()
                    nom = ligne.get("nom", "").strip()

                # Le brief indique que l'adresse e-mail sert d'identifiant de connexion
                # et que les comptes de démo ont le mot de passe 'demo1234'
                utilisateur, cree = Utilisateur.objects.get_or_create(
                    username=email,
                    defaults={
                        "email": email,
                        "first_name": prenom,
                        "last_name": nom,
                        "regime": ligne.get("regime", "").strip(),
                    },
                )

                if cree:
                    # set_password() hache le mot de passe 
                    utilisateur.set_password("demo1234")
                    utilisateur.save()
                    self.stdout.write(f"  + Utilisateur créé : {utilisateur.email}")

                # On memorise l'utilisateur pour lier les planifications
                utilisateurs_par_csv_id[csv_id] = utilisateur

        # =====================================================================
        # 5. CHARGEMENT DES PLANIFICATIONS (actions.csv)
        # =====================================================================
        chemin_actions = os.path.join(
            settings.BASE_DIR, "donnees", "recettes", "actions.csv"
        )
        self.stdout.write("Chargement des planifications...")

        with open(chemin_actions, mode="r", encoding="utf-8") as fichier:
            lecteur = csv.DictReader(fichier)

            for ligne in lecteur:
                csv_user_id = ligne["utilisateur_identier"].strip()
                csv_recette_id = ligne["objet_identier"].strip()

                utilisateur_obj = utilisateurs_par_csv_id.get(csv_user_id)
                recette_obj = recettes_par_csv_id.get(csv_recette_id)

                if not utilisateur_obj or not recette_obj:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ! Planification ignorée (utilisateur '{csv_user_id}' ou recette '{csv_recette_id}' introuvable)."
                        )
                    )
                    continue

                # Conversion de la date 
                date_prevue_obj = parse_date(ligne["date_prevue"].strip())

                # Conversion des dates/heures en datetime du fuseau horaire si nécessaire
                dt_creation = parse_datetime(ligne["date_creation"].strip())
                if dt_creation and timezone.is_naive(dt_creation):
                    dt_creation = timezone.make_aware(dt_creation)

                dt_modification_raw = ligne["date_modification"].strip()
                dt_modification_dt = parse_datetime(dt_modification_raw)
                if dt_modification_dt:
                    if timezone.is_naive(dt_modification_dt):
                        dt_modification_dt = timezone.make_aware(dt_modification_dt)
                    # Dans models.py, date_modification est un DateField
                    date_modif_obj = dt_modification_dt.date()
                else:
                    date_modif_obj = parse_date(dt_modification_raw)

                planif, cree = Planification.objects.get_or_create(
                    utilisateur_id=utilisateur_obj,
                    recette_id=recette_obj,
                    date_prevue=date_prevue_obj,
                    defaults={
                        "etat": ligne["etat"].strip(),
                        "convives": int(ligne["convives"]),
                    },
                )

                # Attention : dans models.py, date_creation et date_modification ont auto_now_add=True.
                
                if cree and dt_creation and date_modif_obj:
                    Planification.objects.filter(pk=planif.pk).update(
                        date_creation=dt_creation,
                        date_modification=date_modif_obj,
                    )
                    self.stdout.write(
                        f"  + Planification créée : {utilisateur_obj.email} -> {recette_obj.titre}"
                    )

        self.stdout.write(self.style.SUCCESS("=== Chargement terminé avec succès ! ==="))