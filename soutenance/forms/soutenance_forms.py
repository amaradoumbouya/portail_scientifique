from django import forms
from soutenance.models.soutenance import Soutenance



class SoutenanceForm(forms.ModelForm):
    class Meta:
        model = Soutenance
        exclude = [
            'projet',
            'responsable_planification',
            'created_at',
            'updated_at',
            'slug',
        ]

        widgets = {

            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'date'}),
            'heure': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'lieu': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lieu de la soutenance'}),
            'statut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Statut'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        heure = cleaned_data.get('heure')

        if not date:
            self.add_error('date', "La date est obligatoire.")

        if not heure:
            self.add_error('heure', "L'heure est obligatoire.")
        return cleaned_data