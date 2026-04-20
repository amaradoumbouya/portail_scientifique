from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from accounts.models import CustumerUser, UserProfile

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
        fields = ['adresse', 'institution', 'fonction_poste', 'grade', 'specialite', 'orcid', 'photo','reseau_social_facebook', 'reseau_social_twitter', 'reseau_social_linkedin', 'reseau_social_youtube']
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