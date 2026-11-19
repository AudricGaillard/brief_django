from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Categorie, Ingredient, Planification, Recette, Utilisateur


class CustomUserAdmin(UserAdmin):
    """
    Personnalisation de l'affichage de l'utilisateur dans l'admin
    pour inclure le champ spécifique regime.
    """
    fieldsets = UserAdmin.fieldsets + (
        ('Informations spécifiques', {'fields': ('regime',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations spécifiques', {'fields': ('regime',)}),
    )


admin.site.register(Utilisateur, CustomUserAdmin)
admin.site.register(Categorie)
admin.site.register(Recette)
admin.site.register(Ingredient)
admin.site.register(Planification)
