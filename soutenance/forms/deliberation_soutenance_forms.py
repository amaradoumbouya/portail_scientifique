from django import forms

from soutenance.models.deliberation_soutenance import DeliberationSoutenance


class DeliberationSoutenanceForm(forms.ModelForm):

    class Meta:

        model = DeliberationSoutenance

        fields = [

            "note_finale",

            "decision",

            "observations",

        ]

        widgets = {

            "note_finale": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ex : 16.50", "min": "0", "max": "20", "step": "0.01",}),

            "decision": forms.Select(attrs={"class": "form-control",}),

            "observations": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Observations du jury...",}),

        }

    def clean_note_finale(self):

        note = self.cleaned_data.get("note_finale")

        if note is None:

            raise forms.ValidationError("La note finale est obligatoire.")

        if note < 0 or note > 20:

            raise forms.ValidationError("La note doit être comprise entre 0 et 20.")

        return note