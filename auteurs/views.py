from django.shortcuts import render, redirect, get_object_or_404
from auteurs.models import Auteur
from publications.models.publication import Publication
from auteurs.forms import AuteurForm
from accounts.models import CustumerUser
from institutions.models import Institution
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import TemplateView, CreateView, ListView, UpdateView, DeleteView




class AuteurCreateView(CreateView):
    model = Auteur
    form_class = AuteurForm
    template_name = 'back/auteurs/index.html'
    success_url = reverse_lazy("auteurs:index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated and getattr(user, "role", "") == "admin":
            context["auteurs"] = Auteur.objects.order_by('-id')
        else:
            publications = Publication.objects.filter(user=user)
            if publications.exists():
                auteurs_lies = Auteur.objects.filter(id__in=publications.values_list('auteurs', flat=True)).distinct().order_by('-id')
                context['auteurs'] = auteurs_lies
            else:
                pass
                # context["auteurs"] = Auteur.objects.filter(user=user).order_by('-id')
 
        return context
    

def profil_auteur_template_view(request):
    if request.method == 'POST':
        institution_id = request.POST.get('institution')
        try:
            institution = Institution.objects.get(pk=institution_id)
        except Institution.DoesNotExist:
            messages.error(request, "Institution invalide.")
            return redirect('auteurs:index')

        Auteur.objects.create(
            photo = request.FILES.get('photo'),
            prenoms = request.POST.get('prenoms'),
            nom = request.POST.get('nom'),
            email = request.POST.get('email'),
            orcid = request.POST.get('orcid'),
            statut = request.POST.get('statut'),
            institution = institution,  # ici on met l'objet
            facebook = request.POST.get('facebook'),
            twitter = request.POST.get('twitter'),
            linkedin = request.POST.get('linkedin'),
            site_web = request.POST.get('site_web'),
            biographie = request.POST.get('biographie')
        )

        statut_auteur = get_object_or_404(CustumerUser, id=request.user.id)
        statut_auteur.role = 'auteur'
        statut_auteur.photo = request.FILES.get('photo')
        statut_auteur.save()

        messages.success(request, 'Profil complété avec succès !')
        return redirect('auteurs:index')




class AuteurUpdateView(UpdateView):
    model          = Auteur
    form_class     = AuteurForm
    template_name = "back/auteurs/update.html"
    success_url = reverse_lazy("auteurs:index")
    context_object_name = "auteurs"

    def form_valid(self, form):
        messages.success(self.request, f"Auteur {self.request.POST.get('prenoms')} {self.request.POST.get('nom')} modifié avec succès !")
        return super().form_valid(form)

    
class AuteurDeleteView(DeleteView):
    model         = Auteur
    template_name = "back/auteurs/index.html"
    success_url   = reverse_lazy("auteurs:index")