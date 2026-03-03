from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required
from publications.views import publication_et_indexation, statut_publication, PublicationUpdateView, PublicationDeleteView, detail_publication


app_name = 'publications'
urlpatterns = [
    path('index/', login_required(publication_et_indexation), name='index'),
    path('statut-publication/', login_required(statut_publication),name='statut_publication'),
    path('detail-publication/<str:slug>/', login_required(detail_publication), name='detail'),
    path('update-publication/<str:slug>/', login_required(PublicationUpdateView.as_view()), name='update'),
    path('delete-publication/<str:slug>/', login_required(PublicationDeleteView.as_view()), name='delete'),
]
