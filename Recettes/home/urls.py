from django.urls import path
from .views import HomeView, CatalogueView

# Routes de l'application home
urlpatterns = [
    path("", HomeView.as_view(), name="accueil"),
    path("catalogue/", CatalogueView.as_view(), name="catalogue"),
]