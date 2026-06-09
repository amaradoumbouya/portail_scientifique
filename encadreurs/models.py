from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from institutions.models import Institution
from django.conf import settings
from django.contrib.auth import  get_user_model
User = get_user_model()

class Encadreur(models.Model):
    prenoms     = models.CharField(max_length=100, verbose_name= 'Prénom(s)')
    nom         = models.CharField(max_length=100, verbose_name= 'Nom')
    email       = models.EmailField(blank=True, null=True, verbose_name= 'Email')
    ajouter_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,on_delete=models.SET_NULL)
    slug        = models.SlugField(max_length=255, unique=True, editable=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    @property
    def ImageUrl(self):
        try:
            url = self.photo.url
        except:
            url = ''
        return url 

    @property
    def full_name(self):
        return f"{self.prenoms} {self.nom}"

    def __str__(self):
        return self.full_name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.full_name) + '-' + get_random_string(5)
        super(Encadreur, self).save(*args, **kwargs)

    class Meta:
        db_table = 'encadreur'
        verbose_name = 'encadreur'
        verbose_name_plural = 'encadreurs'