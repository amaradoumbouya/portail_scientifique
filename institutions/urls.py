from django.urls import path
from django.contrib.auth.decorators import login_required
from institutions.views import InstitutionCreateView, InstitutionUpdateView, InstitutionDeleteView, institut_dashboard, ChercheurDeleteView, ChercheurDetailView, liste_etudiants

app_name = 'institutions'
urlpatterns = [
    path('index/', login_required(InstitutionCreateView.as_view()), name='index'),
    path('update-institution/<str:slug>/', login_required(InstitutionUpdateView.as_view()), name='update'),
    path('delete-institution/<str:slug>/', login_required(InstitutionDeleteView.as_view()), name='delete'),
    path('institution-dashboard/', login_required(institut_dashboard), name='institution_dashboard'),
    path('delete-chercheur/<str:slug>/', login_required(ChercheurDeleteView.as_view()), name='delete_chercheur'),
    path('detail-chercheur/<str:slug>/', login_required(ChercheurDetailView.as_view()), name='detail_chercheur'),
    path('liste-etudiants/', login_required(liste_etudiants), name='liste_etudiants'),
    path('liste-etudiants/<str:niveau>/', login_required(liste_etudiants), name='liste_etudiants_niveau'),
]
