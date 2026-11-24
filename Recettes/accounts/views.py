from django.contrib.auth.views import LoginView
from .forms import InscriptionForm
from django.views.generic import CreateView
from django.urls import reverse_lazy

# Afficher le formulaire de connexion
class ConnexionView(LoginView):
    template_name = "accounts/connexion.html"


# Afficher le formulaire d'inscription
class InscriptionView(CreateView):
    form_class = InscriptionForm
    template_name = "accounts/inscription.html"
    success_url = reverse_lazy("connexion")