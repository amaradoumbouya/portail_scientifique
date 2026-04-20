from django.urls import path
from django.contrib.auth.decorators import login_required
from accounts.views import AccountCreateView, Update_state, CustumUserUpdateView, CustumUserDeleteView, profil_user_template_view

app_name = "accounts"
urlpatterns = [
    path('index/', login_required(AccountCreateView.as_view()), name='index'),
    path('update-state/', login_required(Update_state), name='update_state'),
    path('profil-user/', profil_user_template_view, name='profil_user'),
    path('update-custumer/<str:slug>/', login_required(CustumUserUpdateView.as_view()), name='update'),
    path('delete-custumer/<str:slug>/', login_required(CustumUserDeleteView.as_view()), name='delete'),
    
]
