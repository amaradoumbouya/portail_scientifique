from django.db import models
from django.utils.text import slugify
from django.urls import reverse
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
        MEMOIRE = "memoire", "Mémoire"
        THESE = "these", "Thèse"

    class StatutIndexation(models.TextChoices):
        EN_ATTENTE = "En attente", "En attente"
        ACCEPTEE = "Acceptée", "Acceptée"
        REJETEE = "Rejetée", "Rejetée"

    class Licence(models.TextChoices):
        CC_BY = "CC-BY-4.0", "CC BY 4.0 — Attribution"
        CC_BY_SA = "CC-BY-SA-4.0", "CC BY-SA 4.0 — Attribution, Partage à l'identique"
        CC_BY_NC = "CC-BY-NC-4.0", "CC BY-NC 4.0 — Pas d'utilisation commerciale"
        CC_BY_NC_SA = "CC-BY-NC-SA-4.0", "CC BY-NC-SA 4.0"
        CC_BY_ND = "CC-BY-ND-4.0", "CC BY-ND 4.0 — Pas de modification"
        CC_BY_NC_ND = "CC-BY-NC-ND-4.0", "CC BY-NC-ND 4.0"
        TOUS_DROITS = "tous-droits-reserves", "Tous droits réservés"

    LICENCE_URLS = {
        "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
        "CC-BY-SA-4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
        "CC-BY-NC-4.0": "https://creativecommons.org/licenses/by-nc/4.0/",
        "CC-BY-NC-SA-4.0": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "CC-BY-ND-4.0": "https://creativecommons.org/licenses/by-nd/4.0/",
        "CC-BY-NC-ND-4.0": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
    }

    photo                       = models.ImageField(upload_to='publicatons/photos', blank=True, null=True, verbose_name='Photo :')
    titre                       = models.CharField(max_length=300, blank=True, null=True, verbose_name= 'Titre')
    type_publication            = models.CharField(max_length=50, choices=TypePublication.choices, default='', verbose_name= 'Type du publication')
    domaine                     = models.CharField(max_length=100, blank=True, null=True, verbose_name= 'Domaine')
    fichier_pdf                 = models.FileField(upload_to='publications/fichiers', verbose_name= 'Fichier')
    langue                      = models.CharField(max_length=50, blank=True, default='français', verbose_name= 'Langue')
    doi                         = models.CharField(max_length=100, blank=True, null=True, verbose_name= 'Doi')
    statut_indexation           = models.CharField(max_length=50, choices=StatutIndexation.choices, default='En attente', verbose_name= 'Statut indexation')
    bases_indexation            = models.CharField(max_length=255, blank=True, null=True, verbose_name='Bases d\'indexation')
    motif_rejet                 = models.TextField(blank=True, null=True, verbose_name='Motif rejet')
    mots_cles                   = models.TextField(blank=True, null=True, verbose_name='Mots cles')
    resume                      = models.TextField(blank=True, null=True, verbose_name= 'Resumé')
    texte_integral              = models.TextField(blank=True, null=True, verbose_name="Texte intégral")
    texte_nettoye               = models.TextField(blank=True, null=True, verbose_name="Texte nettoyé")
    statut_publication          = models.BooleanField(default=False)
    licence                     = models.CharField(
        max_length=40,
        choices=Licence.choices,
        default=Licence.CC_BY,
        blank=True,
        verbose_name='Licence',
    )
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

    def get_absolute_url(self):
        return reverse('portail_site:detail_publication', kwargs={'slug': self.slug})

    @property
    def licence_url(self):
        return self.LICENCE_URLS.get(self.licence or '')

    @property
    def citation_language(self):
        langue = (self.langue or 'fr').strip().lower()
        mapping = {
            'fr': 'fr', 'français': 'fr', 'francais': 'fr', 'french': 'fr',
            'en': 'en', 'anglais': 'en', 'english': 'en',
            'es': 'es', 'espagnol': 'es', 'spanish': 'es',
            'pt': 'pt', 'portugais': 'pt', 'portuguese': 'pt',
        }
        return mapping.get(langue, 'fr')

    @property
    def doi_url(self):
        identifiant = self.doi_identifiant
        if not identifiant:
            return ''
        return f'https://doi.org/{identifiant}'

    @property
    def doi_identifiant(self):
        doi = (self.doi or '').strip()
        prefixes = (
            'https://doi.org/',
            'http://doi.org/',
            'https://dx.doi.org/',
            'http://dx.doi.org/',
        )
        lower = doi.lower()
        for prefix in prefixes:
            if lower.startswith(prefix):
                return doi[len(prefix):]
        return doi


    def indexer(self, fichier, verifier_international=True, motifs_prealables=None):
        """
        1) Enrichissement NLP (texte, résumé, mots-clés, domaine, langue)
        2) Enregistrement du modèle Indexation
        3) Niveau 1 — affiliations / auteurs (institutions inscrites)
        4) Niveau 2 — indexation internationale (Scopus, WoS, DOAJ, AJOL)

        Un article ou une communication de colloque n'est Accepté(e) que si :
        - les institutions citées sont inscrites sur la plateforme ;
        - les auteurs sont affiliés à ces institutions ;
        - puis la revue/article est reconnu dans Scopus, WoS, DOAJ ou AJOL.

        Les mémoires / thèses passent uniquement par l'indexation NLP locale.
        """
        from publications.nlp_tools import (
            extraire_texte_du_pdf,
            nettoyer_texte,
            extraire_resume,
            extraire_mots_cles,
            classifier_domaine,
            detecter_langue,
            calculer_score_pertinence,
            enrichir_meta_depuis_doi,
            verifier_indexation_internationale,
        )
        from publications.verification_affiliations import (
            verifier_affiliations_et_auteurs,
        )
        from indexations.models import Indexation

        # Verrou métier : articles et colloques ne peuvent pas contourner
        # la vérification internationale, même si l'appelant passe False.
        if self.type_publication in (
            self.TypePublication.ARTICLE,
            self.TypePublication.COLLOQUE,
            'article',
            'colloque',
        ):
            verifier_international = True

        if verifier_international:
            self.statut_indexation = 'En attente'
            self.bases_indexation = ''
            self.motif_rejet = "Vérification des affiliations en cours…"

        texte = ""
        try:
            fichier.seek(0)
            texte = extraire_texte_du_pdf(fichier) or ""
            self.langue = detecter_langue(texte)

            if texte and len(texte.strip()) >= 300:
                self.texte_integral = texte
                texte_nettoye = nettoyer_texte(texte)
                self.texte_nettoye = texte_nettoye
                self.resume = extraire_resume(texte)
                self.mots_cles = extraire_mots_cles(texte_nettoye) if texte_nettoye.strip() else ""
                self.domaine = classifier_domaine(texte)
            else:
                self.texte_integral = texte
                if verifier_international:
                    self.motif_rejet = (
                        "Texte PDF court ou vide — enrichissement NLP limité. "
                        "Vérification des affiliations en cours…"
                    )

        except Exception as e:
            if verifier_international:
                self.motif_rejet = (
                    f"Enrichissement NLP partiel ({e}). "
                    "Vérification des affiliations en cours…"
                )

        score = calculer_score_pertinence(
            texte or self.texte_integral or "",
            self.mots_cles or "",
            self.domaine or "",
        )
        if self.pk:
            Indexation.objects.update_or_create(
                publication=self,
                defaults={
                    'mots_cles_ai': self.mots_cles or '',
                    'resume_ia': self.resume or '',
                    'score_pertinence': score,
                    'outil_indexation': 'spaCy + TF-IDF + NLTK',
                },
            )

        if not verifier_international:
            self.statut_indexation = 'Acceptée'
            self.statut_publication = True
            self.bases_indexation = 'Portail CRICT (NLP)'
            self.motif_rejet = ''
            return

        texte_pdf = texte or self.texte_integral or ""
        meta_doi = enrichir_meta_depuis_doi(self.doi) if self.doi else None

        # --------------------------------------------------
        # Niveau 1 : institutions inscrites + affiliations
        # --------------------------------------------------
        resultat_aff = verifier_affiliations_et_auteurs(
            self,
            texte_pdf=texte_pdf,
            meta_externes=meta_doi,
        )
        motifs_niveau1 = list(motifs_prealables or [])
        if resultat_aff.get("statut") == "Rejetée":
            motifs_niveau1.insert(0, resultat_aff.get("motif") or (
                "Affiliations ou auteurs non conformes aux institutions "
                "inscrites sur la plateforme."
            ))
        if motifs_niveau1:
            self.statut_indexation = "Rejetée"
            self.statut_publication = False
            self.bases_indexation = ""
            self.motif_rejet = " ".join(motifs_niveau1)
            return

        # --------------------------------------------------
        # Niveau 2 : Scopus / WoS / DOAJ / AJOL
        # --------------------------------------------------
        nom_revue = None
        try:
            real = self.get_real_instance()
            nom_revue = getattr(real, 'nom_revue', None)
        except Exception:
            nom_revue = None

        resultat = verifier_indexation_internationale(
            doi=self.doi,
            nom_revue=nom_revue,
            texte_pdf=texte_pdf,
            titre=self.titre,
            meta=meta_doi,
        )

        self.statut_indexation = resultat.get('statut', 'En attente')
        bases = resultat.get('bases') or []
        self.bases_indexation = ", ".join(bases) if bases else ""

        if self.statut_indexation == 'Acceptée':
            self.statut_publication = True
            self.motif_rejet = ""
        elif self.statut_indexation == 'Rejetée':
            self.statut_publication = False
            self.motif_rejet = resultat.get('motif') or (
                "Non reconnu dans Scopus, WoS, DOAJ ni AJOL."
            )
        else:
            self.motif_rejet = resultat.get('motif') or (
                "Vérification d'indexation en cours…"
            )


    def get_notification_content(self):

        subject = f"Statut de votre publication: {self.titre}"

        message = f"""

        Bonjour {self.user}, votre publication intitulée {self.titre} a été traitée.

        Statut : {self.statut_indexation}.

        {f"❌ Motif: {self.motif_rejet}" if self.statut_indexation in ('Rejetée', 'En attente') else f"✅ Indexation acceptée ({self.bases_indexation or 'base internationale'})."}.

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