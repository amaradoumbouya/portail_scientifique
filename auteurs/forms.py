from django import forms
from auteurs.models import Auteur

class AuteurForm(forms.ModelForm):
    class Meta:
        model = Auteur
        fields = ['photo', 'prenoms', 'nom', 'email', 'orcid', 'statut', 'institution', 'facebook', 'twitter', 'linkedin', 'site_web', 'biographie']
        widgets = {
            "prenoms":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "nom":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "email":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "orcid":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "statut":forms.Select(attrs={'class': 'form-control form-control-rounded choices__input'}),
            "institution":forms.Select(attrs={'class': 'form-control form-control-rounded choices__input'}),
        }
        