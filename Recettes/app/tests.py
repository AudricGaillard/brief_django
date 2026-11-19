# A EXECUTER AVEC : python manage.py test

from django.test import TestCase

# Create your tests here.
from .models import Utilisateur

class testUser(TestCase):
    def setUp(self):
        Utilisateur.objects.create_user(
            username='test',
            email="test.python@gmail.com",
            regime=[]
        )

    def testModel(self):
        print(Utilisateur.objects.get(username='test'))
        print(Utilisateur.objects.get(username='test').email)
        print(Utilisateur.objects.get(username='test').password)
        print(Utilisateur.objects.get(username='test').regime)
        