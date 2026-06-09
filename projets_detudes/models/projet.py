from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.crypto import get_random_string


class ProjetEtude(models.Model):

    class TypeProjet(models.TextChoices):
        MEMOIRE = "memoire", "Mémoire"
        THESE = "these", "Thèse"

    class StatutProjet(models.TextChoices):
        SOUMIS = "soumis"
        EN_COURS = "en_cours"
        EN_REVUE = "en_revue"
        VALIDE = "valide"
        TERMINE = "termine"
        REJETE = "rejete"

    type_projet     = models.CharField(max_length=20, choices=TypeProjet.choices)
    titre           = models.CharField(max_length=255, verbose_name="Titre du projet")
    description     = models.TextField(verbose_name="Description du projet")
    createur        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    candidate       = models.ForeignKey("projets_detudes.Candidate",on_delete=models.CASCADE,related_name="etudiant")
    statut          = models.CharField(max_length=20, choices=StatutProjet.choices, default="soumis")
    date_validation = models.DateTimeField(null=True, blank=True)
    slug            = models.SlugField(max_length=255, unique=True, editable=False ,blank=True, null=True,)
    date_soumission = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titre
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titre) + '-' + get_random_string(5)
        super(ProjetEtude, self).save(*args, **kwargs)