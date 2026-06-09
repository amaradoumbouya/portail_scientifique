from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from projets_detudes.models.projet import ProjetEtude  


class ProgressReport(models.Model):
    projet = models.ForeignKey(ProjetEtude, on_delete=models.CASCADE, related_name="reports")
    soumis_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contenu = models.TextField()
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(max_length=20, default="soumis")
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=255, unique=True, editable=False, blank=True, null=True)

    def __str__(self):
        return f"Rapport - {self.projet.titre}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.soumis_par.full_name) + '-' + get_random_string(5)
        super(ProgressReport, self).save(*args, **kwargs)