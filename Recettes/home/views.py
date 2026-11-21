from django.views.generic import ListView

# Afficher la page d'accueil
from django.views.generic import ListView
from .models import Recette

# Create your views here.
class ListRecipesView(ListView):
    model=Recette
    template_name='recette_list.html'
    context_object_name = 'recettes'