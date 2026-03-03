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
    STATUT_INDEXATION = (
        ('En attente', 'En attente'),
        ('Acceptée', 'Acceptée'), # J'ai changé 'Indexée' en 'Acceptée' avant d'avoir plus de clarté sur l'idée d'indexation
        ('Rejetée', 'Rejetée')
    )
    photo                       = models.ImageField(upload_to='publicatons/photos', blank=True, null=True, verbose_name='Photo :')
    titre                       = models.CharField(max_length=300, blank=True, null=True, verbose_name= 'Titre')
    auteurs                     = models.ManyToManyField(Auteur, blank=True, null=True, verbose_name= 'Auteur(s)')
    encadreurs                  = models.ManyToManyField(Encadreur, blank=True, null=True, verbose_name= 'Encadreur(s)')
    type_document               = models.ForeignKey(TypeDocument, on_delete=models.SET_NULL, null=True, verbose_name= 'Type du document')
    domaine                     = models.CharField(max_length=100, blank=True, null=True, verbose_name= 'Domaine')
    date_publication            = models.DateField( verbose_name= 'Date')
    fichier_pdf                 = models.FileField(upload_to='publications/fichiers', verbose_name= 'Fichier')
    langue                      = models.CharField(max_length=50, default='français', verbose_name= 'Langue')
    institutions_contributrices = models.ManyToManyField(Institution, related_name='publications_contribuees', blank=True, null=True, verbose_name= 'Institution(s)')
    doi                         = models.CharField(max_length=100, blank=True, null=True, verbose_name= 'Doi')
    orcid_auteur_principal      = models.CharField(max_length=100, blank=True, null=True, verbose_name= 'Orcid')
    statut_indexation           = models.CharField(max_length=50, choices=STATUT_INDEXATION, default='En attente', verbose_name= 'Statut indexation')
    motif_rejet                 = models.TextField(blank=True, null=True, verbose_name='Motif rejet')
    mots_cles                   = models.TextField(blank=True, verbose_name='Mots cles')
    resume                      = models.TextField(blank=True, null=True, verbose_name= 'Resumé')
    statut_publication          = models.BooleanField(default=False)
    nom_revue                   = models.CharField(max_length=225, blank=True, null=True, verbose_name='Nom de la revue')
    nom_colloque                = models.CharField(max_length=225, blank=True, null=True, verbose_name='Nom du colloque')
    lien_article                = models.URLField(max_length=500, blank=True, null=True, verbose_name="Lien de l'article")
    user                        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    slug                        = models.SlugField(max_length=255, unique=True, editable=False)
    date_ajout_systeme          = models.DateTimeField(auto_now_add=True)
    updated_at                  = models.DateTimeField(auto_now=True)


    def indexer(self, fichier):
        from publications.nlp_tools import (extraire_texte_du_pdf, extraire_resume_et_mots_cles, classifier_domaine)

        try:
            fichier.seek(0)
            texte = extraire_texte_du_pdf(fichier)
            if not texte or len(texte.strip()) < 300:
                self.statut_indexation = 'Rejetée'
                self.motif_rejet = "Le texte extrait est vide ou trop court pour être analysé."
                return

            resume, mots_cles = extraire_resume_et_mots_cles(texte)
            domaine = classifier_domaine(texte)

            self.resume = resume
            self.mots_cles = mots_cles
            self.domaine = domaine

            # Règles semi-automatiques : présence d'éléments obligatoires
            if self.type_document == '1':  # Communication scientifique

                if not resume:
                    self.statut_indexation = 'Rejetée'
                    self.motif_rejet = "Aucun résumé n'a pu être généré."
                elif not mots_cles:
                    self.statut_indexation = 'Rejetée'
                    self.motif_rejet = "Les mots-clés n'ont pas pu extraits."
                elif not domaine or domaine == 'Autres':
                    self.statut_indexation =  'Rejetée'
                    self.motif_rejet  = "Le domaine n'a pas pu être identifié."
                elif not self.auteurs.exists():
                    self.statut_indexation = 'En attente'
                    self.motif_rejet = "Informations incomplètes(auteurs manquants)."
                else:
                    self.statut_indexation = 'Acceptée'
                    self.statut_publication = True
                    self.motif_rejet = ""

            elif self.type_document == '5':  # Article scientifique

                if not resume:
                    self.statut_indexation = 'Rejetée'
                    self.motif_rejet = "Aucun résumé n'a pu être généré."
                elif not mots_cles:
                    self.statut_indexation = 'Rejetée'
                    self.motif_rejet = "Les mots-clés n'ont pas pu extraits."
                elif not domaine or domaine == 'Autres':
                    self.statut_indexation =  'Rejetée'
                    self.motif_rejet  = "Le domaine n'a pas pu être identifié."
                elif not (self.auteurs.exists() and self.nom_revue.exists() and self.lien_article.exists()):
                    self.statut_indexation = 'En attente'
                    self.motif_rejet = "Informations incomplètes(auteurs, nom de la vue ou le lien de l'article manquants)."
                else:
                    self.statut_indexation = 'Acceptée'
                    self.statut_publication = True
                    self.motif_rejet = ""

            elif self.type_document == '2' or self.type_document == '3': # Thèse ou Mémoire

                if not resume:
                    self.statut_indexation = 'Rejetée'
                    self.motif_rejet = "Aucun résumé n'a pu être généré."
                elif not mots_cles:
                    self.statut_indexation = 'Rejetée'
                    self.motif_rejet = "Les mots-clés n'ont pas pu extraits."
                elif not domaine or domaine == 'Autres':
                    self.statut_indexation =  'Rejetée'
                    self.motif_rejet  = "Le domaine n'a pas pu être identifié."
                elif not (self.auteurs.exists() and self.encadreurs.exists() and self.institutions_contributrices.exists()):
                    self.statut_indexation = 'En attente'
                    self.motif_rejet = "Informations incomplètes(auteurs, encadreurs ou institutions manquants)."
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
        super(Publication, self).save(*args, **kwargs)

    class Meta:
        db_table = 'publication'
        verbose_name = 'publication'
        verbose_name_plural = 'publications'


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