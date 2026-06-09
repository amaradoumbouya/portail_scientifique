from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.contrib.auth import  get_user_model

User = get_user_model()

class TypeDocument(models.Model):
    libelle    = models.CharField(max_length=100, verbose_name='Type Document')
    slug       = models.SlugField(max_length=255, unique=True, editable=False)
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='type_document')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



    def __str__(self):
        return self.libelle
    

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.libelle) + '-' + get_random_string(5)
        super(TypeDocument, self).save(*args, **kwargs)

    class Meta:
        db_table = 'type_document'
        verbose_name = 'types_document'
        verbose_name_plural = 'types_document'

