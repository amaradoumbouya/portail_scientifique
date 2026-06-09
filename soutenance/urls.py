from django.urls import path
from soutenance.views.soutenance_view import *

app_name = 'soutenance'

urlpatterns = [


    path('soutenance/', modal_soutenance, name="modal_soutenance"),

    path('demande-soutenance/voir-plus/<slug:slug>/', modal_voir_plus_soutenance, name='modal_voir_plus_soutenance'),
    path('demande-soutenance/planifier-soutenance/<slug:slug>/', modal_planifier_soutenance, name='modal_planifier_soutenance'),
    path('demande-soutenance/ajout-membre-jury/<slug:slug>/', modal_ajouter_membres_jury, name='modal_ajouter_membres_jury'),
    path('demande-soutenance/liste-membres-jury/<slug:slug>/', modal_liste_membres_jury, name='modal_liste_membres_jury'),
    path('soutenance/liste-soutenances/', index_soutenance, name='index_soutenance'),
    path('soutenance/deliberation-soutenance/<slug:slug>/', ajouter_deliberation, name='ajouter_deliberation'),
    path('soutenance/voir-plus-deliberation-soutenance/<slug:slug>/', voir_plus_deliberation, name='voir_plus_deliberation'),

    # ==========================================
    # DEMANDE DE SOUTENANCE
    # ==========================================

    path('demande-soutenance/<slug:slug>/', modal_demande_soutenance, name='modal_demande_soutenance'),

    # ==========================================
    # MODIFICATION DEMANDE DE SOUTENANCE
    # ==========================================

    path('modification-demande-soutenance/<slug:slug>/', modal_modification_demande_soutenance, name='modal_modification_demande_soutenance'),  
]