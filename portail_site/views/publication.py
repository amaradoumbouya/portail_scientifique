from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from types_document.models import TypeDocument
from publications.models import Publication
from django.core.paginator import Paginator
from auteurs.models import Auteur
from encadreurs.models import Encadreur
from django.contrib.auth.decorators import login_required
from publications.forms import PublicationForm
from django.shortcuts import redirect



# La vue de toutes les publications
class PublicationTemplateView(TemplateView):
    template_name = 'pages/publication.html'

# La vue publication par type
def publication_par_type_template_view(request, slug):
    type_document = get_object_or_404(TypeDocument, slug=slug)
    publications = Publication.objects.filter(type_document=type_document, statut_publication=True).order_by('-id')
    paginator = Paginator(publications, 6)  # ou 10, selon votre choix
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "pages/publication_par_type.html", {'page_obj':page_obj, 'type_document':type_document})




# Detail_d'une_publication
def detail_publication_template(request, slug):
    publication = get_object_or_404(Publication, slug=slug)
    publications_categorie = Publication.objects.filter(domaine=publication.domaine).exclude(id=publication.id).order_by('-id')[:10]
    comments = publication.comments.order_by('-id')[:5]
    return render(request, 'pages/detail_publication.html', {'publication': publication, 'publications_categorie': publications_categorie, 'comments': comments,
    })


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