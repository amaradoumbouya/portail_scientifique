from django.shortcuts import render
from django.views.generic import TemplateView


class IndexationTemplateView(TemplateView):
    template_name = 'back/indexations/index.html'

# Create your views here.
