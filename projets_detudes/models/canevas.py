from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.crypto import get_random_string


class CanevasProjet(models.Model):

    projet      = models.ForeignKey("ProjetEtude", on_delete=models.CASCADE, related_name="canevas")
    titre       = models.CharField(max_length=255, blank=True, null=True, verbose_name='Titre')
    description = models.TextField()
    canevas_pdf = models.FileField(upload_to='projet_etude/canevas', verbose_name= 'Fichier')
    cree_par    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,null=True)
    slug        = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.projet.titre}- {self.titre}"

def save(self, *args, **kwargs):

    if not self.slug:

        base_slug = slugify(self.titre)

        # Limiter la taille
        base_slug = base_slug[:200]

        self.slug = (base_slug + "-" + get_random_string(5))
        
    super().save(*args, **kwargs)