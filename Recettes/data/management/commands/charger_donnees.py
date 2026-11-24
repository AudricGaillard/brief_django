import csv
from decimal import Decimal, InvalidOperation
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from accounts.models import Utilisateur
from home.models import Categorie, Ingredient, Planification, Recette


def lire_colonne(ligne, *noms_possibles, defaut=""):
    """Récupère la valeur d'une colonne CSV en testant plusieurs noms possibles."""
    for nom in noms_possibles:
        if nom in ligne and ligne[nom] is not None:
            return ligne[nom].strip()
    return defaut


def parse_decimal_safe(valeur_brute, defaut=Decimal("1.00")):
    """Convertit une chaîne numérique (ex. '0.5', '1,5', '2') en Decimal."""
    if not valeur_brute:
        return defaut
    nettoyee = valeur_brute.replace(",", ".").strip()
    try:
        return Decimal(nettoyee)
    except InvalidOperation:
        return defaut


def parse_aware_datetime(valeur_brute):
    """Parse une date/heure ISO et la rend 'aware' selon le fuseau Django si nécessaire."""
    if not valeur_brute:
        return None
    dt = parse_datetime(valeur_brute)
    if dt is None:
        d = parse_date(valeur_brute)
        if d is None:
            return None
        dt = timezone.datetime.combine(d, timezone.datetime.min.time())
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


class Command(BaseCommand):
    """Charge les données CSV dans SQLite de manière relançable (sans doublons)."""

    help = "Charge catégories, recettes, ingrédients, utilisateurs et planifications depuis les CSV."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Début du chargement des données ==="))

        categories_par_csv_id = {}
        recettes_par_csv_id = {}
        utilisateurs_par_csv_id = {}

        dossier_donnees = os.path.join(settings.BASE_DIR.parent, "donnees")
        
        # ---------------------------------------------------------------------
        # 1. CATÉGORIES (categories.csv)
        # ---------------------------------------------------------------------
        chemin_categories = os.path.join(dossier_donnees, "categories.csv")
        self.stdout.write("Chargement des catégories...")

        

        with open(chemin_categories, mode="r", encoding="utf-8-sig") as fichier:
            for ligne in csv.DictReader(fichier):
                csv_id = lire_colonne(ligne, "id", "identier")
                nom_categorie = lire_colonne(ligne, "nom")
                if not nom_categorie:
                    continue

                categorie, cree = Categorie.objects.update_or_create(
                    nom=nom_categorie,
                    defaults={},
                )
                if csv_id:
                    categories_par_csv_id[csv_id] = categorie
                if cree:
                    self.stdout.write(f"  + Catégorie créée : {categorie.nom}")

        # ---------------------------------------------------------------------
        # 2. RECETTES (objets.csv)
        # ---------------------------------------------------------------------
        chemin_objets = os.path.join(dossier_donnees, "objets.csv")
        self.stdout.write("Chargement des recettes...")

        with open(chemin_objets, mode="r", encoding="utf-8-sig") as fichier:
            for ligne in csv.DictReader(fichier):
                csv_id = lire_colonne(ligne, "id", "identier")
                csv_cat_id = lire_colonne(ligne, "categorie_id", "categorie_identier")
                titre_recette = lire_colonne(ligne, "titre")

                categorie_obj = categories_par_csv_id.get(csv_cat_id)
                if not categorie_obj or not titre_recette:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ! Recette ignorée '{titre_recette}' (catégorie '{csv_cat_id}' introuvable ou titre vide)."
                        )
                    )
                    continue

                regimes_bruts = lire_colonne(ligne, "regimes_incompatibles")
                liste_regimes = [
                    r.strip() for r in regimes_bruts.split(";") if r.strip()
                ]

                prep_min = int(lire_colonne(ligne, "temps_preparation_min", defaut="1") or 1)
                cuisson_min = int(lire_colonne(ligne, "temps_cuisson_min", defaut="0") or 0)
                portions = int(lire_colonne(ligne, "portions", defaut="1") or 1)
                difficulte = lire_colonne(ligne, "difficulte", defaut="facile")
                etat_pub = lire_colonne(ligne, "etat_publication", defaut="brouillon")
                etapes = lire_colonne(ligne, "etapes")

                recette, cree = Recette.objects.update_or_create(
                    titre=titre_recette,
                    defaults={
                        "categorie_id": categorie_obj,
                        "temps_preparation_min": max(1, prep_min),
                        "temps_cuisson_min": max(0, cuisson_min),
                        "portions": max(1, portions),
                        "difficulte": difficulte,
                        "etat_publication": etat_pub,
                        "etapes": etapes,
                        "regimes_incompatibles": liste_regimes,
                    },
                )
                if csv_id:
                    recettes_par_csv_id[csv_id] = recette
                if cree:
                    self.stdout.write(f"  + Recette créée : {recette.titre}")

        # ---------------------------------------------------------------------
        # 3. INGRÉDIENTS (ingredients.csv)
        # ---------------------------------------------------------------------
        chemin_ingredients = os.path.join(dossier_donnees, "ingredients.csv")
        self.stdout.write("Chargement des ingrédients...")

        with open(chemin_ingredients, mode="r", encoding="utf-8-sig") as fichier:
            for ligne in csv.DictReader(fichier):
                csv_recette_id = lire_colonne(ligne, "recette_id", "recette_identier")
                recette_obj = recettes_par_csv_id.get(csv_recette_id)
                nom_ingredient = lire_colonne(ligne, "nom")

                if not recette_obj or not nom_ingredient:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ! Ingrédient ignoré '{nom_ingredient}' (recette '{csv_recette_id}' introuvable ou nom vide)."
                        )
                    )
                    continue

                quantite_val = parse_decimal_safe(
                    lire_colonne(ligne, "quantite", defaut="1"),
                    defaut=Decimal("1.00"),
                )
                if quantite_val <= 0:
                    quantite_val = Decimal("0.01")

                unite_val = lire_colonne(ligne, "unite", defaut="g")

                ingredient, cree = Ingredient.objects.update_or_create(
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

        # ---------------------------------------------------------------------
        # 4. UTILISATEURS (utilisateurs.csv)
        # ---------------------------------------------------------------------
        chemin_utilisateurs = os.path.join(dossier_donnees, "utilisateurs.csv")
        self.stdout.write("Chargement des utilisateurs...")

        roles_valides = {"utilisateur", "gestionnaire"}

        with open(chemin_utilisateurs, mode="r", encoding="utf-8-sig") as fichier:
            for ligne in csv.DictReader(fichier):
                csv_id = lire_colonne(ligne, "id", "identier")
                email = lire_colonne(ligne, "email").lower()
                prenom = lire_colonne(ligne, "prenom", "first_name")
                nom = lire_colonne(ligne, "nom", "last_name")
                identifiant = lire_colonne(ligne, "username") or email

                if not identifiant:
                    continue

                role_brut = lire_colonne(ligne, "role", "type_compte", defaut="utilisateur").lower()
                role_valide = role_brut if role_brut in roles_valides else "utilisateur"

                regime_brut = lire_colonne(ligne, "regime")
                regime_val = regime_brut if regime_brut else None

                utilisateur, cree = Utilisateur.objects.get_or_create(
                    username=identifiant,
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
                    # On met à jour les métadonnées sans écraser le mot de passe existant
                    utilisateur.email = email or utilisateur.email
                    utilisateur.first_name = prenom or utilisateur.first_name
                    utilisateur.last_name = nom or utilisateur.last_name
                    utilisateur.role = role_valide
                    utilisateur.regime = regime_val
                    utilisateur.save()

                if csv_id:
                    utilisateurs_par_csv_id[csv_id] = utilisateur

        # ---------------------------------------------------------------------
        # 5. PLANIFICATIONS (actions.csv)
        # ---------------------------------------------------------------------
        chemin_actions = os.path.join(dossier_donnees, "actions.csv")
        self.stdout.write("Chargement des planifications...")

        maintenant = timezone.now()

        with open(chemin_actions, mode="r", encoding="utf-8-sig") as fichier:
            for ligne in csv.DictReader(fichier):
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
                if not date_prevue_obj:
                    self.stdout.write(
                        self.style.WARNING("  ! Planification ignorée : date_prevue invalide.")
                    )
                    continue

                dt_creation = parse_aware_datetime(lire_colonne(ligne, "date_creation")) or maintenant
                dt_modification = (
                    parse_aware_datetime(lire_colonne(ligne, "date_modification")) or dt_creation
                )

                etat_val = lire_colonne(ligne, "etat", defaut="prevue")
                convives_val = int(lire_colonne(ligne, "convives", defaut="1") or 1)
                convives_val = max(1, min(10, convives_val))

                planif, cree = Planification.objects.update_or_create(
                    utilisateur_id=utilisateur_obj,
                    recette_id=recette_obj,
                    date_prevue=date_prevue_obj,
                    defaults={
                        "etat": etat_val,
                        "convives": convives_val,
                        "date_creation": dt_creation,
                        "date_modification": dt_modification,
                    },
                )

                # Réapplique explicitement date_creation et date_modification pour garantir
                # la conservation exacte des horodatages du CSV même en cas de mise à jour.
                Planification.objects.filter(pk=planif.pk).update(
                    date_creation=dt_creation,
                    date_modification=dt_modification,
                )

                if cree:
                    self.stdout.write(
                        f"  + Planification créée : {utilisateur_obj.username} -> {recette_obj.titre}"
                    )

        self.stdout.write(self.style.SUCCESS("=== Chargement terminé avec succès ! ==="))