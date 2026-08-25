from django.urls import path

from statistiques.views import statistiques_publiques

app_name = "statistiques"
urlpatterns = [
    path("", statistiques_publiques, name="index"),
]
