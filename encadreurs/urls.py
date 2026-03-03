from django.urls import path
from django.contrib.auth.decorators import login_required
from encadreurs.views import EncadreurCreateView, EncadreurUpdateView, EncadreurDeleteView

app_name = 'encadreurs'
urlpatterns = [
    path('index/', login_required(EncadreurCreateView.as_view()), name='index' ),
    path('update-encadreur/<str:slug>/', login_required(EncadreurUpdateView.as_view()), name='update'),
    path('delete-encadreur/<str:slug>/', login_required(EncadreurDeleteView.as_view()), name='delete'),
    
]
