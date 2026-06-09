from django.db import models
from django.utils.text import slugify
from auteurs.models import Auteur
from encadreurs.models import Encadreur
from types_document.models import TypeDocument
from institutions.models import Institution
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import  get_user_model

User = get_user_model()


class Publication(models.Model):
    class TypePublication(models.TextChoices):
        ARTICLE = "article", "Article scientifique"
        COLLOQUE = "colloque", "Communication de Colloque"

    class StatutIndexation(models.TextChoices):
        EN_ATTENTE = "En attente", "En attente"
        ACCEPTEE = "Acceptée", "Acceptée"
        REJETEE = "Rejetée", "Rejetée"
        
    photo                       = models.ImageField(upload_to='publicatons/photos', blank=True, null=True, verbose_name='Photo :')
    titre                       = models.CharField(max_length=300, blank=True, null=True, verbose_name= 'Titre')
    type_publication            = models.CharField(max_length=50, choices=TypePublication.choices, default='', verbose_name= 'Type du publication')
    domaine                     = models.CharField(max_length=100, blank=True, null=True, verbose_name= 'Domaine')
    fichier_pdf                 = models.FileField(upload_to='publications/fichiers', verbose_name= 'Fichier')
    langue                      = models.CharField(max_length=50, blank=True, default='français', verbose_name= 'Langue')
    doi                         = models.CharField(max_length=100, blank=True, null=True, verbose_name= 'Doi')
    statut_indexation           = models.CharField(max_length=50, choices=StatutIndexation.choices, default='En attente', verbose_name= 'Statut indexation')
    motif_rejet                 = models.TextField(blank=True, null=True, verbose_name='Motif rejet')
    mots_cles                   = models.TextField(blank=True, null=True, verbose_name='Mots cles')
    resume                      = models.TextField(blank=True, null=True, verbose_name= 'Resumé')
    texte_integral              = models.TextField(blank=True, null=True, verbose_name="Texte intégral")
    texte_nettoye               = models.TextField(blank=True, null=True, verbose_name="Texte nettoyé")
    statut_publication          = models.BooleanField(default=False)
    user                        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="publications")
    slug                        = models.SlugField(max_length=255, unique=True, editable=False)
    date_ajout_systeme          = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at                  = models.DateTimeField(auto_now=True)

    def get_real_instance(self):
        if hasattr(self, 'article'):
            return self.article
        elif hasattr(self, 'colloque'):
            return self.colloque
        return self


    def indexer(self, fichier):
        from publications.nlp_tools import (extraire_texte_du_pdf, nettoyer_texte, extraire_resume, extraire_mots_cles, classifier_domaine)

        try:
            # ==========================
            # EXTRACTION TEXTE
            # ==========================
            fichier.seek(0)
            texte = extraire_texte_du_pdf(fichier)

            if not texte or len(texte.strip()) < 300:

                self.statut_indexation = 'Rejetée'

                self.motif_rejet = (
                    "Le texte extrait est vide "
                    "ou trop court pour être analysé."
                )

                return
            
            # ==========================
            # SAUVEGARDE TEXTE BRUT
            # ==========================
            self.texte_integral = texte



            # ==========================
            # NETTOYAGE NLP
            # ==========================
            texte_nettoye = nettoyer_texte(texte)
            self.texte_nettoye = texte_nettoye


            # ==========================
            # EXTRACTION RESUME
            # ==========================
            resume = extraire_resume(texte)

            self.resume = resume



            # ==========================
            # EXTRACTION MOTS CLES
            # ==========================
            mots_cles = extraire_mots_cles(texte_nettoye)
            self.mots_cles = mots_cles

            # ==========================
            # CLASSIFICATION DOMAINE
            # ==========================
            domaine = classifier_domaine(texte)
            self.domaine = domaine


            # ==========================
            # VALIDATION
            # ==========================
            if not resume:

                self.statut_indexation = 'Rejetée'

                self.motif_rejet = ("Résumé introuvable.")

            elif not mots_cles:

                self.statut_indexation = 'Rejetée'

                self.motif_rejet = ("Mots-clés introuvables.")

            elif domaine == "Autres":

                self.statut_indexation = 'En attente'

                self.motif_rejet = ("Domaine non identifié.")

            else:

                self.statut_indexation = 'Acceptée'

                self.statut_publication = True

                self.motif_rejet = ""
  
        except Exception as e:
            self.statut_indexation = 'Rejetée'
            self.motif_rejet = f"Erreur lors de l’analyse automatique : {str(e)}"


    def get_notification_content(self):

        subject = f"Statut de votre publication: {self.titre}"

        message = f"""

        Bonjour {self.user}, votre publication intitulée {self.titre} a été traitée.

        Statut : {self.statut_indexation}.

        {f"❌ Motif du rejet: {self.motif_rejet}" if self.statut_indexation == 'Rejetée' or self.statut_indexation == 'En attente' else "✅ Elle a été Acceptée avec succès."}.

        Vous pouvvez consultez le detail ici {f"http://127.0.0.1:8000/publications/detail-publication/{self.slug}/"}

        Merci pour votre contribution Scientifique.

        L'equipe du portail """

        return subject, message


    def send_notification_email(self):

        if self.user and self.user.email:

            subject, message = self.get_notification_content()

            send_mail(

                subject = subject,

                message = message,

                from_email=settings.DEFAULT_FROM_EMAIL,

                recipient_list=[self.user.email],

                fail_silently=False
            )

    @property
    def ImageUrl(self):
        try:
            url = self.photo.url
        except:
            url = ''
        return url

    @property
    def full_name(self):
        return f"{self.titre} {self.langue}"

    def __str__(self):
        return self.full_name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            last_pk = Publication.objects.order_by('pk').last()
            self.slug = slugify(self.full_name) + '-' + str(last_pk.pk + 1) if last_pk else '1'
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'publication'
        verbose_name = 'publication'
        verbose_name_plural = 'publications'



# Models pour la publications des articles scientifiques
class ArticleScientifique(Publication):
    nom_revue = models.CharField(max_length=225)
    lien_article = models.URLField(max_length=500, blank=True, null=True, verbose_name="Lien de l'article")
    facteur_impact = models.FloatField(blank=True, null=True)

# Models pour la publications des communications de colloque
class Colloque(Publication):
    nom_colloque = models.CharField(max_length=225)
    lieu = models.CharField(max_length=255, blank=True, null=True)
    date_colloque = models.DateField(blank=True, null=True)

# Models pour gérer l'ordre des auteurs ajouter
class PublicationAuteur(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=30, default='')
    ordre = models.PositiveIntegerField()
    class Meta:
        ordering = ['ordre']
        unique_together = ('publication', 'ordre')

    def __str__(self):
        return f"{self.auteur} (ordre {self.ordre})"
    
# Models for likes
class PublicationLike(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='likes')
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    liked_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('publication', 'user')
        db_table = 'publicationLike'

# Models for comments
class PublicationComment(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='comments')
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contenu     = models.TextField()
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'publicationComment'

# Models for downloads
class PublicationDownload(models.Model):
    publication   = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='downloads')
    ip_address    = models.GenericIPAddressField(null=True, blank=True)
    user          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'publicationDownload'