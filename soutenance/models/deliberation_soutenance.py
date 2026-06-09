from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from projets_detudes.models.projet import ProjetEtude



class Award(models.Model):
    projet             = models.OneToOneField(ProjetEtude, on_delete=models.CASCADE)
    degree_awarded     = models.CharField(max_length=255)
    award_date         = models.DateField()
    certificate_number = models.CharField(max_length=100)
    slug               = models.SlugField(max_length=255, unique=True, editable=False, blank=True, null=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Award - {self.projet.titre}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.projet.titre) + '-' + get_random_string(5)
        super(Award, self).save(*args, **kwargs)



class DeliberationSoutenance(models.Model):

    class Decision(models.TextChoices):

        ADMIS = "admis", "Admis"

        ADMIS_CORRECTIONS = (
            "admis_corrections",

            "Admis sous réserve de corrections"
            )

        AJOURNE = "ajourne", "Ajourné"

        REJETE = "rejete", "Rejeté"

    soutenance        = models.OneToOneField("Soutenance", on_delete=models.CASCADE, related_name="deliberation")
    note_finale       = models.DecimalField(max_digits=4, decimal_places=2)
    mention           = models.CharField(max_length=100, blank=True)
    decision          = models.CharField(max_length=50, choices=Decision.choices)
    observations      = models.TextField(blank=True)
    saisi_par         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    date_deliberation = models.DateTimeField(auto_now_add=True)
    resultat_publie   = models.BooleanField(default=False)
    date_publication  = models.DateTimeField(null=True, blank=True)
    slug              = models.SlugField(max_length=255, unique=True, editable=False, blank=True, null=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def __str__(self):

        return f"{self.soutenance.projet.titre}"
    
    def save(self, *args, **kwargs):

        if not self.slug:

            self.slug = slugify(self.soutenance.projet.titre) + '-' + get_random_string(5)

        super(DeliberationSoutenance, self).save(*args, **kwargs)

class ArchiveSoutenance(models.Model):
    soutenance = models.OneToOneField("Soutenance",on_delete=models.CASCADE, related_name="archive")
    date_archivage = models.DateTimeField(auto_now_add=True)
    archive_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    commentaire = models.TextField(blank=True)

    def __str__(self):

        return f"Archive - {self.soutenance.projet.titre}"