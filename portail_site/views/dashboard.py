from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils import timezone
from publications.models import Publication, Auteur, Encadreur, Institution, PublicationLike, PublicationComment, PublicationDownload

# Fonction permettant de formater la durée en mois, jours, heures, minutes et secondes
def format_duration(seconds):
    if seconds is None:
        return None

    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    days = int(hours // 24)
    months = int(days // 30)

    if months >= 1:
        return f"il y a {months} mois"
    elif days >= 1:
        return f"il y a {days} jours"
    elif hours >= 1:
        return f"il y a {hours}h {minutes % 60}min"
    elif minutes >= 1:
        return f"il y a {minutes}min"
    else:
        return f"il y a {int(seconds)}s"

# La vue du tableau de bord backOffice
class DashboardTemplateView(TemplateView):
    template_name = 'back/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()

        def time_since(obj, attr):
            return (now - getattr(obj, attr)).total_seconds() if obj else None

        # ADMIN : Voir toutes les publications et stats globales
        if user.is_authenticated and getattr(user, "role", "") == "admin":
            context['publications'] = Publication.objects.order_by('-date_ajout_systeme')
            context['nb_publications'] = Publication.objects.count()
            context['nb_auteurs'] = Auteur.objects.count()
            context['nb_encadreurs'] = Encadreur.objects.count()
            context['nb_institutions'] = Institution.objects.count()

            # Derniers éléments
            context['time_since_last_publication'] = format_duration(time_since(
                Publication.objects.order_by('-date_ajout_systeme').first(), 'date_ajout_systeme'
            ))
            context['time_since_last_auteur'] = format_duration(time_since(
                Auteur.objects.order_by('-created_at').first(), 'created_at'
            ))
            context['time_since_last_encadreur'] = format_duration(time_since(
                Encadreur.objects.order_by('-created_at').first(), 'created_at'
            ))
            context['time_since_last_institution'] = format_duration(time_since(
                Institution.objects.order_by('-created_at').first(), 'created_at'
            ))

        # UTILISATEUR SIMPLE : Voir uniquement ses propres stats
        else:
            if not user.is_authenticated:
                return context

            context['publications'] = Publication.objects.filter(user=user).order_by('-date_ajout_systeme')
            context['nb_publications'] = context['publications'].count()
            context['nb_likes'] = PublicationLike.objects.filter(user=user).count()
            context['nb_commentaires'] = PublicationComment.objects.filter(user=user).count()
            context['nb_telechargements'] = PublicationDownload.objects.filter(user=user).count()

            context['time_since_last_publication'] = format_duration(time_since(
                context['publications'].first(), 'date_ajout_systeme'
            ))
            context['time_since_last_like'] = format_duration(time_since(
                PublicationLike.objects.filter(user=user).order_by('-liked_at').first(), 'liked_at'
            ))
            context['time_since_last_commentaire'] = format_duration(time_since(
                PublicationComment.objects.filter(user=user).order_by('-created_at').first(), 'created_at'
            ))
            context['time_since_last_telechargement'] = format_duration(time_since(
                PublicationDownload.objects.filter(user=user).order_by('-downloaded_at').first(), 'downloaded_at'
            ))

        return context