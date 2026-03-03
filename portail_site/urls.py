from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.decorators import login_required
from portail_site.views import DashboardTemplateView, IndexTemplateView, PublicationTemplateView, AproposTemplateView, contact_us_template_view, detail_publication_template, detail_auteur_template_view, detail_encadreur_template_view, inscriptionTemplateView, user_login_view, depot_publication, MonprofilTemplateView, MespublicationsTemplateView, MessagesTemplateView, NotificationsTemplateView, activate_account, publication_par_type_template_view, like_publication, comment_publication, download_publication


app_name = 'portail_site'
urlpatterns = [
    path('', IndexTemplateView.as_view(), name='index'),
    path('dashboard/', login_required(DashboardTemplateView.as_view()), name='dashboard'),
    path('publication/', PublicationTemplateView.as_view(), name='publication'),
    path('publication-par-type/<slug:slug>', views.publication_par_type_template_view, name='publication_par_type'),
    
    # Les URLs pour les publicationLike, publicationComment et publicationDownload
    path('like/<int:pk>/', views.like_publication, name='like_publication'),
    path('comment/<int:pk>/', views.comment_publication, name='comment_publication'),
    path('download/<int:pk>/', views.download_publication, name='download_publication'),
    # Les URLs pour les publicationLike, publicationComment et publicationDownload

    path('a-propos/', AproposTemplateView.as_view(), name='a_propos'),
    path('contact/', views.contact_us_template_view, name='contact'),
    path('inscription/', views.inscriptionTemplateView, name='inscription'),
    path('activation/<uidb64>/<token>/', activate_account, name='activation'),
    path('mon-profil/', login_required(MonprofilTemplateView.as_view()), name='mon_profil'),
    path('mes-publications/',login_required(MespublicationsTemplateView.as_view()), name='mes_publications'),
    path('depot-publication/',login_required(views.depot_publication), name='depot_publication'),
    path('messages/',login_required(MessagesTemplateView.as_view()), name='messages'),
    path('notifications/',login_required(NotificationsTemplateView.as_view()), name='notifications'),
    path('detail-publication/<slug:slug>/', views.detail_publication_template, name='detail_publication'),
    path('detail-auteur/<slug:slug>/', views.detail_auteur_template_view, name='detail_auteur'),
    path('detail-encadreur/<slug:slug>/', views.detail_encadreur_template_view, name='detail_encadreur'),
    path('connexion/', views.user_login_view, name='connexion'),
    path('deconnexion/',auth_views.LogoutView.as_view(),name="deconnexion"),
    
]
