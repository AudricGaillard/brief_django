from django.urls import path
from .views import ListRecipesView
 

# Routes de l'application home
urlpatterns = [
    path("", ListRecipesView.as_view(), name="accueil"),
]