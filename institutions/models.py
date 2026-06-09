from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.utils.crypto import get_random_string



class Institution(models.Model):
    TYPE_INSTITUTION = (
        ('Université', 'Université'),
        ('Centre de documentation', 'Centre de documentation'),
        ('Centre de recherche scientifique', 'Centre de recherche scientifique(CRS/IRS)'),
        ("Institution d'enseignement supérieur", "Institution d'enseignement supérieur"),
    )
    type_institution             = models.CharField(max_length=50, blank=True, null=True, choices=TYPE_INSTITUTION, verbose_name= "Type d'Institution")
    nom_institution              = models.CharField(max_length=255, verbose_name= "Nom de l'Institution")
    slug                         = models.SlugField(max_length=255, unique=True, editable=False)
    sigle_institution            = models.CharField(max_length=20, verbose_name= "Sigle de l'Institution")
    email_institution            = models.EmailField(verbose_name= "Email de l'Institution")
    telephone_institution        = models.CharField(max_length=20, default=0, verbose_name= "Téléphone de l'Institution")
    adresse_institution          = models.CharField(max_length=30, verbose_name= "Adresse de l'Institution")
    ville                        = models.CharField(max_length=20, blank=True, null=True, verbose_name= "Ville")
    pays                         = models.CharField(max_length=20, blank=True, null=True, default='Guinée', verbose_name= "Pays")
    ror                          = models.CharField(max_length=255, verbose_name= "ROR")
    site_web_institution         = models.URLField(verbose_name= "Site web")
    logo_institution             = models.ImageField(upload_to='institutions/logos/', blank=True, null=True, verbose_name= "Logo de l'Institution")
    reseau_social_facebook_inst  = models.URLField(blank=True, null=True, verbose_name= "Facebook")
    reseau_social_twitter_inst   = models.URLField(blank=True, null=True, verbose_name= "Twitter")
    reseau_social_linkedin_inst  = models.URLField(blank=True, null=True, verbose_name= "LinkedIn")
    reseau_social_youtube_inst   = models.URLField(blank=True, null=True, verbose_name= "YouTube")
    user                         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='institutions')
    created_at                   = models.DateTimeField(auto_now_add=True)
    updated_at                   = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom_institution
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom_institution) + '-' + get_random_string(5)
        super(Institution, self).save(*args, **kwargs)

    class Meta:
        db_table = 'institution'
        verbose_name = 'institution'
        verbose_name_plural = 'institutions'
