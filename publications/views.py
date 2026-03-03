from django.shortcuts import render, redirect, get_object_or_404
from publications.models import Publication
from publications.forms import PublicationForm
from notifications.models import Notification
from auteurs.forms import AuteurForm
from accounts.models import CustumerUser
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from publications.nlp_tools import extraire_texte_du_pdf, extraire_resume_et_mots_cles, classifier_domaine



# Ajout_et_indexation_d'une_publication
def publication_et_indexation(request):

    if not getattr(request.user, "role", None):
        form = AuteurForm()
        return render(request, 'back/auteurs/profil_auteur.html', {'form': form})

    if request.method == 'POST':
        form = PublicationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            publication = form.save(commit=False)
            fichier = request.FILES['fichier_pdf']
            publication.user = request.user if request.user.is_authenticated else None

            # Étape 1 : sauvegarde initiale
            publication.save()

            # Étape 2 : ManyToMany
            form.save_m2m()

            # Étape 3 : Indexation
            fichier.seek(0)
            publication.indexer(fichier)
            publication.save()

            # Envoi de l'email
            publication.send_notification_email()

            # Notification interne
            subject, message = publication.get_notification_content()
            Notification.objects.create(
                user=publication.user,
                objectif=subject,
                detail=message
            )
            messages.success(request, "Votre publication a été soumise avec succès. Vous recevrez une notification dès qu'elle sera traitée.")
            return redirect('publications:detail', slug=publication.slug)
    else:
        form = PublicationForm(user=request.user)

    user = request.user
    if getattr(user, "role", None) == "admin":
        publications = Publication.objects.order_by("-id")
    else:
        publications = Publication.objects.filter(user=user).order_by('-id')

    return render(request, 'back/publications/index.html', {'form': form, 'publications': publications})



# Statut publication, pour savoir si la publication est faite oui ou non
def statut_publication(request): 
    if request.method == 'POST':
        idpublier = request.POST.get('idpublier')
        pub = get_object_or_404(Publication, id=idpublier)
        pub.statut_publication = not pub.statut_publication  
        pub.save()

    # Redirection selon le rôle de l'utilisateur
    user = request.user
    if hasattr(user, 'role') and user.role == 'admin':
        return redirect('publications:index')
    else:
        return redirect('portail_site:dashboard')


# Detail_d'une_publication
def detail_publication(request, slug):
    publication = get_object_or_404(Publication, slug=slug)
    return render(request, 'back/publications/detail.html', {'publication': publication})


# Modification_d'une_publication
class PublicationUpdateView(LoginRequiredMixin, UpdateView): 
    model = Publication
    form_class = PublicationForm
    template_name = "back/publications/update.html"
    context_object_name = "publication"

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated and user.role == "admin":
            return reverse_lazy("publications:index")
        else:
            return reverse("portail_site:dashboard")

    def form_valid(self, form):
        messages.success(self.request, f"publication {self.request.POST.get('titre')} modifié avec succès !")
        return super().form_valid(form)

# Suppression_d'une_publication
class PublicationDeleteView(LoginRequiredMixin, DeleteView):
    model = Publication
    template_name = "back/publications/index.html"
    context_object_name = "publication"
    
    def get_success_url(self):
        user = self.request.user
        if hasattr(user, "role") and user.role == "admin":
            return reverse_lazy("publications:index")
        return reverse("portail_site:dashboard")
