from django import forms
from publications.models import Publication
from auteurs.models import Auteur
from encadreurs.models import Encadreur
from institutions.models import Institution

class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = [
            'type_document',
            'photo',
            'titre',
            'auteurs',
            'encadreurs', 
            'date_publication',
            'langue',
            'institutions_contributrices',
            'doi',
            'orcid_auteur_principal',
            'nom_revue',
            'nom_colloque',
            'lien_article', 
            'fichier_pdf'
        ]
        widgets = {
            "titre":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "auteurs":forms.SelectMultiple(attrs={'class': 'form-control form-control-rounded choices__input'}),
            "encadreurs":forms.SelectMultiple(attrs={'class': 'form-control form-control-rounded choices__input'}),
            "type_document":forms.Select(attrs={'class': 'form-control form-control-rounded choices__input'}),
            "date_publication":forms.TextInput(attrs={'type':'date', 'class': 'form-control form-control-rounded'}),
            "langue":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "institutions_contributrices":forms.SelectMultiple(attrs={'class': 'form-control form-control-rounded choices__input'}),
            "doi":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "orcid_auteur_principal":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
        }
        

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # On récupère l'utilisateur transmis depuis la vue
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['auteurs'].queryset = Auteur.objects.filter(user=user)
            self.fields['encadreurs'].queryset = Encadreur.objects.filter(user=user)

        