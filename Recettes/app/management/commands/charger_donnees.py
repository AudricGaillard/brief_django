import csv
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from app.models import Categorie, Ingredient, Planification, Recette, Utilisateur


def lire_colonne(ligne, *noms_possibles, defaut=""):
    """
    Récupère la valeur d'une colonne CSV en testant plusieurs noms possible.
    """
    for nom in noms_possibles:
        if nom in ligne and ligne[nom] is not None:
            return ligne[nom].strip()
    return defaut


class Command(BaseCommand):
    """
    Commande Django permettant de charger les fichiers CSV
    dans la base SQLite  (sans créer de doublons).
    """

    

    def handle(self, *args, **options):
        """
        Point d'entrée exécuté lors de l'appel : python manage.py charger_donnees
        """
        self.stdout.write(self.style.SUCCESS("=== Début du chargement des données ==="))

        # Dictionnaires de correspondance : ancien_id_csv -> objet_django_en_base
        categories_par_csv_id = {}
        recettes_par_csv_id = {}
        utilisateurs_par_csv_id = {}

        # Dossier commun contenant les CSV 
        dossier_donnees = os.path.join(settings.BASE_DIR.parent, "donnees", "recettes")

        # =====================================================================
        # 1. CHARGEMENT DES CATÉGORIES (categories.csv)
        # =====================================================================
        chemin_categories = os.path.join(dossier_donnees, "categories.csv")
        self.stdout.write("Chargement des catégories...")

        with open(chemin_categories, mode="r", encoding="utf-8-sig") as fichier:
            lecteur = csv.DictReader(fichier)

            for ligne in lecteur:
                # L'en-tête réel de categories.csv est 'id,nom'
                csv_id = lire_colonne(ligne, "id", "identier")
                nom_categorie = lire_colonne(ligne, "nom")

                if not nom_categorie:
                    continue

                # get_or_create évite les doublons si on relance la commande
                categorie, cree = Categorie.objects.get_or_create(
                    nom=nom_categorie
                )

                if csv_id:
                    categories_par_csv_id[csv_id] = categorie

                if cree:
                    self.stdout.write(f"  + Catégorie créée : {categorie.nom}")

        # =====================================================================
        # 2. CHARGEMENT DES RECETTES (objets.csv)
        # =====================================================================
        chemin_objets = os.path.join(dossier_donnees, "objets.csv")
        self.stdout.write("Chargement des recettes...")

        with open(chemin_objets, mode="r", encoding="utf-8-sig") as fichier:
            lecteur = csv.DictReader(fichier)

            for ligne in lecteur:
                csv_id = lire_colonne(ligne, "id", "identier")
                csv_cat_id = lire_colonne(ligne, "categorie_id", "categorie_identier")
                titre_recette = lire_colonne(ligne, "titre")

                categorie_obj = categories_par_csv_id.get(csv_cat_id)
                if not categorie_obj:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ! Catégorie CSV '{csv_cat_id}' introuvable pour '{titre_recette}'."
                        )
                    )
                    continue

                # Conversion de la chaîne séparée par ';' en liste Python 
                regimes_bruts = lire_colonne(ligne, "regimes_incompatibles")
                liste_regimes = [
                    r.strip() for r in regimes_bruts.split(";") if r.strip()
                ]

                cuisson_raw = lire_colonne(ligne, "temps_cuisson_min", defaut="0")

                recette, cree = Recette.objects.get_or_create(
                    titre=titre_recette,
                    defaults={
                        "categorie_id": categorie_obj,
                        "temps_preparation_min": int(lire_colonne(ligne, "temps_preparation_min", defaut="1")),
                        "temps_cuisson_min": int(cuisson_raw or 0),
                        "portions": int(lire_colonne(ligne, "portions", defaut="1")),
                        "difficulte": lire_colonne(ligne, "difficulte"),
                        "etat_publication": lire_colonne(ligne, "etat_publication"),
                        "etapes": lire_colonne(ligne, "etapes"),
                        "regimes_incompatibles": liste_regimes,
                    },
                )

                if csv_id:
                    recettes_par_csv_id[csv_id] = recette

                if cree:
                    self.stdout.write(f"  + Recette créée : {recette.titre}")

        # =====================================================================
        # 3. CHARGEMENT DES INGRÉDIENTS (ingredients.csv)
        # =====================================================================
        chemin_ingredients = os.path.join(dossier_donnees, "ingredients.csv")
        self.stdout.write("Chargement des ingrédients...")

        with open(chemin_ingredients, mode="r", encoding="utf-8-sig") as fichier:
            lecteur = csv.DictReader(fichier)

            for ligne in lecteur:
                csv_recette_id = lire_colonne(ligne, "recette_id", "recette_identier")
                recette_obj = recettes_par_csv_id.get(csv_recette_id)

                nom_ingredient = lire_colonne(ligne, "nom")
                if not recette_obj:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ! Recette CSV '{csv_recette_id}' introuvable pour l'ingrédient '{nom_ingredient}'."
                        )
                    )
                    continue

                quantite_val = int(float(lire_colonne(ligne, "quantite", defaut="1")))
                unite_val = lire_colonne(ligne, "unite")

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
        chemin_utilisateurs = os.path.join(dossier_donnees, "utilisateurs.csv")
        self.stdout.write("Chargement des utilisateurs...")

        roles_valides = {"utilisateur", "gestionnaire"}

        with open(chemin_utilisateurs, mode="r", encoding="utf-8-sig") as fichier:
            lecteur = csv.DictReader(fichier)

            for ligne in lecteur:
                csv_id = lire_colonne(ligne, "id", "identier")
                email = lire_colonne(ligne, "email").lower()

                prenom_nom_combine = lire_colonne(ligne, "prenom, nom")
                if prenom_nom_combine:
                    parties = prenom_nom_combine.split(",", 1)
                    prenom = parties[0].strip()
                    nom = parties[1].strip() if len(parties) > 1 else ""
                else:
                    prenom = lire_colonne(ligne, "prenom", "first_name")
                    nom = lire_colonne(ligne, "nom", "last_name")

                identifiant_connexion = lire_colonne(ligne, "username") or email
                if not identifiant_connexion:
                    continue

                # Lecture et normalisation du rôle (par défaut : "utilisateur")
                role_brut = lire_colonne(ligne, "role", "type_compte", defaut="utilisateur").lower()
                role_valide = role_brut if role_brut in roles_valides else "utilisateur"

                # Lecture de l'information propre au thème (peut être vide pour un gestionnaire)
                regime_brut = lire_colonne(ligne, "regime")
                regime_val = regime_brut if regime_brut else None

                utilisateur, cree = Utilisateur.objects.get_or_create(
                    username=identifiant_connexion,
                    defaults={
                        "email": email,
                        "first_name": prenom,
                        "last_name": nom,
                        "role": role_valide,
                        "regime": regime_val,
                    },
                )

                if cree:
                    utilisateur.set_password("demo1234")
                    utilisateur.save()
                    self.stdout.write(
                        f"  + Utilisateur créé : {utilisateur.username} ({utilisateur.role})"
                    )
                else:
                    # Mise à jour si le rôle ou le régime a changé dans le CSV
                    modifie = False
                    if utilisateur.role != role_valide:
                        utilisateur.role = role_valide
                        modifie = True
                    if utilisateur.regime != regime_val:
                        utilisateur.regime = regime_val
                        modifie = True
                    if modifie:
                        utilisateur.save()
                        self.stdout.write(
                            f"  ~ Utilisateur mis à jour : {utilisateur.username} ({utilisateur.role})"
                        )

                if csv_id:
                    utilisateurs_par_csv_id[csv_id] = utilisateur

        # =====================================================================
        # 5. CHARGEMENT DES PLANIFICATIONS (actions.csv)
        # =====================================================================
        chemin_actions = os.path.join(dossier_donnees, "actions.csv")
        self.stdout.write("Chargement des planifications...")

        with open(chemin_actions, mode="r", encoding="utf-8-sig") as fichier:
            lecteur = csv.DictReader(fichier)

            for ligne in lecteur:
                

                csv_user_id = lire_colonne(ligne, "utilisateur_id", "utilisateur_identier")
                csv_recette_id = lire_colonne(ligne, "objet_id", "recette_id", "objet_identier")

                utilisateur_obj = utilisateurs_par_csv_id.get(csv_user_id)
                recette_obj = recettes_par_csv_id.get(csv_recette_id)

                if not utilisateur_obj or not recette_obj:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ! Planification ignorée (utilisateur '{csv_user_id}' ou recette '{csv_recette_id}' introuvable)."
                        )
                    )
                    continue

                date_prevue_obj = parse_date(lire_colonne(ligne, "date_prevue"))

                dt_creation = parse_datetime(lire_colonne(ligne, "date_creation"))
                if dt_creation and timezone.is_naive(dt_creation):
                    dt_creation = timezone.make_aware(dt_creation)

                dt_modification_raw = lire_colonne(ligne, "date_modification")
                dt_modification_dt = parse_datetime(dt_modification_raw)
                if dt_modification_dt:
                    if timezone.is_naive(dt_modification_dt):
                        dt_modification_dt = timezone.make_aware(dt_modification_dt)
                    date_modif_obj = dt_modification_dt.date()
                else:
                    date_modif_obj = parse_date(dt_modification_raw)

                planif, cree = Planification.objects.get_or_create(
                    utilisateur_id=utilisateur_obj,
                    recette_id=recette_obj,
                    date_prevue=date_prevue_obj,
                    defaults={
                        "etat": lire_colonne(ligne, "etat"),
                        "convives": int(lire_colonne(ligne, "convives", defaut="1")),
                    },
                )

                if cree and dt_creation and date_modif_obj:
                    Planification.objects.filter(pk=planif.pk).update(
                        date_creation=dt_creation,
                        date_modification=date_modif_obj,
                    )
                    self.stdout.write(
                        f"  + Planification créée : {utilisateur_obj.username} -> {recette_obj.titre}"
                    )

        self.stdout.write(self.style.SUCCESS("=== Chargement terminé avec succès ! ==="))
        