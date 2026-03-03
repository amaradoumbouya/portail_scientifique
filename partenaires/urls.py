from django.urls import path
from django.contrib.auth.decorators import login_required
from partenaires.views import PartenaireCreateView, PartenairerUpdateView, PartenaireDeleteView, update_partenaire_state

app_name = 'partenaires'
urlpatterns = [
    path('index/', login_required(PartenaireCreateView.as_view()), name='index'),
    path('update-partenaire-state/', login_required(update_partenaire_state), name='update_state'),
    path('partenaire-update/<str:slug>/', login_required(PartenairerUpdateView.as_view()), name='update'),
    path('partenaire-delete/<str:slug>/', login_required(PartenaireDeleteView.as_view()), name='delete'),

    
]
