

from django.urls import path
from .views import ConnexionView, InscriptionView

urlpatterns = [
    path("connexion/", ConnexionView.as_view(), name="connexion"),
    path("inscription/", InscriptionView.as_view(), name="inscription"),
]