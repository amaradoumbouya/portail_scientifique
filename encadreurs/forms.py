from django import forms
from .models import Encadreur

class EncadreurForm(forms.ModelForm):
    class Meta:
        model = Encadreur
        fields = ['photo','prenoms', 'nom', 'email', 'institution', 'grade', 'specialite', 'facebook', 'twitter', 'linkedin', 'site_web', 'parcours',]
        widgets = {
            "prenoms":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "nom":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "email":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "institution":forms.Select(attrs={'class': 'form-control form-control-rounded choices__input'}),
            "grade":forms.Select(attrs={'class': 'form-control form-control-rounded choices__input'}),
            "specialite":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            'parcours': forms.Textarea(attrs={'rows':4}),
        }