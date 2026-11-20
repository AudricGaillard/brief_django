from django.views.generic import ListView
from django.shortcuts import render
from .models import Categorie, Recette, Role

# Create your views here.
class ListRecipesView(ListView):
    model=Recette
    template_name='app/accueil.html'
    context_object_name = 'recettes'
