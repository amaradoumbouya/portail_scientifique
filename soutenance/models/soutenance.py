
from contact_us import models
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from projets_detudes.models.projet import ProjetEtude
from projets_detudes.models.candidate import Candidate


class Soutenance(models.Model):
    projet     = models.ForeignKey(ProjetEtude, on_delete=models.CASCADE)
    responsable_planification = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True, related_name="soutenances_planifiees")
    date       = models.DateField(blank=True, null=True)
    heure      = models.TimeField()
    lieu       = models.CharField(max_length=255)
    statut     = models.CharField(max_length=50, default="Planifiée", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug       = models.SlugField(max_length=255, unique=True, editable=False ,blank=True, null=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.projet.titre) + '-' + get_random_string(5)
        super(Soutenance, self).save(*args, **kwargs)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["projet"],
                name="unique_soutenance_par_projet"
            )
        ]


class DemandeSoutenance(models.Model):
    projet                   = models.ForeignKey(ProjetEtude, on_delete=models.CASCADE)
    candidat                 = models.ForeignKey(Candidate,on_delete=models.CASCADE,related_name="demande_soutenance")
    responsable_institution  = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="demandes_reçues")
    directeur_validation     = models.BooleanField(default=False)
    responsable_validation   = models.BooleanField(default=False)
    date_demande             = models.DateTimeField(auto_now_add=True)
    observations_directeur   = models.TextField(blank=True)
    observations_responsable = models.TextField(blank=True)
    statut                   = models.CharField(max_length=50, default="En attente")
    updated_at               = models.DateTimeField(auto_now=True)
    slug                     = models.SlugField(max_length=255, unique=True, editable=False ,blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.projet.titre) + '-' + get_random_string(5)
        super(DemandeSoutenance, self).save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["projet"],
                name="unique_demande_soutenance_par_projet"
            )
        ]