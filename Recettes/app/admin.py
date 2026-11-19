from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Categorie, Objet, Ingredient, Action # a modifier suivant les noms de classe exact

class CustomUserAdmin(UserAdmin): # A modifier suivant le nom de classe exact
    """
    Personnalisation de l'affichage de l'utilisateur dans l'admin 
    pour inclure les champs spécifiques (role et regime).
    """
    fieldsets = UserAdmin.fieldsets + (
        ('Informations spécifiques', {'fields': ('role', 'regime')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations spécifiques', {'fields': ('role', 'regime')}),
    )

# Enregistrement des classes , a confirmer.
admin.site.register(Utilisateur, CustomUserAdmin)
admin.site.register(Categorie)
admin.site.register(Objet)
admin.site.register(Ingredient)
admin.site.register(Action)
