from django import forms
from evenements.models import Evenement, InscriptionEvenement


class EvenementForm(forms.ModelForm):
    class Meta:
        model = Evenement
        fields = [
            'image',
            'titre',
            'type_evenement',
            'date_evenement',
            'lieu',
            'description',
            'lien_inscription',
            'lien_details',
            'is_actif',
        ]
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control form-control-rounded'}),
            'titre': forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            'type_evenement': forms.Select(attrs={'class': 'form-control form-control-rounded'}),
            'date_evenement': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control form-control-rounded'},
                format='%Y-%m-%dT%H:%M',
            ),
            'lieu': forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control form-control-rounded'}),
            'lien_inscription': forms.URLInput(attrs={'class': 'form-control form-control-rounded'}),
            'lien_details': forms.URLInput(attrs={'class': 'form-control form-control-rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_evenement'].input_formats = [
            '%Y-%m-%dT%H:%M',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
        ]
        if self.instance and self.instance.pk and self.instance.date_evenement:
            self.initial['date_evenement'] = self.instance.date_evenement.strftime('%Y-%m-%dT%H:%M')
        self.fields['lien_inscription'].required = False
        self.fields['lien_details'].required = False
        self.fields['image'].required = False
        self.fields['lieu'].required = False


class InscriptionEvenementForm(forms.ModelForm):
    class Meta:
        model = InscriptionEvenement
        fields = ['prenoms', 'nom', 'email', 'telephone', 'institution', 'message']
        widgets = {
            'prenoms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vos prénoms'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre nom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Votre email'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre téléphone'}),
            'institution': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre institution'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Message (optionnel)'}),
        }
