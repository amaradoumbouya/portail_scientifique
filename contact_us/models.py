from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.contrib.auth import  get_user_model

User = get_user_model()


class ContactUs(models.Model):
    nom_complet        = models.CharField(max_length=225, verbose_name='Nom complet')
    email              = models.EmailField(verbose_name='Email')
    slug               = models.SlugField(max_length=255, unique=True, editable=False)
    objectif           = models.CharField(max_length=255, verbose_name='Objet')
    message            = models.TextField(verbose_name='Message')
    reponse_au_message = models.TextField(verbose_name='Reponse')
    is_read            = models.BooleanField(default=False)
    user               = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now_add=True)

    @property
    def full_name(self):
        return self.nom_complet

    def __str__(self):
        return self.full_name
    

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom_complet) + '-' + get_random_string(5)
        super(ContactUs, self).save(*args, **kwargs)

    class Meta:
        db_table = 'contact_us'
        verbose_name = 'contact_us'
        verbose_name_plural = 'contact_us'