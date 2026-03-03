from django.urls import path
from django.contrib.auth.decorators import login_required
from auteurs.views import AuteurCreateView, AuteurUpdateView, AuteurDeleteView, profil_auteur_template_view

app_name = 'auteurs'
urlpatterns = [
    path('index/', login_required(AuteurCreateView.as_view()), name='index' ),
    path('profil-auteur/', login_required(profil_auteur_template_view), name='profil_auteur' ),
    path('update-auteur/<str:slug>/', login_required(AuteurUpdateView.as_view()), name='update'),
    path('delete-auteur/<str:slug>/', login_required(AuteurDeleteView.as_view()), name='delete'),
    
]
