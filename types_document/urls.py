from django.urls import path
from django.contrib.auth.decorators import login_required
from types_document.views import DocumentCreateView, DocumentUpdateView, DocumentDeleteView

app_name = 'types_document'
urlpatterns = [
    path('index/', login_required(DocumentCreateView.as_view()), name='index'),
    path('update-document/<str:slug>/', login_required(DocumentUpdateView.as_view()), name='update'),
    path('delelte-document/<str:slug>/', login_required(DocumentDeleteView.as_view()), name='delete'),
]
