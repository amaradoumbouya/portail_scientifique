from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from projets_detudes.models.projet import ProjetEtude



class Document(models.Model):

    class TypeDocument(models.TextChoices):
        RAPPORT = "rapport"
        PROPOSITION = "proposition"
        VERSION_FINALE = "final"
        AUTRE = "autre"

    projet        = models.ForeignKey(ProjetEtude, on_delete=models.CASCADE, related_name="documents")
    fichier       = models.FileField(upload_to="projets/")
    uploader      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type_document = models.CharField(max_length=30, choices=TypeDocument.choices)
    version       = models.IntegerField(default=1)
    description   = models.TextField(blank=True)
    slug          = models.SlugField(max_length=255, unique=True, editable=False ,blank=True, null=True)
    date_upload   = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.projet.titre} - v{self.version}"
    

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.uploader.full_name) + '-' + get_random_string(5)
        super(Document, self).save(*args, **kwargs)