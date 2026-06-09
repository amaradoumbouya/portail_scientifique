from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from projets_detudes.models.projet import ProjetEtude

class Participant(models.Model):

    class Role(models.TextChoices):
        AUTEUR = "Auteur principal"
        CO_AUTEUR = "Co-auteur"
        DIRECTEUR = "Directeur"
        CO_DIRECTEUR = "Co-directeur"

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente"
        ACCEPTE = "accepte"
        REFUSE = "refuse"

    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='participant')
    projet       = models.ForeignKey(ProjetEtude, on_delete=models.CASCADE, related_name="projet")
    role         = models.CharField(max_length=30, choices=Role.choices)
    has_accepted = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    date_ajout   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    slug         = models.SlugField(max_length=255, unique=True, editable=False, blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.role}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.user.full_name) + '-' + get_random_string(5)
        super().save(*args, **kwargs)