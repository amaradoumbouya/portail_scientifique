from django.shortcuts import render
from django.core.paginator import Paginator
from publications.models import Publication
from types_document.models import TypeDocument


class PortailMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Initialisation (appelée une seule fois au démarrage)

    def __call__(self, request):
        # Code exécuté avant la vue (pré-traitement de la requête)

        # La liste de toutes les publicatons sur la page d'accueil
        publications = Publication.objects.filter(statut_indexation='Indexée', statut_publication='True').order_by('-id')[:6]

        ################# Toutes les publications #################
        toutes_les_publications = Publication.objects.all().order_by('id')
        # Paginer les publications
        paginator = Paginator(toutes_les_publications, 6)  # ou 10, selon votre choix
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        # Passer toutes les publications paginés à la requête
        request.page_obj = page_obj

        # Les types de document(ça va servir à dynamiser le menu)
        type_document = TypeDocument.objects.all()

        request.type_document = type_document


        # La liste de toutes les publicatons sur la page d'accueil
        request.publications = publications

        response = self.get_response(request)
        # Code exécuté après la vue (post-traitement de la réponse)
        #         
        return response