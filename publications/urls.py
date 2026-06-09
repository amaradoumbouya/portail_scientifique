from django.urls import path
# from . import views
from django.contrib.auth.decorators import login_required
from publications.views.publication_views import *
# from publications.views.publication_views import publication_et_indexation, statut_publication, PublicationUpdateView, PublicationDeleteView, detail_publication, modal_memoire_de_master, modal_these_de_doctorat, modal_article_scientifique, modal_communication_colloque


app_name = 'publications'
urlpatterns = [
    path('index/', login_required(user_publications), name='index'),
    path('statut-publication/', login_required(statut_publication),name='statut_publication'),
    path('detail-publication/<str:slug>/', login_required(detail_publication), name='detail'),
    path('update-publication/<str:slug>/', login_required(PublicationUpdateView.as_view()), name='update'),
    path('delete-publication/<str:slug>/', login_required(PublicationDeleteView.as_view()), name='delete'),

    # URLs pour les modals de publication
    path('article-scientifique/', modal_article_scientifique, name='modal_article_scientifique'),
    path('communication-de-colloque/', modal_communication_colloque, name='modal_communication_colloque'),

    # URL pour la recherche de publications
    path('recherche/', rechercher_publications,name='recherche_publications'),
]
