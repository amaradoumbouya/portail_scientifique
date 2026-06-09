from django import forms
from projets_detudes.models.participant import Participant

class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = [
            'user',
            'projet',
            'role',
            ]
        
        widgets = {
            "user": forms.Select(attrs={'class': 'form-control form-control-rounded'}),
            "projet": forms.Select(attrs={'class': 'form-control form-control-rounded'}),
            "role": forms.Select(attrs={'class': 'form-control form-control-rounded'}),
        }
        