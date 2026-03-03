from django import forms
from contact_us.models import ContactUs

class ContactUsForm(forms.ModelForm):
    class Meta:
        model = ContactUs
        fields = ['nom_complet', 'email', 'objectif', 'message']
        widgets = {
            "nom_complet":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "email":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "objectif":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
        }
        