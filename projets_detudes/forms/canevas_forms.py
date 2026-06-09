from django import forms

from projets_detudes.models.canevas import CanevasProjet


# =========================================================
# FORMULAIRE AJOUT / MODIFICATION CANEVAS
# =========================================================
class CanevasProjetForm(forms.ModelForm):

    class Meta:

        model = CanevasProjet

        fields = [
            'titre',
            'description',
            'canevas_pdf',
        ]

        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Description du canevas'}),
            'canevas_pdf': forms.FileInput(attrs={'class': 'form-control'}),
        }

    # =====================================================
    # VALIDATION PDF
    # =====================================================
    def clean_canevas_pdf(self):

        fichier = self.cleaned_data.get('canevas_pdf')
        if fichier:

            # Vérification extension
            if not fichier.name.endswith('.pdf'):
                raise forms.ValidationError("Le fichier doit être un PDF.")

            # Taille max : 10 MB
            if fichier.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Le fichier ne doit pas dépasser 10 MB.")
        return fichier