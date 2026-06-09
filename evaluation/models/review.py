from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from projets_detudes.models.projet import ProjetEtude


class Review(models.Model):

    projet             = models.ForeignKey(ProjetEtude, on_delete=models.CASCADE)
    reviewer           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    decision           = models.CharField(max_length=50)
    commentaire        = models.TextField()
    date_review        = models.DateTimeField(auto_now_add=True)
    slug               = models.SlugField(max_length=255, unique=True, editable=False ,blank=True, null=True,)
    updated_at         = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.projet.titre) + '-' + get_random_string(5)
        super(Review, self).save(*args, **kwargs)