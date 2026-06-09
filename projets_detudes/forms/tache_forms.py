from django import forms

from projets_detudes.models.tache import Tache

from projets_detudes.models.canevas import (CanevasProjet)

from projets_detudes.models.participant import (Participant)

from django.contrib.auth import get_user_model

User = get_user_model()


# =========================================================
# FORMULAIRE TACHE
# =========================================================
class TacheForm(forms.ModelForm):

    class Meta:

        model = Tache

        exclude = [
            'projet',
            'cree_par',
            'slug',
            'date_creation',
            'updated_at',
        ]

        widgets = {

            'canevas': forms.Select(attrs={'class': 'form-control'}),
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'fichier_pdf_tache': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Description de la tâche'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assigne_a': forms.Select(attrs={'class': 'form-control'}),
            'priorite': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'progression': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }

    # =====================================================
    # FILTRER LES CANEVAS DU PROJET
    # =====================================================
    def __init__(self, *args, **kwargs):

        projet = kwargs.pop('projet', None)

        super().__init__(*args, **kwargs)

        if projet:
            # =============================================
            # CANEVAS DU PROJET
            # =============================================
            self.fields['canevas'].queryset = CanevasProjet.objects.filter(projet=projet)
            # =============================================
            # PARTICIPANTS
            # =============================================
            participants = Participant.objects.filter(projet=projet,
                role__in=[
                    Participant.Role.AUTEUR,
                    Participant.Role.CO_AUTEUR
                ]).values_list('user_id',flat=True)

            self.fields['assigne_a'].queryset = User.objects.filter(id__in=participants)
    # =====================================================
    # VALIDATION DATE
    # =====================================================
    def clean(self):

        cleaned_data = super().clean()

        date_debut = cleaned_data.get('date_debut')

        date_fin = cleaned_data.get('date_fin')

        # Vérification date fin
        if date_debut and date_fin:

            if date_fin < date_debut:

                self.add_error('date_fin', "La date de fin doit être supérieure à la date de début.")

        return cleaned_data