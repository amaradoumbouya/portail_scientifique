from django.urls import path
from projets_detudes.views.modal_views import *
# projet_etude_index,modal_memoire_de_master, modal_these_de_doctorat, liste_des_etudiants_a_encadrer


app_name = 'projets_detudes'

urlpatterns = [
    # URLs pour les modals de publication
    path('', projet_etude_index, name='index'),

    # URLs pour les modals de projet d'etude(memoire et thèse)
    path('memoire-master/', modal_memoire_de_master, name='modal_memoire'),
    path('these-doctorat/', modal_these_de_doctorat, name='modal_these'),

    # URLs pour les etapes de l'encadrement
    path('projet-detude-voir-plus/<slug:slug>/', modal_voir_plus, name='modal_voir_plus'),
    path('projet-detude-canevas/<slug:slug>/', modal_canevas, name='modal_canevas'),
    path('projet-detude-planing/<slug:slug>/', modal_planing, name='modal_planing'),
    path('projet-detude-tache/<slug:slug>/', modal_tache, name='modal_tache'),
    path('projet-detude-liste-des-taches/<slug:slug>/', liste_des_taches_template_view, name='liste_des_taches'),
    path('projet-detude-modification-tache/<slug:slug>/', modal_modification_tache, name='modal_update_tache'),
    path('projet-detude-progression/', progression_template_view, name='progression'),
    path('projet-detude-demande-soutenance/', modal_demande_soutenance, name='modal_demande_soutenance'),

    # Liste
    path('liste-planing/<slug:slug>/', liste_planing, name='liste_planing'),
    # Modification
    path('modification-planing/<slug:slug>/', modal_modification_planing, name='modal_modification_planing'),

    # URLs pour afficher la liste des etudiants liés à un encadrant
    path('liste-des-etudiants-à-encadrer/', liste_des_etudiants_a_encadrer, name='etudiants_a_encadrer'),
]
