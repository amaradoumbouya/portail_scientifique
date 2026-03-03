from django import forms
from partenaires.models import Partenaire

class PartenaireForm(forms.ModelForm):
    class Meta:
        model = Partenaire
        fields = ['logo', 'nom', 'site_web', 'email', 'telephone', 'adresse', 'description']