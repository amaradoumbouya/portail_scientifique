from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string 


class ProjetPublication(models.Model):
    projet        = models.ForeignKey("Projets_etudes.ProjetEtude", on_delete=models.CASCADE)
    publication   = models.ForeignKey("publications.Publication", on_delete=models.CASCADE)
    relation_type = models.CharField(max_length=50)  # extrait, dérivé, principal
    slug          = models.SlugField(max_length=255, unique=True, editable=False ,blank=True, null=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.projet.titre) + '-' + get_random_string(5)
        super(ProjetPublication, self).save(*args, **kwargs)