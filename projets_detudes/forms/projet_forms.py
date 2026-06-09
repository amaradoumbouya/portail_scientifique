from django import forms
from projets_detudes.models.projet import ProjetEtude

class ProjetForm(forms.ModelForm):
    class Meta:
        model = ProjetEtude
        fields = [
            'titre',
            'description',
            ]
        
        widgets = {
            "titre": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "description": forms.Textarea(attrs={'class': 'form-control form-control-rounded', 'rows': 4}),
        }
        