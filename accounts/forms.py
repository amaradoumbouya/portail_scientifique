from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from accounts.models import *


class CustumerUserForm(UserCreationForm):
    class Meta:
        model = CustumerUser
        fields = ['prenoms', 'nom', 'email', 'tel', 'sexe', 'password1', 'password2']
        widgets = {
            "prenoms": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "nom": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "email": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "tel": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            'sexe': forms.Select(attrs={'class': 'form-control form-control-rounded choices__input'}),
            'password1': forms.TextInput(attrs={'type': 'password', 'class': 'form-control form-control-rounded'}),
            'password2': forms.TextInput(attrs={'type': 'password', 'class': 'form-control form-control-rounded'}),
        }

class CustumerUserChangeForm(UserChangeForm):
    class Meta:
        model = CustumerUser
        fields = ['prenoms', 'nom', 'email', 'tel', 'sexe']
        widgets = {
            "prenoms": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "nom": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "email": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "tel": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            'sexe': forms.Select(attrs={'class': 'form-control form-control-rounded choices__input'}),
        }

class CustumerUserChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.TextInput(attrs={'type': 'password', 'class': 'form-control form-control-rounded'}), label='Mot de passe actuel :')
    new_password1 = forms.CharField(widget=forms.TextInput(attrs={'type': 'password', 'class': 'form-control form-control-rounded'}), label='Nouveau mot de passe :')
    new_password2 = forms.CharField(widget=forms.TextInput(attrs={'type': 'password', 'class': 'form-control form-control-rounded'}), label='Confirmer le nouveau mot de passe :')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [ 'adresse', 'institution', 'fonction_poste', 'grade', 'specialite', 'orcid', 'photo', 'site_web', 'reseau_social_facebook', 'reseau_social_twitter', 'reseau_social_linkedin', 'reseau_social_youtube']
        widgets = {
            "adresse": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "institution": forms.Select(attrs={'class': 'form-control form-control-rounded choices__input'}),
            "fonction_poste": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "grade": forms.Select(attrs={'class': 'form-control form-control-rounded choices__input'}),
            "specialite": forms.Select(attrs={'class': 'form-control form-control-rounded choices__input'}),
            "orcid": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "photo": forms.FileInput(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_facebook": forms.URLInput(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_twitter": forms.URLInput(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_linkedin": forms.URLInput(attrs={'class': 'form-control form-control-rounded'}),
            "reseau_social_youtube": forms.URLInput(attrs={'class': 'form-control form-control-rounded'}),
        }

class User_biographyForm(forms.ModelForm):
    class Meta:
        model = User_biography
        fields = ['biographie']
        widgets = {
            'biographie': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

class User_emploiForm(forms.ModelForm):
    class Meta:
        model = User_emploi
        fields = ['nom_institution', 'ville_emploi', 'region_emploi', 'pays_emploi', 'departement_emploi', 'poste_occupe', 'date_debut_emploi', 'date_fin_emploi']
        widgets = {
            'nom_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'ville_emploi': forms.TextInput(attrs={'class': 'form-control'}),
            'region_emploi': forms.TextInput(attrs={'class': 'form-control'}),
            'pays_emploi': forms.TextInput(attrs={'class': 'form-control'}),
            'departement_emploi': forms.TextInput(attrs={'class': 'form-control'}),
            'poste_occupe': forms.TextInput(attrs={'class': 'form-control'}),
            'date_debut_emploi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin_emploi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class User_etude_academiqueForm(forms.ModelForm):
    class Meta:
        model = User_etude_academique
        fields = ['type_formation', 'nom_institution', 'ville_institution', 'region_institution', 'pays_institution', 'departement_etude', 'diplome_obtenu', 'date_debut_etude', 'date_fin_etude']
        widgets = {
            'type_formation': forms.Select(attrs={'class': 'form-control'}),
            'nom_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'ville_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'region_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'pays_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'departement_etude': forms.TextInput(attrs={'class': 'form-control'}),
            'diplome_obtenu': forms.TextInput(attrs={'class': 'form-control'}),
            'date_debut_etude': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin_etude': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class User_experience_professionnelleForm(forms.ModelForm):
    class Meta:
        model = User_experience_professionnelle
        fields = ['nom_institution', 'poste_occupe', 'date_debut_experience', 'date_fin_experience']
        widgets = {
            'nom_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'poste_occupe': forms.TextInput(attrs={'class': 'form-control'}),
            'date_debut_experience': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin_experience': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class User_travaux_rechercheForm(forms.ModelForm):
    class Meta:
        model = User_travaux_recherche
        fields = ['nom_institution', 'ville_institution', 'region_institution', 'pays_institution', 'departement_recherche', 'poste_occupe', 'titre_domaine_recherche', 'date_de_debut_travaux', 'date_de_fin_travaux']
        widgets = {
            'nom_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'ville_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'region_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'pays_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'departement_recherche': forms.TextInput(attrs={'class': 'form-control'}),
            'poste_occupe': forms.TextInput(attrs={'class': 'form-control'}),
            'titre_domaine_recherche': forms.TextInput(attrs={'class': 'form-control'}),
            'date_de_debut_travaux': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_de_fin_travaux': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }