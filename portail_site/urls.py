from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.decorators import login_required
from portail_site.views import *


app_name = 'portail_site'

urlpatterns = [
    path('', IndexTemplateView.as_view(), name='index'),
    path('dashboard/', login_required(DashboardTemplateView.as_view()), name='dashboard'),
    path('publication/', PublicationTemplateView.as_view(), name='publication'),
    path('publication-par-type/', views.publication_par_type_template_view, name='publication_par_type'),
    path('publication-par-type/<slug:slug>/', views.publication_par_type_template_view, name='publication_par_type_detail'),
    
    # Les URLs pour les publicationLike, publicationComment et publicationDownload
    path('like/<int:pk>/', views.like_publication, name='like_publication'),
    path('comment/<int:pk>/', views.comment_publication, name='comment_publication'),
    path('download/<int:pk>/', views.download_publication, name='download_publication'),
    # Les URLs pour les publicationLike, publicationComment et publicationDownload

    path('a-propos/', AproposTemplateView.as_view(), name='a_propos'),
    path('contact/', views.contact_us_template_view, name='contact'),
    path('inscription/', views.inscriptionTemplateView, name='inscription'),
    path('compte-institution/', views.inscription_compte_institution, name='inscription_institution'),
    path('compte-enseignant/', views.inscription_compte_enseignant, name='inscription_enseignant'),
    path('compte-etudiant/', views.inscription_compte_etudiant, name='inscription_etudiant'),
    path('activation/<uidb64>/<token>/', activate_account, name='activation'),
    path('mon-profil/', login_required(MonprofilTemplateView.as_view()), name='mon_profil'),
    path('mes-publications/',login_required(MespublicationsTemplateView.as_view()), name='mes_publications'),
    path('depot-publication/',login_required(views.depot_publication), name='depot_publication'),
    path('messages/',login_required(MessagesTemplateView.as_view()), name='messages'),
    path('notifications/',login_required(NotificationsTemplateView.as_view()), name='notifications'),
    path('detail-publication/<slug:slug>/', views.detail_publication_template, name='detail_publication'),
    path('recherche/', views.recherche_template_view, name='recherche'),
    path('detail-auteur/<slug:slug>/', views.detail_auteur_template_view, name='detail_auteur'),
    path('detail-encadreur/<slug:slug>/', views.detail_encadreur_template_view, name='detail_encadreur'),
    path('connexion/', views.user_login_view, name='connexion'),
    path('deconnexion/',auth_views.LogoutView.as_view(),name="deconnexion"),

    # URLs pour les modals avec slugs et pk optionnel
    path('modal/profil/<slug:slug>/', views.modal_profil, name='modal_profil'),
    path('modal/biographie/<slug:slug>/', views.modal_biographie, name='modal_biographie'),
    path('modal/details/<str:model_name>/<int:pk>/', views.modal_detail_activite, name='details_activite'),
    
    path('modal/emploi/<slug:slug>/', views.modal_emploi, name='modal_emploi'),
    path('modal/emploi/<slug:slug>/<int:pk>/', views.modal_emploi, name='modal_emploi_edit'),
    
    path('modal/education-qualification/<slug:slug>/', views.modal_education_qualification, name='modal_education_qualification'),
    path('modal/education-qualification/<slug:slug>/<int:pk>/', views.modal_education_qualification, name='modal_education_qualification_edit'),
    
    path('modal/experience-professionnelle/<slug:slug>/', views.modal_experience_professionnelle, name='modal_experience_professionnelle'),
    path('modal/experience-professionnelle/<slug:slug>/<int:pk>/', views.modal_experience_professionnelle, name='modal_experience_professionnelle_edit'),
    
    path('modal/travaux-recherche/<slug:slug>/', views.modal_travaux_recherche, name='modal_travaux_recherche'),
    path('modal/travaux-recherche/<slug:slug>/<int:pk>/', views.modal_travaux_recherche, name='modal_travaux_recherche_edit'),
    
    path('modal/reseaux-sociaux/<slug:slug>/', views.modal_reseaux_sociaux, name='modal_reseaux_sociaux'),

]
