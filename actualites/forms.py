from django import forms
from actualites.models import Actualite


class ActualiteForm(forms.ModelForm):
    class Meta:
        model = Actualite
        fields = [
            'image',
            'titre',
            'date_publication',
            'resume',
            'contenu',
            'is_actif',
        ]
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control form-control-rounded'}),
            'titre': forms.TextInput(attrs={'class': 'form-control form-control-rounded'}),
            'date_publication': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control form-control-rounded'},
                format='%Y-%m-%d',
            ),
            'resume': forms.Textarea(attrs={'rows': 3, 'class': 'form-control form-control-rounded'}),
            'contenu': forms.Textarea(attrs={'rows': 6, 'class': 'form-control form-control-rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_publication'].input_formats = ['%Y-%m-%d']
        if self.instance and self.instance.pk and self.instance.date_publication:
            self.initial['date_publication'] = self.instance.date_publication.strftime('%Y-%m-%d')
        self.fields['image'].required = False
