from django.urls import path
from indexations.views import IndexationTemplateView

app_name = 'indexations'
urlpatterns = [
    path('index/', IndexationTemplateView.as_view(), name='index')
]
