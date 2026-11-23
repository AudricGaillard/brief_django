
from django.urls import path
from .views import (
    CatalogueView,
    HomeView,
    MesDemandesView,
    PlanificationCreateView,
    RecetteDetailView,
)




urlpatterns = [
    path("", HomeView.as_view(), name="accueil"),
    path("catalogue/", CatalogueView.as_view(), name="catalogue"),
    path("catalogue/<int:pk>/", RecetteDetailView.as_view(), name="recette_detail"),
    path("catalogue/<int:pk>/demande/", PlanificationCreateView.as_view(), name="planification_create"),
    path("mes-demandes/", MesDemandesView.as_view(), name="mes_demandes"),
]