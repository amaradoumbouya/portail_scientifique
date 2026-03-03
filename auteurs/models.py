from django.db import models
from django.utils.text import slugify
from institutions.models import Institution
from django.conf import settings
from django.contrib.auth import  get_user_model

User = get_user_model()


class Auteur(models.Model):
    STATUT = (
        ('Enseignant', 'Enseignant'),
        ('Doctorant', 'Doctorant'),
        ('Chercheur', 'Chercheur'),
        ('Autre', 'Autre')
    )
    photo       = models.ImageField(upload_to='auteurs/photos/', blank=True, null=True)
    nom         = models.CharField(max_length=100, verbose_name= 'Nom')
    prenoms     = models.CharField(max_length=100, verbose_name= 'Prénom(s)')
    email       = models.EmailField(blank=True, null=True, verbose_name= 'Email')
    orcid       = models.CharField(max_length=50, blank=True, null=True, verbose_name= 'Orcid')
    statut      = models.CharField(max_length=50, choices=STATUT, verbose_name= 'Statut')
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, verbose_name= 'Institution')
    # Réseaux sociaux
    facebook    = models.URLField(blank=True, null=True)
    twitter     = models.URLField(blank=True, null=True)
    linkedin    = models.URLField(blank=True, null=True)
    site_web    = models.URLField(blank=True, null=True)
    biographie  = models.TextField(blank=True, null=True, help_text="Résumé du parcours académique et professionnel")
    slug        = models.SlugField(max_length=255, unique=True, editable=False)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
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
            last_pk = Auteur.objects.order_by('pk').last()
            self.slug = slugify(self.full_name) + '-' + str(last_pk.pk + 1) if last_pk else '1'
        super(Auteur, self).save(*args, **kwargs)

    class Meta:
        db_table = 'auteur'
        verbose_name = 'auteur'
        verbose_name_plural = 'auteurs'
