from django import forms
from django.contrib.auth.forms import UserCreationForm,UserChangeForm
from accounts.models import CustumerUser, UserProfile
from institutions.models import Institution

class CustumerUserForm(UserCreationForm):
    class Meta:
        model = CustumerUser
        fields = [
            'prenoms',
            'nom',
            'email',
            'tel',
            'sexe',
            'password1',
            'password2'
            ]
        
        widgets = {
            "prenoms": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "nom": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "email": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "tel": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            'sexe': forms.Select(attrs={'class': 'form-control form-control-rounded choices__input'}),
            'password1': forms.TextInput(attrs={'type': 'password', 'class': 'form-control form-control-rounded'}),
            'password2': forms.TextInput(attrs={'type': 'password', 'class': 'form-control form-control-rounded'}),
        }



class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'adresse',
            'institution',
            'fonction_poste',
            'grade',
            'specialite',
            'orcid',
            'photo',
            'reseau_social_facebook',
            'reseau_social_twitter',
            'reseau_social_linkedin',
            'reseau_social_youtube'
            ]
        
        widgets = {
            "adresse": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "institution": forms.Select(attrs={'class': 'form-control form-control-rounded choices__input'}),
            "fonction_poste": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "grade": forms.Select(attrs={'class': 'form-control form-control-rounded'}),
            "specialite": forms.Select(attrs={'class': 'form-control form-control-rounded'}),
            "orcid": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "photo": forms.FileInput(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_facebook": forms.URLInput(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_twitter": forms.URLInput(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_linkedin": forms.URLInput(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_youtube": forms.URLInput(attrs={'class': 'form-control form-control-rounded'}),
        }

class InstitutionForm(forms.ModelForm):
    class Meta:
        model = Institution
        fields = [
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