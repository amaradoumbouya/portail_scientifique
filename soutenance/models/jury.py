from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from soutenance.models.soutenance import Soutenance
from projets_detudes.models.projet import ProjetEtude



class JuryMember(models.Model):

    class RoleJury(models.TextChoices):
        PRESIDENT = "president", "Président"
        RAPPORTEUR = "rapporteur", "Rapporteur"
        EXAMINATEUR = "examinateur", "Examinateur"
        DIRECTEUR = "directeur", "Directeur"
        CO_DIRECTEUR = "co_directeur", "Co-directeur"

    soutenance = models.ForeignKey(Soutenance, on_delete=models.CASCADE, related_name="jury")
    enseignant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jury_as_enseignant")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jury_created", blank=True, null=True)
    role       = models.CharField(max_length=30,choices=RoleJury.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug       = models.SlugField(max_length=255, unique=True, editable=False ,blank=True, null=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.created_by.full_name) + '-' + get_random_string(5)
        super(JuryMember, self).save(*args, **kwargs)