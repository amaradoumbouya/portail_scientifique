from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from accounts.models import CustumerUser

class CustumerUserForm(UserCreationForm):
    class Meta:
        model = CustumerUser
        fields = [
            'prenoms', 'nom', 'adresse', 'email', 'tel',
            'sexe', 'role', 'photo', 'password1', 'password2'
        ]
        widgets = {
            "prenoms": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "nom": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "adresse": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "email": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "tel": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            'sexe': forms.Select(attrs={'class': 'form-control form-control-rounded choices__input'}),
            'role': forms.Select(attrs={'class': 'form-control form-control-rounded choices__input'}),
            'password1': forms.TextInput(attrs={'type': 'password', 'class': 'form-control form-control-rounded'}),
            'password2': forms.TextInput(attrs={'type': 'password', 'class': 'form-control form-control-rounded'}),
        }

