from django import forms
from institutions.models import Institution

class InstitutionForm(forms.ModelForm):
    class Meta:
        model = Institution
        fields = [
            'type_institution',
            'nom_institution',
            'sigle_institution',
            'email_institution',
            'telephone_institution',
            'adresse_institution',
            'ville',
            'pays',
            'ror',
            'site_web_institution',
            'logo_institution',
            'reseau_social_facebook_inst',
            'reseau_social_twitter_inst',
            'reseau_social_linkedin_inst',
            'reseau_social_youtube_inst'
            ]
        
        widgets = {
            "type_institution": forms.Select(attrs={'class': 'form-control form-control-rounded'}),
            "nom_institution":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "sigle_institution":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "email_institution":forms.EmailInput(attrs={'class': 'form-control form-control-rounded'}),
            "telephone_institution":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "adresse_institution":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "ville":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "pays":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "ror":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "site_web_institution":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "logo_institution":forms.FileInput(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_facebook_inst": forms.URLInput(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_twitter_inst": forms.URLInput(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_linkedin_inst": forms.URLInput(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_youtube_inst": forms.URLInput(attrs={'class': 'form-control form-control-rounded'}),

        }
        