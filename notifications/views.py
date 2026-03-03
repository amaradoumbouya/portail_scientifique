from django.shortcuts import render
from django.views.generic import TemplateView


class NotificationTemplateView(TemplateView):
    template_name = 'back/notifications/index.html'

# Create your views here.
