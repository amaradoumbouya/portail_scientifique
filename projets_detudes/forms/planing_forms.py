from django import forms

from projets_detudes.models.planing import PlanningEncadrement


class PlanningEncadrementForm(forms.ModelForm):

    class Meta:

        model = PlanningEncadrement

        exclude = [
            'projet',
            'cree_par',
            'slug',
            'created_at',
            'updated_at'
        ]

        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date_rendez_vous': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'heure_debut': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'lieu': forms.TextInput(attrs={'class': 'form-control'}),
            'lien_visio': forms.URLInput(attrs={'class': 'form-control'}),
        }