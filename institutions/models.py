from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.contrib.auth import  get_user_model

User = get_user_model()


class Institution(models.Model):
    TYPE_INSTITUTION = (
        ('Université', 'Université'),
        ('Centre de recherche', 'Centre de recherche'),
    )
    nom = models.CharField(max_length=255, verbose_name= "Nom de l'Institution")
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    type = models.CharField(max_length=100, choices=TYPE_INSTITUTION, verbose_name= "Type")
    ville = models.CharField(max_length=100, verbose_name= "Ville")
    pays = models.CharField(max_length=100, default='Guinée', verbose_name= "Pays")
    site_web = models.URLField(blank=True, null=True, verbose_name= "Site web")
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        return f"{self.nom} {self.type}"

    def __str__(self):
        return self.full_name
    

    def save(self, *args, **kwargs):
        if not self.slug:
            last_pk = Institution.objects.order_by('pk').last()
            self.slug = slugify(self.full_name) + '-' + str(last_pk.pk + 1) if last_pk else '1'
        super(Institution, self).save(*args, **kwargs)

    class Meta:
        db_table = 'institution'
        verbose_name = 'institution'
        verbose_name_plural = 'institutions'
