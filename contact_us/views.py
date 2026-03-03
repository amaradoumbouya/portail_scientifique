from django.shortcuts import render, redirect, get_object_or_404
from contact_us.models import ContactUs
from contact_us.forms import ContactUsForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import linebreaks

from django.views.generic import TemplateView, CreateView, ListView, UpdateView, DeleteView


# La vue d'ajout de message
class ContactUsCreateView(CreateView):
    model = ContactUs
    form_class = ContactUsForm
    template_name = 'back/contact_us/index.html'
    success_url = reverse_lazy("contact_us:index")

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
            self.object = form.save()
            messages.success(self.request, "Message envoyé avec succès !")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_message"] = ContactUs.objects.order_by('-id')
        return context



# La vue repondre au message
def repondre_au_message_contact(request, slug):
    contact_message = get_object_or_404(ContactUs, slug=slug)
    return render(request, "back/contact_us/reponse.html", {'contact_message':contact_message})


# La vue reponse au message contact
def reponse_au_message_contact(request):
    if request.method == 'POST':
        message_id = request.POST.get('message_id')
        reponse = request.POST.get('reponse_au_message', '').strip()

        if not message_id or not reponse:
            messages.error(request, "ID du message ou réponse manquant.")
            return redirect('contact_us:index')

        contact_message = get_object_or_404(ContactUs, id=message_id)
        contact_message.reponse_au_message = reponse
        contact_message.is_read = True
        contact_message.save()
        slug_message = contact_message.slug

        # Envoi de l'email de réponse
        subject = f"Portail Scientifique: Reponse à votre demande {contact_message.objectif} "
        message_text = reponse
        message_html = f"""
        <p>{linebreaks(reponse)}</p>
        <p>Cordialement,<br>L’équipe Techniqque du CRICT(Centre de Recherche en Informatique et Cyber-Technologie)</p>
        """
        send_mail(
            subject,
            message_text,
            settings.DEFAULT_FROM_EMAIL,
            [contact_message.email],
            html_message=message_html,
            fail_silently=False,
        )

        messages.success(request, "Message répondu avec succès !")
        return redirect('contact_us:detail', slug=slug_message)

    return redirect('contact_us:index')



# Detail_message
def detail_message(request, slug):
    message = get_object_or_404(ContactUs, slug=slug)
    return render(request, 'back/contact_us/detail.html', {'message': message})



# La vue suppression de message
class ContactUsDeleteView(DeleteView):
    model         = ContactUs
    template_name = "back/contact_us/index.html"
    success_url   = reverse_lazy("contact_us:index")