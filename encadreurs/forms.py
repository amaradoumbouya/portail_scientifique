from django import forms
from .models import Encadreur

class EncadreurForm(forms.ModelForm):
    class Meta:
        model = Encadreur
        fields = ['prenoms', 'nom', 'email']
        widgets = {
            "prenoms":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "nom":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "email":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
        }