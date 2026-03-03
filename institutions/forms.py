from django import forms
from institutions.models import Institution

class InstitutionForm(forms.ModelForm):
    class Meta:
        model = Institution
        fields = ['nom', 'type', 'ville', 'pays', 'site_web']
        widgets = {
            "nom":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "type":forms.Select(attrs={'class': 'form-control form-control-rounded choices__input'}),
            "ville":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "pays":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "site_web":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),

        }
        