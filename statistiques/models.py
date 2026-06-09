from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from publications.models.publication import Publication

class Statistique(models.Model):
    publication = models.OneToOneField(Publication, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    nb_vues = models.PositiveIntegerField(default=0)
    nb_telechargements = models.PositiveIntegerField(default=0)
    partages = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stats pour {self.publication.titre}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.publication.titre) + '-' + get_random_string(5)
        super(Statistique, self).save(*args, **kwargs)

    class Meta:
        db_table = 'statistique'
        verbose_name = 'statistique'
        verbose_name_plural = 'statistiques'
