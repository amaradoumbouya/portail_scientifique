from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from publications.models.publication import Publication

class Indexation(models.Model):
    publication = models.OneToOneField(Publication, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    date_indexation = models.DateTimeField(auto_now_add=True)
    mots_cles_ai = models.TextField()
    resume_ia = models.TextField()
    score_pertinence = models.FloatField()
    outil_indexation = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Indexation de {self.publication.titre}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.publication.titre) + '-' + get_random_string(5)
        super(Indexation, self).save(*args, **kwargs)

    class Meta:
        db_table = 'indexation'
        verbose_name = 'indexation'
        verbose_name_plural = 'indexations'

