from django.shortcuts import render, redirect
from encadreurs.models import Encadreur
from publications.models import Publication
from encadreurs.forms import EncadreurForm
from auteurs.forms import AuteurForm
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, ListView, UpdateView, DeleteView


class EncadreurCreateView(CreateView):
    model = Encadreur
    form_class = EncadreurForm
    template_name = 'back/encadreurs/index.html'
    success_url = reverse_lazy("encadreurs:index")

    def dispatch(self, request, *args, **kwargs):
        # Si l'utilisateur n'a pas de rôle, on affiche un autre formulaire
        if not request.user.is_authenticated or not request.user.role:
            messages.info(request, "Veuillez compléter votre profil avant de continuer.")
            form = AuteurForm()
            return render(request, 'back/auteurs/profil_auteur.html', {'form': form})
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
            self.object = form.save()
            messages.success(self.request, "Encadreur ajouté avec succès !")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated and getattr(user, "role", "") == "admin":
            # Admin voit tous les encadreurs
            context["encadreurs"] = Encadreur.objects.order_by('-id')
        else:
            # Publications créées par cet utilisateur
            publications = Publication.objects.filter(user=user)
            
            if publications.exists():
                # Encadreurs liés à ces publications
                encadreurs_lies = Encadreur.objects.filter(id__in=publications.values_list('encadreurs', flat=True)).distinct()
                context['encadreurs'] = encadreurs_lies
            else:
                # Sinon, on affiche les encadreurs que l'utilisateur a créés
                context['encadreurs'] = Encadreur.objects.filter(user=user).order_by('-id')

        return context


class EncadreurUpdateView(UpdateView):
    model          = Encadreur
    form_class     = EncadreurForm
    template_name = "back/encadreurs/update.html"
    success_url = reverse_lazy("encadreurs:index")
    context_object_name = "encadreurs"

    def form_valid(self, form):
        messages.success(self.request, f"Encadreur {self.request.POST.get('prenoms')} {self.request.POST.get('nom')} modifié avec succès !")
        return super().form_valid(form)

    
class EncadreurDeleteView(DeleteView):
    model         = Encadreur
    template_name = "back/encadreurs/index.html"
    success_url   = reverse_lazy("encadreurs:index")