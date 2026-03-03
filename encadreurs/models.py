from django.db import models
from django.utils.text import slugify
from institutions.models import Institution
from django.conf import settings
from django.contrib.auth import  get_user_model

User = get_user_model()

class Encadreur(models.Model):
    GRADE = (
        ('Professeur', 'Professeur'),
        ('Maître de conférences', 'Maître de conférences'),
        ('Docteur', 'Docteur'),
        ('Autre', 'Autre')
    )
    photo       = models.ImageField(upload_to='encadreurs/photos/', blank=True, null=True)
    prenoms     = models.CharField(max_length=100, verbose_name= 'Prénom(s)')
    nom         = models.CharField(max_length=100, verbose_name= 'Nom')
    slug        = models.SlugField(max_length=255, unique=True, editable=False)
    email       = models.EmailField(blank=True, null=True, verbose_name= 'Email')
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, verbose_name= 'Institution')
    grade       = models.CharField(max_length=100, choices=GRADE, default='Autre', verbose_name= 'Grade')
    specialite  = models.CharField(max_length=200, help_text="Ex: Intelligence Artificielle, Biologie moléculaire...", verbose_name= 'Spécialité')
    # Réseaux sociaux
    facebook    = models.URLField(blank=True, null=True)
    twitter     = models.URLField(blank=True, null=True)
    linkedin    = models.URLField(blank=True, null=True)
    site_web    = models.URLField(blank=True, null=True)
    parcours    = models.TextField(blank=True, help_text="Résumé du parcours académique et professionnel", verbose_name= 'Parcours')
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
            last_pk = Encadreur.objects.order_by('pk').last()
            self.slug = slugify(self.full_name) + '-' + str(last_pk.pk + 1) if last_pk else '1'
        super(Encadreur, self).save(*args, **kwargs)

    class Meta:
        db_table = 'encadreur'
        verbose_name = 'encadreur'
        verbose_name_plural = 'encadreurs'