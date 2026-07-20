from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.db.models import Q, Count
from types_document.models import TypeDocument
from publications.models.publication import Publication
from django.core.paginator import Paginator
from auteurs.models import Auteur
from encadreurs.models import Encadreur
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from publications.forms.publication_forms import PublicationForm
from projets_detudes.models.projet import ProjetEtude
from django.shortcuts import redirect

User = get_user_model()


# La vue de toutes les publications
class PublicationTemplateView(TemplateView):
    template_name = 'pages/publication.html'


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
            'projet',
            ProjetEtude.objects.filter(type_projet='memoire').order_by('-date_soumission'),
        )

    if any(mot in libelle for mot in ('thèse', 'these', 'doctorat')):
        return (
            'projet',
            ProjetEtude.objects.filter(type_projet='these').order_by('-date_soumission'),
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
    publication = get_object_or_404(Publication, slug=slug, statut_publication=True)
    publications_categorie = (
        Publication.objects.filter(domaine=publication.domaine, statut_publication=True)
        .exclude(id=publication.id)
        .order_by('-date_ajout_systeme')[:10]
    )
    comments = publication.comments.order_by('-id')[:5]
    return render(
        request,
        'pages/detail_publication.html',
        {
            'publication': publication,
            'publications_categorie': publications_categorie,
            'comments': comments,
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
    return ProjetEtude.objects.filter(
        Q(titre__icontains=query) | Q(description__icontains=query),
        type_projet__in=['these', 'memoire'],
    ).order_by('-date_soumission')


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

# Informations sur l'auteur
def detail_auteur_template_view(request, slug):
    auteur = get_object_or_404(Auteur, slug=slug)
    publications = Publication.objects.filter(auteurs__in=[auteur]).order_by('-id')[:10]
    return render(request, 'pages/detail_auteur.html', {'auteur': auteur, 'publications': publications,})

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
