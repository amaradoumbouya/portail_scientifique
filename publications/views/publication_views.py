from django.shortcuts import render, redirect, get_object_or_404
from projets_detudes.models import candidate
from projets_detudes.models.participant import Participant
from projets_detudes.models.projet import ProjetEtude
from publications.models.publication import Publication, PublicationAuteur, Colloque, ArticleScientifique
from auteurs.models import Auteur
from encadreurs.models import Encadreur
from publications.forms.publication_forms import PublicationForm,ArticleForm, ColloqueForm
from publications.coauteurs import resoudre_auteurs_cites, enregistrer_coauteurs
from publications.verification_affiliations import MOTIFS_PREFIXE
from projets_detudes.forms.projet_forms import ProjetForm
from notifications.models import Notification
from auteurs.forms import AuteurForm
from accounts.models import CustumerUser
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from publications.nlp_tools import extraire_texte_du_pdf, nettoyer_texte, extraire_resume, extraire_mots_cles, classifier_domaine
from django.db import transaction
from django.utils.crypto import get_random_string

# Envoi d'un email apres l'inscription sur le portail
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.db import connection
from django.contrib.auth.decorators import login_required

# Pour la vue d'activation du compte apres l'inscription
from django.utils.encoding import force_str


def _message_apres_soumission(request, publication, type_libelle):
    """Informe l'utilisateur du résultat des vérifications (affiliations puis bases internationales)."""
    if publication.statut_indexation == "Rejetée":
        messages.warning(
            request,
            f"Votre {type_libelle} a été soumis mais rejeté. "
            f"Motif : {publication.motif_rejet or 'non conforme.'}"
        )
    elif publication.statut_indexation == "Acceptée":
        messages.success(
            request,
            f"Votre {type_libelle} a été soumis et indexé avec succès."
        )
    else:
        messages.info(
            request,
            f"Votre {type_libelle} a été soumis. "
            "La vérification d'indexation est en cours."
        )


# Vue pour lister toutes les publications effectuées par l'utilisateur
@login_required
def user_publications(request):

    user_publications = Publication.objects.filter(
        publicationauteur__auteur=request.user
    ).distinct().prefetch_related(
        'publicationauteur_set',
        'publicationauteur_set__auteur',
        'publicationauteur_set__auteur__profile',
        'publicationauteur_set__auteur__profile__institution'
    ).order_by('-date_ajout_systeme', '-id')

    return render(
        request,
        'back/publications/index.html',
        {
            'user_publications': user_publications
        }
    )

# Statut publication, pour savoir si la publication est faite oui ou non
def statut_publication(request): 
    if request.method == 'POST':
        idpublier = request.POST.get('idpublier')
        pub = get_object_or_404(Publication, id=idpublier)
        pub.statut_publication = not pub.statut_publication  
        pub.save()

    # Redirection selon le rôle de l'utilisateur
    user = request.user
    if hasattr(user, 'role') and user.role == 'admin':
        return redirect('publications:index')
    else:
        return redirect('portail_site:dashboard')

# Detail_d'une_publication
def detail_publication(request, slug):
    publication = get_object_or_404(
        Publication.objects.prefetch_related(
            'publicationauteur_set',
            'publicationauteur_set__auteur',
            'publicationauteur_set__auteur__profile',
            'publicationauteur_set__auteur__profile__institution',
        ),
        slug=slug,
    )
    return render(request, 'back/publications/detail.html', {'publication': publication})

# Modification_d'une_publication
class PublicationUpdateView(LoginRequiredMixin, UpdateView): 
    model = Publication
    form_class = PublicationForm
    template_name = "back/publications/update.html"
    context_object_name = "publication"

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated and user.role == "admin":
            return reverse_lazy("publications:index")
        else:
            return reverse("publications:index")

    def form_valid(self, form):
        messages.success(self.request, f"publication {self.request.POST.get('titre')} modifié avec succès !")
        response = super().form_valid(form)
        if 'fichier_pdf' in form.changed_data:
            fichier = form.cleaned_data.get('fichier_pdf')
            if fichier:
                self.object.indexer(fichier)
                self.object.save()
        return response

# Suppression_d'une_publication
class PublicationDeleteView(LoginRequiredMixin, DeleteView):
    model = Publication
    template_name = "back/publications/index.html"
    context_object_name = "publication"
    
    def get_success_url(self):
        user = self.request.user
        if hasattr(user, "role") and user.role == "admin":
            return reverse_lazy("publications:index")
        return reverse("publications:index")

# Vue pour le modal article scientifique
def modal_article_scientifique(request):

    # ==========================================
    # INITIALISATION FORMULAIRES
    # ==========================================
    form_publication = PublicationForm()

    form_article = ArticleForm()

    # ==========================================
    # VERIFICATION PROFIL UTILISATEUR
    # ==========================================
    champs_obligatoires = [
        'role',
        'institution',
        'orcid',
        'fonction_poste'
    ]

    profile = getattr(request.user, 'profile', None)

    if not profile:

        messages.error(request,"Profil utilisateur introuvable.")

        return redirect('portail_site:dashboard')

    if not all(getattr(profile, champ, None) for champ in champs_obligatoires):

        messages.warning(request, "Veuillez compléter votre profil.")

        return redirect('accounts:profil_user')

    # ==========================================
    # TRAITEMENT POST
    # ==========================================
    if request.method == "POST":

        form_publication = PublicationForm(request.POST, request.FILES)

        form_article = ArticleForm(request.POST)

        publication_valid = form_publication.is_valid()

        article_valid = form_article.is_valid()

        print("Erreurs publication :", form_publication.errors)

        print("Erreurs article :", form_article.errors)

        if publication_valid and article_valid:

            try:

                # ==========================================
                # RECUPERATION FICHIER PDF
                # ==========================================
                fichier = request.FILES.get('fichier_pdf')

                if not fichier:

                    messages.error(request, "Veuillez ajouter un fichier PDF.")

                    return redirect(request.path)

                # ==========================================
                # VERIFICATION TYPE PDF
                # ==========================================
                if fichier.content_type != 'application/pdf':

                    messages.error(request,"Le fichier doit être au format PDF.")

                    return redirect(request.path)

                # ==========================================
                # VERIFICATION TAILLE PDF
                # ==========================================
                if fichier.size > 20 * 1024 * 1024:

                    messages.error(request,"Le fichier dépasse 20 MB.")

                    return redirect(request.path)

                user = request.user

                # ==========================================
                # TRANSACTION PRINCIPALE
                # ==========================================
                with transaction.atomic():

                    # ==========================================
                    # CREATION PUBLICATION
                    # ==========================================
                    publication = form_publication.save(commit=False)

                    publication.user = (user if user.is_authenticated else None)

                    publication.save()

                    form_publication.save_m2m()

                    print("Publication créée avec succès")

                    # ==========================================
                    # CREATION ARTICLE SCIENTIFIQUE
                    # ==========================================
                    article = form_article.save(commit=False)

                    # IMPORTANT :
                    # héritage multi-table Django
                    article.pk = publication.pk

                    article.user = publication.user

                    article.save()

                    form_article.save_m2m()

                    print("Article scientifique créé")

                    # ==========================================
                    # AUTEUR PRINCIPAL
                    # ==========================================
                    PublicationAuteur.objects.get_or_create(
                        auteur=user,
                        publication=publication,
                        defaults={
                            'role': 'Auteur principal',
                            'ordre': 1
                        }
                    )

                    print("Auteur principal ajouté")

                    from publications.nlp_tools import (
                        extraire_texte_du_pdf,
                        enrichir_meta_depuis_doi,
                    )
                    doi = form_publication.cleaned_data.get("doi") or publication.doi
                    fichier.seek(0)
                    texte_pdf = extraire_texte_du_pdf(fichier) or ""
                    meta_doi = enrichir_meta_depuis_doi(doi) if doi else None

                    analyse_coauteurs = resoudre_auteurs_cites(
                        texte_pdf=texte_pdf,
                        meta_externes=meta_doi,
                        deposant=user,
                    )
                    enregistrer_coauteurs(
                        publication,
                        analyse_coauteurs,
                        request,
                        sujet_existant="Participation à une publication scientifique",
                    )

                    print("Co-auteurs traités")

                    motifs_prealables = []
                    if analyse_coauteurs.get("rejets"):
                        motifs_prealables.append(
                            MOTIFS_PREFIXE
                            + "\n"
                            + "\n".join(analyse_coauteurs["rejets"])
                        )

                    # ==========================================
                    # INDEXATION NLP COMPLETE
                    # ==========================================
                    fichier.seek(0)

                    publication.indexer(
                        fichier,
                        motifs_prealables=motifs_prealables,
                    )

                    publication.save()

                    print("Indexation NLP terminée")

                # ==========================================
                # FIN TRANSACTION
                # ==========================================

                # ==========================================
                # EMAIL NOTIFICATION
                # ==========================================
                publication.send_notification_email()

                print("Email notification envoyé")

                # ==========================================
                # NOTIFICATION INTERNE
                # ==========================================
                subject, message = (publication.get_notification_content())

                Notification.objects.create(
                    user=publication.user,
                    objectif=subject,
                    detail=message
                )

                print("Notification interne créée")

                _message_apres_soumission(
                    request, publication, "article scientifique"
                )

                return redirect('publications:index')

            except Exception as e:

                print("ERREUR REELLE :", str(e))

                messages.error(request, f"Une erreur est survenue : {str(e)}")

    else:

        form_publication = PublicationForm()

        form_article = ArticleForm()

    # ==========================================
    # RENDER TEMPLATE
    # ==========================================
    return render(request,
        'back/modals_publications/article_scientifique.html',
        {
            "form_publication": form_publication,
            "form_article": form_article,
        }
    )

# Vue pour le modal communication de colloque
def modal_communication_colloque(request):

    # ==========================================
    # INITIALISATION FORMULAIRES
    # ==========================================
    form_publication = PublicationForm()

    form_colloque = ColloqueForm()

    # ==========================================
    # VERIFICATION PROFIL UTILISATEUR
    # ==========================================
    champs_obligatoires = [
        'role',
        'institution',
        'orcid',
        'fonction_poste'
    ]

    profile = getattr(request.user, 'profile', None)

    if not profile:

        messages.error(request, "Profil utilisateur introuvable.")

        return redirect('portail_site:dashboard')

    if not all(getattr(profile, champ, None) for champ in champs_obligatoires):

        messages.warning(request, "Veuillez compléter votre profil.")

        return render(request, 'back/auteurs/profil_auteur.html')

    # ==========================================
    # TRAITEMENT POST
    # ==========================================
    if request.method == "POST":

        form_publication = PublicationForm(
            request.POST,
            request.FILES
        )

        form_colloque = ColloqueForm(request.POST)

        publication_valid = form_publication.is_valid()

        colloque_valid = form_colloque.is_valid()

        print("Erreurs publication :", form_publication.errors)

        print("Erreurs colloque :", form_colloque.errors)

        if publication_valid and colloque_valid:

            try:

                # ==========================================
                # RECUPERATION PDF
                # ==========================================
                fichier = request.FILES.get('fichier_pdf')

                if not fichier:

                    messages.error(request, "Veuillez ajouter un fichier PDF.")

                    return redirect(request.path)

                # ==========================================
                # VERIFICATION TYPE PDF
                # ==========================================
                if fichier.content_type != 'application/pdf':

                    messages.error(request, "Le fichier doit être au format PDF.")

                    return redirect(request.path)

                # ==========================================
                # VERIFICATION TAILLE PDF
                # ==========================================
                if fichier.size > 20 * 1024 * 1024:

                    messages.error(request, "Le fichier dépasse 20 MB.")

                    return redirect(request.path)

                user = request.user

                # ==========================================
                # TRANSACTION PRINCIPALE
                # ==========================================
                with transaction.atomic():

                    # ==========================================
                    # CREATION PUBLICATION
                    # ==========================================
                    publication = form_publication.save(commit=False)

                    publication.user = (
                        user if user.is_authenticated else None
                    )

                    publication.save()

                    form_publication.save_m2m()

                    print("Publication créée avec succès")

                    # ==========================================
                    # CREATION COLLOQUE
                    # ==========================================
                    colloque = form_colloque.save(commit=False)

                    # IMPORTANT :
                    # héritage multi-table Django
                    colloque.pk = publication.pk

                    colloque.user = publication.user

                    colloque.save()

                    form_colloque.save_m2m()

                    print("Communication colloque créée")

                    # ==========================================
                    # AUTEUR PRINCIPAL
                    # ==========================================
                    PublicationAuteur.objects.get_or_create(
                        auteur=user,
                        publication=publication,
                        defaults={
                            'role': 'Auteur principal',
                            'ordre': 1
                        }
                    )

                    print("Auteur principal ajouté")

                    from publications.nlp_tools import (
                        extraire_texte_du_pdf,
                        enrichir_meta_depuis_doi,
                    )
                    doi = form_publication.cleaned_data.get("doi") or publication.doi
                    fichier.seek(0)
                    texte_pdf = extraire_texte_du_pdf(fichier) or ""
                    meta_doi = enrichir_meta_depuis_doi(doi) if doi else None

                    analyse_coauteurs = resoudre_auteurs_cites(
                        texte_pdf=texte_pdf,
                        meta_externes=meta_doi,
                        deposant=user,
                    )
                    enregistrer_coauteurs(
                        publication,
                        analyse_coauteurs,
                        request,
                        sujet_existant="Participation à une communication de colloque",
                    )

                    print("Co-auteurs traités")

                    motifs_prealables = []
                    if analyse_coauteurs.get("rejets"):
                        motifs_prealables.append(
                            MOTIFS_PREFIXE
                            + "\n"
                            + "\n".join(analyse_coauteurs["rejets"])
                        )

                    # ==========================================
                    # INDEXATION NLP COMPLETE
                    # ==========================================
                    fichier.seek(0)

                    publication.indexer(
                        fichier,
                        motifs_prealables=motifs_prealables,
                    )

                    publication.save()

                    print("Indexation NLP terminée")

                # ==========================================
                # FIN TRANSACTION
                # ==========================================

                # ==========================================
                # EMAIL NOTIFICATION
                # ==========================================
                publication.send_notification_email()

                print("Email notification envoyé")

                # ==========================================
                # NOTIFICATION INTERNE
                # ==========================================
                subject, message = (
                    publication.get_notification_content()
                )

                Notification.objects.create(
                    user=publication.user,
                    objectif=subject,
                    detail=message
                )

                print("Notification interne créée")

                _message_apres_soumission(
                    request, publication, "communication de colloque"
                )

                return redirect('publications:index')

            except Exception as e:

                print("ERREUR REELLE :", str(e))

                messages.error(
                    request,
                    f"Une erreur est survenue : {str(e)}"
                )

    else:

        form_publication = PublicationForm()

        form_colloque = ColloqueForm()

    # ==========================================
    # RENDER TEMPLATE
    # ==========================================
    return render(
        request,
        'back/modals_publications/colloque.html',
        {
            "form_publication": form_publication,
            "form_colloque": form_colloque,
        }
    )

def rechercher_publications(request):

    query = request.GET.get('q')

    publications = []

    if query:

        with connection.cursor() as cursor:

            cursor.execute("""

                SELECT id,

                MATCH(
                    titre,
                    resume,
                    mots_cles,
                    texte_nettoye
                )

                AGAINST(%s IN NATURAL LANGUAGE MODE)

                AS pertinence

                FROM publication

                WHERE MATCH(
                    titre,
                    resume,
                    mots_cles,
                    texte_nettoye
                )

                AGAINST(%s IN NATURAL LANGUAGE MODE)

                ORDER BY pertinence DESC

            """, [query, query])

            resultats = cursor.fetchall()

        ids = [row[0] for row in resultats]

        publications = Publication.objects.filter(
            id__in=ids
        )

    return render(

        request,

        'back/publications/recherche.html',

        {
            'publications': publications,
            'query': query
        }
    )



