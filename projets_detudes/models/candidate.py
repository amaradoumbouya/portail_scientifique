from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.crypto import get_random_string


    
class Candidate(models.Model):
    NIVEAU = (
        ('master', 'Master'),
        ('doctorat', 'Doctorat'),
    )
    user                   = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='candidate')
    adresse                = models.CharField(max_length=150, blank=True, null=True, verbose_name='Adresse :')
    matricule              = models.CharField(max_length=50, unique=True)
    niveau                 = models.CharField(max_length=20, choices=NIVEAU)
    domaine                = models.CharField(max_length=150)
    sujet_recherche        = models.TextField(blank=True, null=True)
    annee_inscription      = models.DateTimeField(null=True, blank=True)
    institution            = models.ForeignKey("institutions.Institution", on_delete=models.SET_NULL, null=True)
    orcid                  = models.CharField(max_length=150,blank=True, null=True, verbose_name='ORCID :')
    photo                  = models.ImageField(upload_to='accounts', blank=True, null=True, verbose_name='Photo :')
    reseau_social_facebook = models.URLField(blank=True, null=True, verbose_name= "Facebook")
    reseau_social_twitter  = models.URLField(blank=True, null=True, verbose_name= "Twitter")
    reseau_social_linkedin = models.URLField(blank=True, null=True, verbose_name= "LinkedIn")
    reseau_social_youtube  = models.URLField(blank=True, null=True, verbose_name= "YouTube")
    site_web               = models.URLField(blank=True, null=True, verbose_name="Site web")
    slug                   = models.SlugField(max_length=255, unique=True, editable=False)
    created_at             = models.DateTimeField(auto_now_add=True)
    updated_at             = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.user)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.user.full_name) + '-' + get_random_string(5)
        super(Candidate, self).save(*args, **kwargs)