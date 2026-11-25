from django.contrib.auth.views import LoginView
from .forms import InscriptionForm
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from home.models import  Recette
from django.views.generic import  ListView


# Afficher le formulaire de connexion
class ConnexionView(LoginView):
    template_name = "accounts/connexion.html"


# Afficher le formulaire d'inscription
class InscriptionView(CreateView):
    form_class = InscriptionForm
    template_name = "accounts/inscription.html"
    success_url = reverse_lazy("connexion")


class RechercheRecetteView(LoginRequiredMixin, ListView):
    model = Recette
    template_name = "home/recherche_recettes.html"
    context_object_name = "recettes"

    def get_queryset(self):
        queryset = Recette.objects.filter(etat_publication="publiee").select_related("categorie_id")
        query = self.request.GET.get("q", "").strip()

        if query:
            mots = query.split()
            for mot in mots:
                queryset = queryset.filter(
                    Q(titre__icontains=mot)
                    | Q(etapes__icontains=mot)
                    | Q(categorie_id__nom__icontains=mot)
                )
            queryset = queryset.distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context  