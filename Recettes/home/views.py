
from django.views.generic import ListView, TemplateView
from .models import Recette

# Afficher la page d'accueil
class HomeView(TemplateView):
    template_name = "home/recette_list.html"  # ou le nom de ton fichier d'accueil


# Afficher le catalogue des recettes
class CatalogueView(ListView):
    model = Recette
    template_name = "home/catalogue.html"
    context_object_name = "recettes"

    def get_queryset(self):
        return Recette.objects.filter(etat_publication="publiee")