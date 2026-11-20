from django.urls import path
from .views import ConnexionView, InscriptionView


# Routes pour la connexion et l'inscription
urlpatterns = [path("connexion/", ConnexionViews.as_view(), name="inscription"),
]