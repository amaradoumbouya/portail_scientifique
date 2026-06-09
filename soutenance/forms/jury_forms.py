from django import forms

from soutenance.models.jury import JuryMember


class JuryMemberForm(forms.ModelForm):
    class Meta:
        model = JuryMember
        exclude = [
            'soutenance',
            'user',
            'created_at',
            'updated_at',
            'slug',
        ]

        widgets = {
            'enseignant': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),

        }