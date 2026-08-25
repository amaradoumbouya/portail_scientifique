from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from publications.models.publication import Publication

class Indexation(models.Model):
    publication = models.OneToOneField(
        Publication,
        on_delete=models.CASCADE,
        related_name='indexation',
    )
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    date_indexation = models.DateTimeField(auto_now_add=True)
    mots_cles_ai = models.TextField(blank=True, default='')
    resume_ia = models.TextField(blank=True, default='')
    score_pertinence = models.FloatField(default=0)
    outil_indexation = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Indexation de {self.publication.titre}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.publication.titre or 'publication') or 'publication'
            self.slug = base + '-' + get_random_string(5)
        super(Indexation, self).save(*args, **kwargs)

    class Meta:
        db_table = 'indexation'
        verbose_name = 'indexation'
        verbose_name_plural = 'indexations'

