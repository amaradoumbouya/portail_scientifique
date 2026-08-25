from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.urls import reverse
from contact_us.forms import ContactUsForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from publications.models.publication import Publication
from institutions.models import Institution
from projets_detudes.models.projet import ProjetEtude
from accounts.models import UserProfile
from evenements.models import Evenement
from actualites.models import Actualite
from types_document.models import TypeDocument
from datetime import datetime, date
from django.utils import timezone
from django.db.models import Count, Q


def _liste_chercheurs_top(limit=4):
    return list(
        UserProfile.objects
        .filter(
            role__in=['enseignant', 'enseignant chercheur'],
            user__is_active=True,
        )
        .select_related('user')
        .annotate(
            nb_publications=Count(
                'user__publicationauteur',
                filter=Q(user__publicationauteur__publication__statut_publication=True),
                distinct=True,
            )
        )
        .filter(nb_publications__gt=0)
        .order_by('-nb_publications', 'user__nom', 'user__prenoms')[:limit]
    )


# La d'accueil
class IndexTemplateView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        publications_publiees = list(
            Publication.objects.filter(statut_publication=True)
            .order_by('-date_ajout_systeme')
        )
        context['publications_recentes'] = publications_publiees[:4]
        context['autres_publications'] = publications_publiees[4:]
        context['nb_publications'] = len(publications_publiees)
        context['nb_theses_memoires'] = ProjetEtude.objects.count()
        context['nb_chercheurs'] = UserProfile.objects.filter(
            role__in=['enseignant', 'enseignant chercheur']
        ).count()
        context['nb_institutions'] = Institution.objects.count()

        today = date.today()
        deadline = date(today.year, 3, 30)
        if deadline < today:
            deadline = date(today.year + 1, 3, 30)
        context['date_limite_soumission'] = deadline
        context['date_limite_soumission_iso'] = datetime(
            deadline.year, deadline.month, deadline.day, 23, 59, 59
        ).isoformat()
        context['evenements'] = (
            Evenement.objects.filter(is_actif=True, date_evenement__gte=timezone.now())
            .order_by('date_evenement')[:6]
        )
        # Liste dédiée pour éviter tout conflit de nom avec l'app / namespace "actualites"
        context['liste_actualites'] = list(
            Actualite.objects.filter(is_actif=True)
            .order_by('-date_publication', '-created_at')[:3]
        )
        context['liste_chercheurs'] = _liste_chercheurs_top(4)
        return context


# La vue Apropos
class AproposTemplateView(TemplateView):
    template_name = 'pages/a_propos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['liste_chercheurs'] = _liste_chercheurs_top(4)
        return context

# La vue du profil_user
class MonprofilTemplateView(TemplateView):
    template_name = 'pages/mon_profil.html'

# La vue de toutes les publications_user
class MespublicationsTemplateView(TemplateView):
    template_name = 'pages/mes_publications.html'

# La vue des messages_user
class MessagesTemplateView(TemplateView):
    template_name = 'pages/messages.html'


# L vue des notifications_user
class NotificationsTemplateView(TemplateView):
    template_name = 'pages/notifications.html'

# La vue de contact
# def contact_us_template_view(request):
#     if request.method == 'POST':
#         form = ContactUsForm(request.POST)
#         if form.is_valid():
#             contact = form.save()
#             email = contact.email

#             # Envoi de l'email de réception
#             subject = "Sira: Votre message a bien été reçu"
#             message = f"""
#             Bonjour M/Mme {contact.nom_complet},
#             Merci de nous avoir contactés. Nous avons bien reçu votre message et vous répondrons dans les plus brefs délais.

#             Cordialement,
#             L’équipe Techniqque du CRICT(Centre de Recherche en Informatique et Cyber-Technologie)
#             """
#             send_mail(
#                 subject,
#                 message,
#                 settings.DEFAULT_FROM_EMAIL,
#                 [email],
#                 fail_silently=False,
#             )

#             messages.success(request, "Message reçu avec succès. Un mail de confirmation vous a été envoyé.")
#             form = ContactUsForm()
#         else:
#             messages.error(request, "Une erreur est survenue. Veuillez vérifier les informations.")
#     else:
#         form = ContactUsForm()

#     return render(request, "pages/contact.html", {"form": form})


# La vue de contact
def contact_us_template_view(request):

    if request.method == 'POST':

        form = ContactUsForm(request.POST)

        if form.is_valid():

            contact = form.save()

            email = contact.email

            subject = "Sira : Votre message a bien été reçu"

            message = f"""

            Bonjour M/Mme {contact.nom_complet},

            Merci de nous avoir contactés.

            Nous avons bien reçu votre message et nous vous répondrons dans les plus brefs délais.

            Cordialement,

            L'équipe Technique du CRICT

            (Centre de Recherche en Informatique et Cyber-Technologie)

            """

            if email:

                try:

                    send_mail(

                        subject=subject,

                        message=message,

                        from_email=settings.DEFAULT_FROM_EMAIL,

                        recipient_list=[email],
                        
                        fail_silently=False,
                    )

                    messages.success(request, "Message reçu avec succès. Un mail de confirmation vous a été envoyé.")

                except Exception:

                    messages.warning(request,"Votre message a été enregistré mais le mail de confirmation n'a pas pu être envoyé.")

            else:

                messages.success(request, "Message reçu avec succès. Merci de nous avoir contactés.")

            form = ContactUsForm()

        else:

            messages.error(request, "Une erreur est survenue. Veuillez vérifier les informations.")

    else:

        form = ContactUsForm()

    return render(request, "pages/contact.html", {"form": form})


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse('portail_site:sitemap'))
    body = "\n".join([
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /dashboard/",
        "Disallow: /accounts/",
        "Disallow: /modal/",
        "",
        f"Sitemap: {sitemap_url}",
        "",
    ])
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    abs_url = request.build_absolute_uri
    urls = [
        {"loc": abs_url(reverse("portail_site:index")), "changefreq": "daily", "priority": "1.0"},
        {"loc": abs_url(reverse("portail_site:publication")), "changefreq": "daily", "priority": "0.9"},
        {"loc": abs_url(reverse("portail_site:publication_par_type")), "changefreq": "weekly", "priority": "0.8"},
        {"loc": abs_url(reverse("portail_site:a_propos")), "changefreq": "monthly", "priority": "0.4"},
        {"loc": abs_url(reverse("portail_site:contact")), "changefreq": "monthly", "priority": "0.3"},
        {"loc": abs_url(reverse("portail_site:recherche")), "changefreq": "weekly", "priority": "0.5"},
        {"loc": abs_url(reverse("statistiques:index")), "changefreq": "daily", "priority": "0.7"},
        {"loc": abs_url(reverse("portail_site:catalogue_dc_xml")), "changefreq": "daily", "priority": "0.4"},
    ]
    for type_doc in TypeDocument.objects.order_by("libelle"):
        urls.append({
            "loc": abs_url(reverse("portail_site:publication_par_type_detail", kwargs={"slug": type_doc.slug})),
            "changefreq": "weekly",
            "priority": "0.7",
        })
    for pub in Publication.objects.filter(statut_publication=True).only("slug", "updated_at"):
        urls.append({
            "loc": abs_url(pub.get_absolute_url()),
            "lastmod": pub.updated_at.date().isoformat() if pub.updated_at else "",
            "changefreq": "monthly",
            "priority": "0.8",
        })
    return render(
        request,
        "sitemap.xml",
        {"urls": urls},
        content_type="application/xml; charset=utf-8",
    )