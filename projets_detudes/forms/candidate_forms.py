from django import forms
from projets_detudes.models.candidate import Candidate

class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = [
            'adresse',
            'matricule',
            'niveau',
            'domaine',
            'sujet_recherche',
            'annee_inscription',
            'institution',
            'reseau_social_facebook',
            'reseau_social_linkedin',
            'reseau_social_twitter',
            'reseau_social_youtube'
            ]
        
        widgets = {
            "adresse": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "matricule": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "niveau":forms.Select(attrs={'class': 'form-control form-control-rounded'}),
            "domaine":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "sujet_recherche":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "annee_inscription": forms.DateInput(attrs={'class': 'form-control form-control-rounded', 'type': 'date'}),
            "institution":forms.Select(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_facebook":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_linkedin":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_twitter":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_youtube":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
        }
        