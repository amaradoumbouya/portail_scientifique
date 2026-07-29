from django.views.generic import TemplateView
from django.utils import timezone
from django.db.models import Count
from publications.models.publication import (
    Publication,
    PublicationLike,
    PublicationComment,
    PublicationDownload,
)
from accounts.models import UserProfile
from institutions.views import _etudiants_queryset, _filter_etudiants_par_niveau


def count_publications_indexees(qs=None):
    """
    Articles scientifiques publiés et indexés à l'international
    (statut_indexation = Acceptée → reconnu Scopus/WoS/DOAJ/AJOL).
    """
    qs = qs if qs is not None else Publication.objects.all()
    return qs.filter(
        type_publication="article",
        statut_publication=True,
        statut_indexation="Acceptée",
    ).count()


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

        # SUPERUSER : stats globales plateforme
        if user.is_authenticated and user.is_superuser:
            context['publications'] = Publication.objects.order_by('-date_ajout_systeme')

            # Personnel (enseignants / enseignants-chercheurs)
            personnel = (
                UserProfile.objects
                .filter(role__in=['enseignant', 'enseignant chercheur'])
                .annotate(nbre_publications=Count('user__publications', distinct=True))
            )
            context['total_enseignants'] = personnel.filter(role='enseignant').count()
            context['total_chercheurs'] = personnel.filter(role='enseignant chercheur').count()
            context['enseignants_actifs'] = personnel.filter(nbre_publications__gt=0).count()
            context['enseignants_inactifs'] = personnel.count() - context['enseignants_actifs']

            # Étudiants Master / Doctorat (toute la plateforme)
            etudiants_qs = _etudiants_queryset(is_superuser=True)
            context['total_master'] = _filter_etudiants_par_niveau(etudiants_qs, "master").count()
            context['total_doctorat'] = _filter_etudiants_par_niveau(etudiants_qs, "doctorat").count()

            # Production scientifique
            publications_qs = Publication.objects.all()
            context['total_articles'] = publications_qs.filter(type_publication='article').count()
            context['total_communications'] = publications_qs.filter(type_publication='colloque').count()
            context['total_production_scientifique'] = (
                context['total_articles'] + context['total_communications']
            )
            context['total_publications_indexees'] = count_publications_indexees(publications_qs)

            # Données pour les diagrammes (liées aux cartes)
            context['chart_dashboard'] = {
                "personnel": {
                    "labels": [
                        "Enseignants",
                        "Enseignants chercheurs",
                        "Étudiants Master",
                        "Étudiants Doctorat",
                    ],
                    "values": [
                        context['total_enseignants'],
                        context['total_chercheurs'],
                        context['total_master'],
                        context['total_doctorat'],
                    ],
                },
                "activite": {
                    "labels": ["Chercheurs actifs", "Chercheurs inactifs"],
                    "values": [
                        context['enseignants_actifs'],
                        context['enseignants_inactifs'],
                    ],
                },
                "production": {
                    "labels": [
                        "Articles",
                        "Colloques",
                        "Production",
                        "Indexées",
                    ],
                    "values": [
                        context['total_articles'],
                        context['total_communications'],
                        context['total_production_scientifique'],
                        context['total_publications_indexees'],
                    ],
                },
            }

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
