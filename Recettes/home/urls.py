from django.urls import path
from .views import AccueilView
 

# Routes de l'application home
urlpatterns = [
    path("", AccueilView.as_view(), name="accueil"),
]