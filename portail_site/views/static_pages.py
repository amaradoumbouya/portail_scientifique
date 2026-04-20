from django.shortcuts import render
from django.views.generic import TemplateView
from contact_us.forms import ContactUsForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages

# La d'accueil
class IndexTemplateView(TemplateView):
    template_name = 'index.html'


# La vue Apropos
class AproposTemplateView(TemplateView):
    template_name = 'pages/a_propos.html'

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
def contact_us_template_view(request):
    if request.method == 'POST':
        form = ContactUsForm(request.POST)
        if form.is_valid():
            contact = form.save()
            email = contact.email

            # Envoi de l'email de réception
            subject = "Portail Scientifique: Votre message a bien été reçu"
            message = f"""
            Bonjour M/Mme {contact.nom_complet},
            Merci de nous avoir contactés. Nous avons bien reçu votre message et vous répondrons dans les plus brefs délais.

            Cordialement,
            L’équipe Techniqque du CRICT(Centre de Recherche en Informatique et Cyber-Technologie)
            """
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            messages.success(request, "Message reçu avec succès. Un mail de confirmation vous a été envoyé.")
            form = ContactUsForm()
        else:
            messages.error(request, "Une erreur est survenue. Veuillez vérifier les informations.")
    else:
        form = ContactUsForm()

    return render(request, "pages/contact.html", {"form": form})