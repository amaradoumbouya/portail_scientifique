from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string


class Actualite(models.Model):
    titre = models.CharField(max_length=255, verbose_name='Titre')
    resume = models.TextField(
        max_length=500,
        verbose_name='Résumé',
        help_text='Court texte affiché sur la page d’accueil.',
    )
    contenu = models.TextField(verbose_name='Contenu')
    image = models.ImageField(
        upload_to='actualites/images/',
        blank=True,
        null=True,
        verbose_name='Image',
    )
    date_publication = models.DateField(verbose_name='Date de publication')
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    is_actif = models.BooleanField(default=True, verbose_name='Actif ?')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'actualite'
        verbose_name = 'Actualité'
        verbose_name_plural = 'Actualités'
        ordering = ['-date_publication', '-created_at']

    def __str__(self):
        return self.titre

    @property
    def ImageUrl(self):
        try:
            return self.image.url
        except Exception:
            return ''

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titre) + '-' + get_random_string(5)
        super().save(*args, **kwargs)
