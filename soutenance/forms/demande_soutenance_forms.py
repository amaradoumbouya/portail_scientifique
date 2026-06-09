from django import forms
from soutenance.models.soutenance import (DemandeSoutenance)


class DemandeSoutenanceForm(forms.ModelForm):
    class Meta:
        model = DemandeSoutenance
        fields = [
            'observations_directeur',
        ]
        widgets = {
            'observations_directeur': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder':'Motif ou commentaire de la demande'})
        }
        labels = {'observations_directeur':'Observation'}