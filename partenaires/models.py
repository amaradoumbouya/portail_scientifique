from django.db import models
from django.utils.text import slugify
from django.contrib.auth import  get_user_model
User = get_user_model()

class Partenaire(models.Model):
    nom = models.CharField(max_length=255, verbose_name="Nom du partenaire")
    logo = models.ImageField(upload_to='partenaires/logos/', blank=True, null=True, verbose_name="Logo")
    site_web = models.URLField(blank=True, verbose_name="Site Web")
    email = models.EmailField(blank=True, verbose_name="Email de contact")
    telephone = models.CharField(max_length=50, blank=True, verbose_name="Téléphone")
    adresse = models.CharField(max_length=255, blank=True, verbose_name="Adresse")
    description = models.TextField(blank=True, verbose_name="Description")
    slug        = models.SlugField(max_length=255, unique=True, editable=False)
    user        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_ajout = models.DateTimeField(auto_now_add=True)
    is_actif = models.BooleanField(default=True, verbose_name="Actif ?")



    @property
    def ImageUrl(self):
        try:
            url = self.logo.url
        except:
            url = ''
        return url


    def __str__(self):
        return self.nom
    
    def save(self, *args, **kwargs):
        if not self.slug:
            last_pk = Partenaire.objects.order_by('pk').last()
            self.slug = slugify(self.nom) + '-' + str(last_pk.pk + 1) if last_pk else '1'
        super(Partenaire, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Partenaire"
        verbose_name_plural = "Partenaires"
        ordering = ['-date_ajout']