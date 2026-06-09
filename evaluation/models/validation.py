from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from projets_detudes.models.projet import ProjetEtude


class Validation(models.Model):

    projet          = models.ForeignKey(ProjetEtude, on_delete=models.CASCADE, related_name="validations")
    valide_par      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    decision        = models.CharField(max_length=20)  # accepté / rejeté
    commentaire     = models.TextField(blank=True)
    slug            = models.SlugField(max_length=255, unique=True, editable=False ,blank=True, null=True,)
    date_validation = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.projet.titre) + '-' + get_random_string(5)
        super(Validation, self).save(*args, **kwargs)