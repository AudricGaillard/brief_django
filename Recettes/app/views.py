from django.views.generic import TemplateView


# Afficher la page d'accueil
class AccueilView(TemplateView):
    template_name = "accueil.html"
