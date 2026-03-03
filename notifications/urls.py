from django.urls import path
from notifications.views import NotificationTemplateView

app_name = 'notifications'
urlpatterns = [
    path('index/', NotificationTemplateView.as_view(), name='index')
]
