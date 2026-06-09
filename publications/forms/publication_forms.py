from django import forms
from publications.models.publication import Publication, ArticleScientifique, Colloque
from auteurs.models import Auteur
from encadreurs.models import Encadreur
from institutions.models import Institution

class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = [
            'type_publication',
            'photo',
            'titre',
            'langue',
            'doi',
            'fichier_pdf'
        ]
        widgets = {
            "type_publication":forms.Select(attrs={'class': 'form-control form-control-rounded'}),
            "photo":forms.ClearableFileInput(attrs={'class': 'form-control form-control-rounded'}),
            "titre":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "langue":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "doi":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "fichier_pdf":forms.ClearableFileInput(attrs={'class': 'form-control form-control-rounded'}),
        }


class ArticleForm(forms.ModelForm):
    class Meta:
        model = ArticleScientifique
        fields = [
            'nom_revue',
            'lien_article',
            'facteur_impact'
        ]
        widgets ={
            "nom_revue":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "lien_article":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "facteur_impact":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
        }


class ColloqueForm(forms.ModelForm):
    class Meta:
        model = Colloque
        fields = [
            'nom_colloque',
            'lieu',
            'date_colloque'
        ]

        widgets ={
            "nom_colloque":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "lieu":forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "date_colloque":forms.DateInput(attrs={'class': 'form-control form-control-rounded', 'type': 'date'}),
        }