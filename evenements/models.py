from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string


class Evenement(models.Model):
    class TypeEvenement(models.TextChoices):
        CONFERENCE = 'conference', 'Conférence'
        ATELIER = 'atelier', 'Atelier'

    titre = models.CharField(max_length=255, verbose_name='Titre')
    type_evenement = models.CharField(
        max_length=20,
        choices=TypeEvenement.choices,
        default=TypeEvenement.CONFERENCE,
        verbose_name="Type d'événement",
    )
    description = models.TextField(verbose_name='Description')
    image = models.ImageField(
        upload_to='evenements/images/',
        blank=True,
        null=True,
        verbose_name='Image',
    )
    date_evenement = models.DateTimeField(verbose_name="Date de l'événement")
    lieu = models.CharField(max_length=255, blank=True, verbose_name='Lieu')
    lien_inscription = models.URLField(blank=True, verbose_name="Lien d'inscription")
    lien_details = models.URLField(blank=True, verbose_name='Lien détails')
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    is_actif = models.BooleanField(default=True, verbose_name='Actif ?')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'evenement'
        verbose_name = 'Événement'
        verbose_name_plural = 'Événements'
        ordering = ['date_evenement']

    def __str__(self):
        return self.titre

    @property
    def ImageUrl(self):
        try:
            return self.image.url
        except Exception:
            return ''

    @property
    def bouton_inscription(self):
        if self.type_evenement == self.TypeEvenement.ATELIER:
            return 'Participer'
        return "S’inscrire"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titre) + '-' + get_random_string(5)
        super().save(*args, **kwargs)


class InscriptionEvenement(models.Model):
    evenement = models.ForeignKey(
        Evenement,
        on_delete=models.CASCADE,
        related_name='inscriptions',
        verbose_name='Événement',
    )
    prenoms = models.CharField(max_length=150, verbose_name='Prénom(s)')
    nom = models.CharField(max_length=150, verbose_name='Nom')
    email = models.EmailField(verbose_name='Email')
    telephone = models.CharField(max_length=30, blank=True, verbose_name='Téléphone')
    institution = models.CharField(max_length=255, blank=True, verbose_name='Institution')
    message = models.TextField(blank=True, verbose_name='Message')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inscription_evenement'
        verbose_name = "Inscription à un événement"
        verbose_name_plural = "Inscriptions aux événements"
        ordering = ['-created_at']
        unique_together = ('evenement', 'email')

    def __str__(self):
        return f"{self.prenoms} {self.nom} – {self.evenement.titre}"
