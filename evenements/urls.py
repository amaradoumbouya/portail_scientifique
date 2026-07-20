from django.urls import path
from django.contrib.auth.decorators import login_required
from evenements.views import (
    evenements_index,
    inscriptions_index,
    modal_evenement,
    update_evenement_state,
    delete_evenement,
    detail_evenement,
    detail_evenement_back,
    inscription_evenement,
)

app_name = 'evenements'

urlpatterns = [
    path('index/', login_required(evenements_index), name='index'),
    path('inscriptions/', login_required(inscriptions_index), name='inscriptions'),
    path('inscriptions/<slug:slug>/', login_required(inscriptions_index), name='inscriptions_evenement'),
    path('modal/', login_required(modal_evenement), name='modal_evenement'),
    path('modal/<slug:slug>/', login_required(modal_evenement), name='modal_evenement_edit'),
    path('statut/', login_required(update_evenement_state), name='update_state'),
    path('supprimer/<slug:slug>/', login_required(delete_evenement), name='delete'),
    path('gestion/detail/<slug:slug>/', login_required(detail_evenement_back), name='detail_back'),
    path('detail/<slug:slug>/', detail_evenement, name='detail'),
    path('inscription/<slug:slug>/', inscription_evenement, name='inscription'),
]
