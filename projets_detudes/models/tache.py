from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from projets_detudes.models.projet import ProjetEtude

class Tache(models.Model):

    class Priorite(models.TextChoices):
        BASSE = "basse", "Basse"
        MOYENNE = "moyenne", "Moyenne"
        HAUTE = "haute", "Haute"

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        EN_COURS = "en_cours", "En cours"
        TERMINE = "termine", "Terminé"
        RETARD = "retard", "Retard"

    canevas           = models.ForeignKey("CanevasProjet", on_delete=models.CASCADE, related_name="taches")
    projet            = models.ForeignKey(ProjetEtude, on_delete=models.CASCADE, related_name="etapes")
    titre             = models.CharField(max_length=255)
    date_debut        = models.DateField()
    date_fin          = models.DateField()
    description       = models.TextField()
    assigne_a         = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="tache_assignee")
    cree_par          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tache_creee")
    priorite          = models.CharField(max_length=20, choices=Priorite.choices,blank=True, default=Priorite.MOYENNE)
    statut            = models.CharField(max_length=20, choices=Statut.choices,blank=True, default=Statut.EN_ATTENTE)
    progression       = models.PositiveIntegerField(default=0, blank=True, null=True)
    fichier_pdf_tache = models.FileField(upload_to='projet_etude/tache',blank=True, null=True, verbose_name= 'Fichier')
    slug              = models.SlugField(max_length=255, unique=True, editable=False, blank=True, null=True)
    date_creation     = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)


    class Meta:

        ordering = ['date_debut']

    def __str__(self):
        return self.titre
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = (slugify(self.titre) + "-" + get_random_string(5))
        super().save(*args, **kwargs)