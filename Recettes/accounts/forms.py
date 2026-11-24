from django.contrib.auth.forms import UserCreationForm
from accounts.models import Utilisateur


class InscriptionForm(UserCreationForm):
    # Formulaire adapté à notre modele utilisateur
    class Meta(UserCreationForm.Meta):
        model = Utilisateur
        fields = ("username", "regime")