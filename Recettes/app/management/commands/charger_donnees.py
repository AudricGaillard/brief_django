from django.core.management.base import BaseCommand

class Command(BaseCommand):
    

    def handle(files, self, *args, **options):
        """
        C'est la méthode principale qui s'exécute automatiquement 
        quand on lance la commande dans le terminal.
        """
        self.stdout.write(self.style.SUCCESS("Début du chargement des données..."))
        
        # C'est ici que nous écrirons notre logique étape par étape !

        self.stdout.write(self.style.SUCCESS("Chargement terminé avec succès !"))