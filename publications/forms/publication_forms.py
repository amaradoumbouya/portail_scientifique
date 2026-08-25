from django import forms
from publications.models.publication import Publication, ArticleScientifique, Colloque
from auteurs.models import Auteur
from encadreurs.models import Encadreur
from institutions.models import Institution

MAX_PUBLICATION_FILE_SIZE = 50 * 1024 * 1024  # 50 Mo (aligné Nginx)


class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = [
            'type_publication',
            'titre',
            'doi',
            'licence',
            'fichier_pdf'
        ]
        widgets = {
            "type_publication": forms.Select(attrs={'class': 'form-control form-control-rounded'}),
            "titre": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "doi": forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            "licence": forms.Select(attrs={'class': 'form-control form-control-rounded'}),
            "fichier_pdf": forms.ClearableFileInput(attrs={'class': 'form-control form-control-rounded'}),
        }

    def _validate_file_size(self, field_name, label):
        fichier = self.cleaned_data.get(field_name)
        if fichier and hasattr(fichier, 'size') and fichier.size > MAX_PUBLICATION_FILE_SIZE:
            max_mo = MAX_PUBLICATION_FILE_SIZE // (1024 * 1024)
            raise forms.ValidationError(
                f"Le fichier « {label} » est trop volumineux (max. {max_mo} Mo)."
            )
        return fichier

    def clean_fichier_pdf(self):
        return self._validate_file_size('fichier_pdf', 'article')


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