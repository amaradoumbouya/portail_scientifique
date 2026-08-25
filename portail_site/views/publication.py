from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
from types_document.models import TypeDocument
from publications.models.publication import Publication
from django.core.paginator import Paginator
from encadreurs.models import Encadreur
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from publications.forms.publication_forms import PublicationForm
from django.shortcuts import redirect
from publications.metadata import json_ld, json_ld_script, metadonnees_publication

User = get_user_model()


def _publications_publiees():
    return (
        Publication.objects.filter(statut_publication=True)
        .prefetch_related('publicationauteur_set__auteur')
        .order_by('-date_ajout_systeme')
    )


def catalogue_publications(request):
    """Catalogue public de toutes les publications indexées / publiées."""
    qs = _publications_publiees()
    type_filtre = (request.GET.get('type') or '').strip()
    if type_filtre in ('article', 'colloque', 'memoire', 'these'):
        qs = qs.filter(type_publication=type_filtre)

    paginator = Paginator(qs, 9)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(
        request,
        'pages/publication.html',
        {
            'page_obj': page_obj,
            'type_filtre': type_filtre,
            'total': qs.count(),
        },
    )


def _resolver_contenu_par_type(type_document):
    """Associe un TypeDocument aux publications ou projets correspondants."""
    libelle = (type_document.libelle or '').lower()

    if any(mot in libelle for mot in ('article',)):
        return (
            'publication',
            Publication.objects.filter(
                type_publication='article',
                statut_publication=True,
            ).order_by('-date_ajout_systeme'),
        )

    if any(mot in libelle for mot in ('colloque', 'communication')):
        return (
            'publication',
            Publication.objects.filter(
                type_publication='colloque',
                statut_publication=True,
            ).order_by('-date_ajout_systeme'),
        )

    if any(mot in libelle for mot in ('mémoire', 'memoire', 'master')):
        return (
            'publication',
            Publication.objects.filter(
                type_publication='memoire',
                statut_publication=True,
            ).order_by('-date_ajout_systeme'),
        )

    if any(mot in libelle for mot in ('thèse', 'these', 'doctorat')):
        return (
            'publication',
            Publication.objects.filter(
                type_publication='these',
                statut_publication=True,
            ).order_by('-date_ajout_systeme'),
        )

    return ('publication', Publication.objects.none())


def publication_par_type_template_view(request, slug=None):
    if not slug:
        types = TypeDocument.objects.order_by('libelle')
        return render(
            request,
            'pages/publication_par_type.html',
            {
                'type_document': None,
                'types_document': types,
                'page_obj': None,
                'kind': 'types',
            },
        )

    type_document = get_object_or_404(TypeDocument, slug=slug)
    kind, queryset = _resolver_contenu_par_type(type_document)
    paginator = Paginator(queryset, 6)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(
        request,
        'pages/publication_par_type.html',
        {
            'type_document': type_document,
            'page_obj': page_obj,
            'kind': kind,
        },
    )


# Detail_d'une_publication
def detail_publication_template(request, slug):
    publication = get_object_or_404(
        Publication.objects.select_related('indexation').prefetch_related(
            'publicationauteur_set__auteur__profile'
        ),
        slug=slug,
        statut_publication=True,
    )
    publications_categorie = (
        Publication.objects.filter(domaine=publication.domaine, statut_publication=True)
        .exclude(id=publication.id)
        .order_by('-date_ajout_systeme')[:10]
    )
    comments = publication.comments.order_by('-id')[:5]
    pdf_url = (
        request.build_absolute_uri(publication.fichier_pdf.url)
        if publication.fichier_pdf
        else ''
    )
    photo_url = (
        request.build_absolute_uri(publication.photo.url)
        if publication.photo
        else ''
    )
    meta = metadonnees_publication(publication, request)
    return render(
        request,
        'pages/detail_publication.html',
        {
            'publication': publication,
            'publication_reelle': publication.get_real_instance(),
            'publications_categorie': publications_categorie,
            'comments': comments,
            'citation_pdf_url': pdf_url,
            'citation_image_url': photo_url,
            'meta': meta,
            'json_ld_payload': json_ld_script(json_ld(meta)),
        },
    )


def _filtre_publications(query, type_filtre=None):
    qs = Publication.objects.filter(statut_publication=True)
    if type_filtre == 'articles':
        qs = qs.filter(type_publication='article')
    return qs.filter(
        Q(titre__icontains=query)
        | Q(resume__icontains=query)
        | Q(mots_cles__icontains=query)
        | Q(domaine__icontains=query)
    ).distinct().order_by('-date_ajout_systeme')


def _filtre_auteurs(query):
    qs = User.objects.filter(
        Q(profile__role__in=['enseignant', 'enseignant chercheur'])
        | Q(publicationauteur__isnull=False)
    )

    for token in query.split():
        qs = qs.filter(
            Q(prenoms__icontains=token)
            | Q(nom__icontains=token)
            | Q(email__icontains=token)
        )

    return (
        qs.select_related('profile')
        .annotate(nb_publications=Count('publicationauteur', distinct=True))
        .distinct()
        .order_by('nom', 'prenoms')
    )


def _filtre_theses(query):
    return Publication.objects.filter(
        statut_publication=True,
        type_publication__in=['these', 'memoire'],
    ).filter(
        Q(titre__icontains=query)
        | Q(resume__icontains=query)
        | Q(mots_cles__icontains=query)
        | Q(domaine__icontains=query)
    ).order_by('-date_ajout_systeme')


def recherche_template_view(request):
    query = (request.GET.get('q') or '').strip()
    type_filtre = (request.GET.get('type') or 'tout').strip().lower()

    publications = []
    auteurs = []
    theses = []

    if query:
        if type_filtre in ('tout', 'articles'):
            publications = _filtre_publications(
                query,
                type_filtre='articles' if type_filtre == 'articles' else None,
            )
        if type_filtre in ('tout', 'auteurs'):
            auteurs = _filtre_auteurs(query)
        if type_filtre in ('tout', 'theses'):
            theses = _filtre_theses(query)

    return render(
        request,
        'pages/recherche.html',
        {
            'query': query,
            'type_filtre': type_filtre,
            'publications': publications,
            'auteurs': auteurs,
            'theses': theses,
            'total_resultats': len(publications) + len(auteurs) + len(theses),
        },
    )

# Informations sur l'auteur / chercheur (utilisateur du portail)
def detail_auteur_template_view(request, slug):
    auteur = get_object_or_404(
        User.objects.select_related('profile', 'profile__institution', 'biographie'),
        slug=slug,
    )
    publications = list(
        Publication.objects.filter(
            publicationauteur__auteur=auteur,
            statut_publication=True,
        )
        .distinct()
        .order_by('-date_ajout_systeme')
    )
    biographie = ''
    if hasattr(auteur, 'biographie') and auteur.biographie:
        biographie = auteur.biographie.biographie or ''

    from projets_detudes.models.participant import Participant

    projets_encadres = Participant.objects.filter(
        user=auteur,
        role__in=[Participant.Role.DIRECTEUR, Participant.Role.CO_DIRECTEUR],
    ).select_related('projet').distinct()

    nb_publications = len(publications)
    nb_articles = sum(1 for p in publications if p.type_publication == 'article')
    nb_colloques = sum(1 for p in publications if p.type_publication == 'colloque')
    nb_etudiants = projets_encadres.values('projet_id').distinct().count()

    emplois = list(auteur.emploi.all().order_by('-date_debut_emploi'))
    formations = list(auteur.etude_academique.all().order_by('-date_debut_etude'))
    experiences = list(auteur.experience_professionnelle.all().order_by('-date_debut_experience'))
    travaux = list(auteur.travaux_recherche.all().order_by('-date_de_debut_travaux'))

    return render(
        request,
        'pages/detail_auteur.html',
        {
            'auteur': auteur,
            'publications': publications,
            'biographie': biographie,
            'stats': {
                'nb_publications': nb_publications,
                'nb_articles': nb_articles,
                'nb_colloques': nb_colloques,
                'nb_etudiants': nb_etudiants,
            },
            'emplois': emplois,
            'formations': formations,
            'experiences': experiences,
            'travaux': travaux,
        },
    )

# Informations sur l'encadreur
def detail_encadreur_template_view(request, slug):
    encadreur = get_object_or_404(Encadreur, slug=slug)
    publications = Publication.objects.filter(encadreurs__in=[encadreur]).order_by('-id')[:10]
    return render(request, 'pages/detail_encadreur.html', {'encadreur': encadreur, 'publications': publications,})

# La vue de publication_user
@login_required
def depot_publication(request):

    if not request.user.role:

        return render(request, 'pages/profil_auteur.html')

    if request.method == 'POST':

        form = PublicationForm(request.POST, request.FILES)

        if form.is_valid():

            publication = form.save()

            form.save_m2m()  # sauvegarde les auteurs

            return redirect('dashboard')
    else:

        form = PublicationForm()

    return render(request, 'pages/depot_publication.html', {'form': form})
