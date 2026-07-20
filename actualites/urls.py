from django.urls import path
from django.contrib.auth.decorators import login_required
from actualites.views import (
    actualites_index,
    modal_actualite,
    update_actualite_state,
    delete_actualite,
    detail_actualite_back,
    detail_actualite,
)

app_name = 'actualites'

urlpatterns = [
    path('index/', login_required(actualites_index), name='index'),
    path('modal/', login_required(modal_actualite), name='modal_actualite'),
    path('modal/<slug:slug>/', login_required(modal_actualite), name='modal_actualite_edit'),
    path('statut/', login_required(update_actualite_state), name='update_state'),
    path('supprimer/<slug:slug>/', login_required(delete_actualite), name='delete'),
    path('gestion/detail/<slug:slug>/', login_required(detail_actualite_back), name='detail_back'),
    path('detail/<slug:slug>/', detail_actualite, name='detail'),
]
