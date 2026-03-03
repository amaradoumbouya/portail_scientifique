from django import forms
from types_document.models import TypeDocument

class TypeDocumentForm(forms.ModelForm):
    class Meta:
        model = TypeDocument
        fields = ['libelle']
        widgets = {
            "libelle":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),

        }
        