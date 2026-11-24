# Mes Recettes — Application de gestion (Django)

Application web développée avec **Django** (architecture Modèle-Vue-Template et ORM) pour le thème **carnet de recettes** : consultation d'un catalogue de recettes publiées, gestion de comptes (`utilisateur` et `gestionnaire`), planification de repas au prorata des convives avec contrôle de compatibilité alimentaire, et suivi/gestion des états.

> **Périmètre :** Le projet couvre l'ensemble des fonctionnalités obligatoires du socle (sans fonctionnalités bonus).

---

## Équipe 

- **Équipe :** *Kataryna, Audric et Xavier*

---

## Structure du dépôt

Le dépôt sépare les données fournies, la documentation/livrables et le projet Django :

```text
brief_django/
├── docs/                  # Schéma de base de données et scénario de vérification
├── donnees/
│   └── recettes/          # Jeu de données CSV (non modifié) et script de contrôle
│       ├── actions.csv
│       ├── categories.csv
│       ├── ingredients.csv
│       ├── objets.csv
│       ├── utilisateurs.csv
│       ├── README.md
│       └── verifier_donnees.py
├── Recettes/              # Projet Django (contient manage.py et db.sqlite3)
│   ├── accounts/          # Authentification, inscription et profils/rôles
│   ├── app/               # Application applicative
│   ├── data/              # Commande de gestion charger_donnees
│   │   └── management/
│   ├── home/              # Page d'accueil et catalogue
│   ├── recettes/          # Modèles recettes/ingrédients/planifications et gestion
│   ├── static/            # Fichiers statiques (CSS, etc.)
│   ├── templates/         # Gabarit commun (base.html)
│   └── manage.py
├── .env.example           # Modèle de variables d'environnement (le .env est exclu de Git)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Installation et exécution en local

> Adapte l'activation de l'environnement virtuel (`.venv` ou `venv`) .

### 1. Environnement et dépendances
```bash
# Exemple sous Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configuration de l'environnement (`.env`)
Crée un fichier `.env` (exclu de Git via `.gitignore`) contenant au minimum :
- `SECRET_KEY` : clé secrète Django ;
- `DEBUG` : `True` en développement ou `False` en mode vérifié avec `ALLOWED_HOSTS` configuré et fichiers statiques servis proprement.

### 3. Vérification des données CSV, migrations et chargement
```bash
# Contrôle de cohérence des CSV fournis
python donnees/recettes/verifier_donnees.py

# Migrations et chargement rejouable de la base SQLite
cd Recettes
python manage.py makemigrations
python manage.py migrate
python manage.py charger_donnees
```

- La commande `charger_donnees` lit les CSV dans l'ordre des dépendances (`categories.csv` → `objets.csv` → `ingredients.csv` → `utilisateurs.csv` → `actions.csv`), hache les mots de passe via l'API Django (`demo1234` pour les 20 comptes de démonstration), conserve les dates des fichiers (sans les écraser automatiquement) et reste relançable sans créer de doublons.

### 4. Lancement du serveur
```bash
python manage.py runserver
```

---

## Fonctionnalités, routes et règles métier

### Pages et routes imposées
- `/` : Accueil présentant le service, une sélection de recettes du catalogue et l'accès à l'inscription / connexion.
- `/catalogue/` : Catalogue des recettes publiées avec recherche par mot-clé et filtre par catégorie.
- `/catalogue/<id>/` : Détail d'une recette (ingrédients, étapes, régimes incompatibles, action de planification pour utilisateur connecté).
- `/catalogue/<id>/demande/` : Création d'une planification de repas (réservée aux utilisateurs connectés ; utilisateur, recette et état initial gérés côté serveur).
- `/mes-demandes/` : Planifications de l'utilisateur connecté et actions autorisées selon l'état (`prevue` → `cuisinee` si la date prévue est atteinte ou passée, ou `prevue` → `annulee`).
- `/gestion/` : Espace réservé aux `gestionnaire` (liste des planifications les plus récentes en premier, transitions d'état autorisées, et publication / dépublication des recettes).
- `/inscription/`, `/connexion/`, `/deconnexion/` : Gestion des comptes et sessions.

*(Les routes protégées redirigent les anonymes vers la connexion et renvoient une erreur `403` si le rôle ne correspond pas).*

### Règles métier clés
- **Prorata des convives :** Les quantités d'ingrédients sont recalculées selon `quantite × convives / portions` lors de l'affichage d'une planification.
- **Avertissement de régime alimentaire :** Si la recette est incompatible avec le régime de l'utilisateur (`vegetarien`, `vegan`, `sans_gluten`, `sans_lactose`), un avertissement explicite est affiché et exige une confirmation avant enregistrement.
- **Transitions et droits :** Seules les recettes `publiee` sont visibles dans le catalogue ; dépublier une recette (`publiee` → `brouillon`) conserve les planifications existantes mais bloque les nouvelles.

---

## Choix techniques et justifications

*À compléter:*

- **Découpage en applications Django (`accounts`, `home`, `recettes`, `data`, `app`) :** *[Ex. : sépare la gestion des comptes et rôles de la logique métier des recettes et des planifications afin de garder des vues et modèles lisibles.]*
- **Représentation du rôle et de l'information propre au compte (`role` et `regime`) :** *[À compléter : modèle de profil lié à l'utilisateur ou modèle utilisateur étendu, et gestion des droits côté serveur.]*
- **Contrôle des transitions d'état et règles métier :** *[À compléter : validation côté serveur dans les vues/formulaires/modèles pour bloquer les transitions interdites et vérifier la date avant passage à `cuisinee`.]*
- **Commande `charger_donnees` relançable et conservation des dates :** *[À compléter : clé de rapprochement/unicité et affectation explicite des dates plutôt que `auto_now` / `auto_now_add`.]*