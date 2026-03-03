from django.urls import path
from django.contrib.auth.decorators import login_required
from contact_us.views import ContactUsCreateView, repondre_au_message_contact, reponse_au_message_contact, detail_message, ContactUsDeleteView


app_name = 'contact_us'
urlpatterns = [
    path('index/', login_required(ContactUsCreateView.as_view()), name='index' ),
    path('repondre-au-message/<str:slug>/', login_required(repondre_au_message_contact), name='repondre_au_message'),
    path('reponse-au-message/', login_required(reponse_au_message_contact), name='reponse_au_message_contact'),
    path('detail-au-message/<str:slug>/', login_required(detail_message), name='detail'),
    path('delete-message/<str:slug>/', login_required(ContactUsDeleteView.as_view()), name='delete'),
    
]
