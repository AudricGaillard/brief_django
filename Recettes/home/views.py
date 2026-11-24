from decimal import Decimal

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from .models import Categorie, Planification, Recette, Ingredient


class HomeView(TemplateView):
    template_name = "home/recette_list.html"


class CatalogueView(ListView):
    model = Recette
    template_name = "home/catalogue.html"
    context_object_name = "recettes"

    def get_queryset(self):
        queryset = Recette.objects.filter(etat_publication="publiee").select_related("categorie_id")

        recherche = self.request.GET.get("q", "").strip()
        categorie_id = self.request.GET.get("categorie", "").strip()

        if recherche:
            queryset = queryset.filter(
                Q(titre__icontains=recherche) | Q(ingredients__nom__icontains=recherche)
            ).distinct()

        if categorie_id.isdigit():
            queryset = queryset.filter(categorie_id=int(categorie_id))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Categorie.objects.all()
        context["recherche"] = self.request.GET.get("q", "").strip()
        context["categorie_selectionnee"] = self.request.GET.get("categorie", "").strip()
        return context


class RecetteDetailView(DetailView):
    model = Recette
    template_name = "home/recette_detail.html"
    context_object_name = "recette"

    def get_queryset(self):
        base_qs = Recette.objects.select_related("categorie_id").prefetch_related("ingredients")
        return base_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recette = self.object

        categorie = Categorie.objects.get(id = recette.categorie_id_id)
        context['categorie'] = categorie.nom.capitalize()

        context["etapes_liste"] = [
            etape.strip() for etape in (recette.etapes or "").split("|") if etape.strip()
        ]

        ingredients = Ingredient.objects.all()
        ingredients_recettes = ingredients.filter(recette_id_id = recette.id)
        context['ingredients']=[
           {'nom':ingredient.nom.capitalize(), 'quantite':int(ingredient.quantite), 'unite':ingredient.unite} for ingredient in ingredients_recettes
        ]

        regime_utilisateur = (
            getattr(self.request.user, "regime", None)
            if self.request.user.is_authenticated
            else None
        )
        incompatibles = recette.regimes_incompatibles or []

        context["regime_incompatible"] = bool(
            regime_utilisateur and regime_utilisateur in incompatibles
        )

        context["peut_planifier"] = (
            self.request.user.is_authenticated and recette.etat_publication == "publiee"
        )
        return context


class PlanificationForm(forms.ModelForm):
    confirmer_regime = forms.BooleanField(
        required=False,
        label="Je confirme vouloir planifier cette recette malgré l'incompatibilité avec mon régime.",
    )

    class Meta:
        model = Planification
        fields = ["date_prevue", "convives"]
        widgets = {
            "date_prevue": forms.DateInput(attrs={"type": "date"}),
        }


class PlanificationCreateView(LoginRequiredMixin, View):
    template_name = "home/planification_form.html"

    def get_recette_publiee(self, pk):
        recette = get_object_or_404(Recette, pk=pk)
        if recette.etat_publication != "publiee":
            raise PermissionDenied("Cette recette n'est pas disponible à la planification.")
        return recette

    def get(self, request, pk):
        recette = self.get_recette_publiee(pk)
        form = PlanificationForm(initial={"convives": recette.portions})
        regime_utilisateur = getattr(request.user, "regime", None)
        incompatibles = recette.regimes_incompatibles or []
        regime_incompatible = bool(regime_utilisateur and regime_utilisateur in incompatibles)

        return render(
            request,
            self.template_name,
            {
                "recette": recette,
                "form": form,
                "regime_incompatible": regime_incompatible,
                "regime_utilisateur": regime_utilisateur,
            },
        )

    def post(self, request, pk):
        recette = self.get_recette_publiee(pk)
        form = PlanificationForm(request.POST)
        regime_utilisateur = getattr(request.user, "regime", None)
        incompatibles = recette.regimes_incompatibles or []
        regime_incompatible = bool(regime_utilisateur and regime_utilisateur in incompatibles)

        if form.is_valid():
            confirme = form.cleaned_data.get("confirmer_regime", False)
            if regime_incompatible and not confirme:
                messages.warning(
                    request,
                    f"Attention : cette recette est incompatible avec le régime '{regime_utilisateur}'. "
                    "Cochez la case de confirmation pour valider tout de même la demande.",
                )
                return render(
                    request,
                    self.template_name,
                    {
                        "recette": recette,
                        "form": form,
                        "regime_incompatible": regime_incompatible,
                        "regime_utilisateur": regime_utilisateur,
                    },
                )

            maintenant = timezone.now()
            planification = form.save(commit=False)
            planification.utilisateur_id = request.user
            planification.recette_id = recette
            planification.etat = "prevue"
            planification.date_creation = maintenant
            planification.date_modification = maintenant
            planification.save()

            messages.success(request, "Votre planification a bien été enregistrée.")
            return redirect("mes_demandes")

        return render(
            request,
            self.template_name,
            {
                "recette": recette,
                "form": form,
                "regime_incompatible": regime_incompatible,
                "regime_utilisateur": regime_utilisateur,
            },
        )


class MesDemandesView(LoginRequiredMixin, View):
    template_name = "home/mes_demandes.html"

    def get(self, request):
        planifications = (
            Planification.objects.filter(utilisateur_id=request.user)
            .select_related("recette_id", "recette_id__categorie_id")
            .prefetch_related("recette_id__ingredients")
            .order_by("-date_creation")
        )

        aujourd_hui = timezone.localdate()
        demandes_enrichies = []

        for planif in planifications:
            recette = planif.recette_id
            portions_base = Decimal(str(recette.portions or 1))
            convives_demandes = Decimal(str(planif.convives or 1))
            ratio = convives_demandes / portions_base

            ingredients_ajustes = []
            for ing in recette.ingredients.all():
                quantite_calculee = (ing.quantite * ratio).quantize(Decimal("0.01"))
                ingredients_ajustes.append(
                    {
                        "nom": ing.nom,
                        "unite": ing.unite,
                        "quantite_base": ing.quantite,
                        "quantite_ajustee": quantite_calculee,
                    }
                )

            peut_marquer_cuisinee = (
                planif.etat == "prevue" and aujourd_hui >= planif.date_prevue
            )
            peut_annuler = planif.etat == "prevue"

            demandes_enrichies.append(
                {
                    "planification": planif,
                    "recette": recette,
                    "ingredients_ajustes": ingredients_ajustes,
                    "peut_marquer_cuisinee": peut_marquer_cuisinee,
                    "peut_annuler": peut_annuler,
                }
            )

        return render(
            request,
            self.template_name,
            {
                "demandes_enrichies": demandes_enrichies,
                "aujourd_hui": aujourd_hui,
            },
        )

    def post(self, request):
        planif_id = request.POST.get("planification_id")
        action = request.POST.get("action")

        planif = get_object_or_404(
            Planification, pk=planif_id, utilisateur_id=request.user
        )

        if planif.etat != "prevue":
            messages.error(
                request,
                "Cette planification est déjà finalisée et ne peut plus changer d'état.",
            )
            return redirect("mes_demandes")

        if action == "marquer_cuisinee":
            if timezone.localdate() < planif.date_prevue:
                messages.error(
                    request,
                    "Vous ne pouvez marquer cette recette comme cuisinée avant sa date prévue.",
                )
                return redirect("mes_demandes")
            planif.etat = "cuisinee"
            planif.date_modification = timezone.now()
            planif.save(update_fields=["etat", "date_modification"])
            messages.success(request, "La planification a été marquée comme cuisinée.")

        elif action == "annuler":
            planif.etat = "annulee"
            planif.date_modification = timezone.now()
            planif.save(update_fields=["etat", "date_modification"])
            messages.success(request, "La planification a été annulée.")

        else:
            messages.error(request, "Action non reconnue.")

        return redirect("mes_demandes")

class GestionView(LoginRequiredMixin, View):
    template_name = "home/gestion.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if getattr(request.user, "role", None) != "gestionnaire":
            raise PermissionDenied("Accès réservé aux gestionnaires.")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        planifications = (
            Planification.objects.select_related("utilisateur_id", "recette_id")
            .order_by("-date_creation")
        )
        recettes = Recette.objects.select_related("categorie_id").order_by("titre")
        aujourd_hui = timezone.localdate()

        planifications_enrichies = []
        for planif in planifications:
            planifications_enrichies.append(
                {
                    "planification": planif,
                    "peut_marquer_cuisinee": (
                        planif.etat == "prevue" and aujourd_hui >= planif.date_prevue
                    ),
                    "peut_annuler": planif.etat == "prevue",
                }
            )

        return render(
            request,
            self.template_name,
            {
                "planifications_enrichies": planifications_enrichies,
                "recettes": recettes,
                "aujourd_hui": aujourd_hui,
            },
        )

    def post(self, request):
        type_action = request.POST.get("type_action")

        if type_action == "transition_planification":
            planif_id = request.POST.get("planification_id")
            action = request.POST.get("action")
            planif = get_object_or_404(Planification, pk=planif_id)

            if planif.etat != "prevue":
                messages.error(
                    request,
                    "Cette planification est déjà finalisée et ne peut plus changer d'état.",
                )
                return redirect("gestion")

            if action == "marquer_cuisinee":
                if timezone.localdate() < planif.date_prevue:
                    messages.error(
                        request,
                        "Impossible de marquer cette planification comme cuisinée avant sa date prévue.",
                    )
                    return redirect("gestion")
                planif.etat = "cuisinee"
                planif.date_modification = timezone.now()
                planif.save(update_fields=["etat", "date_modification"])
                messages.success(request, "Planification marquée comme cuisinée.")

            elif action == "annuler":
                planif.etat = "annulee"
                planif.date_modification = timezone.now()
                planif.save(update_fields=["etat", "date_modification"])
                messages.success(request, "Planification annulée.")

            else:
                messages.error(request, "Action de planification non reconnue.")

        elif type_action == "basculer_publication":
            recette_id = request.POST.get("recette_id")
            recette = get_object_or_404(Recette, pk=recette_id)

            if recette.etat_publication == "publiee":
                recette.etat_publication = "brouillon"
                messages.success(
                    request,
                    f"La recette « {recette.titre} » est passée en brouillon (nouvelles planifications bloquées).",
                )
            else:
                recette.etat_publication = "publiee"
                messages.success(
                    request,
                    f"La recette « {recette.titre} » est maintenant publiée.",
                )
            recette.save(update_fields=["etat_publication"])

        else:
            messages.error(request, "Action non reconnue.")

        return redirect("gestion")