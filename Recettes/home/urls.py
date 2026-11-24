from django.urls import path
from .views import HomeView, CatalogueView
from django.contrib.auth.views import LogoutView

# Routes de l'application home
urlpatterns = [
    path("", HomeView.as_view(), name="accueil"),
    path("catalogue/", CatalogueView.as_view(), name="catalogue"),
    path("deconnexion/", LogoutView.as_view(), name="deconnexion")
]