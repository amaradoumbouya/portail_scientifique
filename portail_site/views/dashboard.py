from datetime import timedelta
from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate
from publications.models.publication import Publication, Auteur, Encadreur, Institution, PublicationLike, PublicationComment, PublicationDownload


# Calcule le compte jour/semaine/mois + la série des 7 derniers jours (pour la sparkline)
def periode_stats(qs, champ_date, now):
    debut_jour = now - timedelta(days=1)
    debut_semaine = now - timedelta(days=7)
    debut_mois = now - timedelta(days=30)

    stats = {
        "jour": qs.filter(**{f"{champ_date}__gte": debut_jour}).count(),
        "semaine": qs.filter(**{f"{champ_date}__gte": debut_semaine}).count(),
        "mois": qs.filter(**{f"{champ_date}__gte": debut_mois}).count(),
    }

    comptage = (
        qs.filter(**{f"{champ_date}__gte": debut_semaine})
          .annotate(jour=TruncDate(champ_date))
          .values("jour")
          .annotate(total=Count("id"))
    )
    par_jour = {c["jour"]: c["total"] for c in comptage}
    stats["serie"] = [
        par_jour.get((now - timedelta(days=i)).date(), 0)
        for i in range(6, -1, -1)  # du plus ancien au plus récent
    ]
    return stats


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

            # Statistiques par période (jour / semaine / mois) + série sparkline
            context['stat_publications'] = periode_stats(
                Publication.objects.all(), 'date_ajout_systeme', now
            )
            context['stat_telechargements'] = periode_stats(
                PublicationDownload.objects.all(), 'downloaded_at', now
            )
            context['stat_likes'] = periode_stats(
                PublicationLike.objects.all(), 'liked_at', now
            )

        # UTILISATEUR SIMPLE : Voir uniquement ses propres stats
        else:
            if not user.is_authenticated:
                return context

            publications_auteur_principal = (
                Publication.objects
                .filter(
                    publicationauteur__auteur=user,
                    publicationauteur__role='Auteur principal',
                )
                .distinct()
                .order_by('-date_ajout_systeme')
            )

            publications_coauteur = (
                Publication.objects
                .filter(
                    publicationauteur__auteur=user,
                    publicationauteur__role='Co-auteur',
                )
                .distinct()
                .order_by('-date_ajout_systeme')
            )

            context['publications_auteur_principal'] = publications_auteur_principal
            context['publications_coauteur'] = publications_coauteur
            context['nb_publications_auteur_principal'] = publications_auteur_principal.count()
            context['nb_publications_coauteur'] = publications_coauteur.count()
            context['publications'] = (
                Publication.objects
                .filter(
                    publicationauteur__auteur=user,
                    publicationauteur__role__in=['Auteur principal', 'Co-auteur'],
                )
                .distinct()
                .order_by('-date_ajout_systeme')
            )
            context['nb_publications'] = context['publications'].count()
            context['nb_likes'] = PublicationLike.objects.filter(user=user).count()
            context['nb_commentaires'] = PublicationComment.objects.filter(user=user).count()
            context['nb_telechargements'] = PublicationDownload.objects.filter(user=user).count()

            context['time_since_last_publication_auteur'] = format_duration(time_since(
                publications_auteur_principal.first(), 'date_ajout_systeme'
            ))
            context['time_since_last_publication_coauteur'] = format_duration(time_since(
                publications_coauteur.first(), 'date_ajout_systeme'
            ))
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