from django.urls import path
from django.contrib.auth.decorators import login_required
from accounts.views import (
    AccountCreateView,
    Update_state,
    CustumUserUpdateView,
    CustumUserDeleteView,
    profil_user_template_view,
    changer_mot_de_passe,
    verrouiller,
    deverrouiller,
    session_keepalive,
)

app_name = "accounts"
urlpatterns = [
    path('index/', login_required(AccountCreateView.as_view()), name='index'),
    path('update-state/', login_required(Update_state), name='update_state'),
    path('profil-user/', profil_user_template_view, name='profil_user'),
    path('changer-mot-de-passe/', login_required(changer_mot_de_passe), name='changer_mot_de_passe'),
    path('verrouiller/', login_required(verrouiller), name='verrouiller'),
    path('deverrouiller/', login_required(deverrouiller), name='deverrouiller'),
    path('session-keepalive/', login_required(session_keepalive), name='session_keepalive'),
    path('update-custumer/<str:slug>/', login_required(CustumUserUpdateView.as_view()), name='update'),
    path('delete-custumer/<str:slug>/', login_required(CustumUserDeleteView.as_view()), name='delete'),
]
