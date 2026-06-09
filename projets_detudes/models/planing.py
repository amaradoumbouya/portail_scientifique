from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.crypto import get_random_string


class PlanningEncadrement(models.Model):

    class Statut(models.TextChoices):

        PLANIFIE = "planifie", "Planifié"
        EFFECTUE = "effectue", "Effectué"
        REPORTE = "reporte", "Reporté"
        ANNULE = "annule", "Annulé"

    projet           = models.ForeignKey("ProjetEtude", on_delete=models.CASCADE, related_name="planings")
    canevas          = models.ForeignKey("CanevasProjet", on_delete=models.SET_NULL, null=True, blank=True, related_name="planings")
    titre            = models.CharField(max_length=255)
    description      = models.TextField()
    date_rendez_vous = models.DateField()
    heure_debut      = models.TimeField()
    heure_fin        = models.TimeField()
    lieu             = models.CharField(max_length=255, blank=True, null=True)
    lien_visio       = models.URLField(blank=True, null=True)
    statut           = models.CharField(max_length=20, choices=Statut.choices, blank=True, default=Statut.PLANIFIE)
    observation      = models.TextField(blank=True, null=True)
    cree_par         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    slug             = models.SlugField(unique=True, blank=True, null=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:

        ordering = ['date_rendez_vous', 'heure_debut']

    def __str__(self):

        return f"{self.projet.titre} - {self.titre}"

    def save(self, *args, **kwargs):

        if not self.slug:

            self.slug = (slugify(self.titre) + "-"+ get_random_string(5))

        super().save(*args, **kwargs)