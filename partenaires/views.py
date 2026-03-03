from django.shortcuts import render, redirect, get_object_or_404
from partenaires.models import Partenaire
from partenaires.forms import PartenaireForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, UpdateView, DeleteView



# La vue d'ajout de partenaire
class PartenaireCreateView(CreateView):
    model = Partenaire
    form_class = PartenaireForm
    template_name = 'back/partenaires/index.html'
    success_url = reverse_lazy("partenaires:index")

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
        messages.success(self.request, "Partenaire ajouté avec succès !")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        partenaire_list = Partenaire.objects.order_by('-id')
        
        paginator = Paginator(partenaire_list, 6)

        page_number = self.request.GET.get("page")
        
        page_obj = paginator.get_page(page_number)

        context["page_obj"] = page_obj
        return context
    
@require_POST
def update_partenaire_state(request):
    partenaire_id = request.POST.get('partenaire_id')
    partenaire = get_object_or_404(Partenaire, id=partenaire_id)
    partenaire.is_actif = not partenaire.is_actif
    partenaire.save()
    return redirect('partenaires:index')

# La vue de modification des informations d'un partenaire
class PartenairerUpdateView(UpdateView):
    model          = Partenaire
    form_class     = PartenaireForm
    template_name = "back/partenaires/update.html"
    success_url = reverse_lazy("partenaires:index")
    context_object_name = "partenaires"

    def form_valid(self, form):
        messages.success(self.request, f"partenaire {self.request.POST.get('nom')} modifié avec succès !")
        return super().form_valid(form)

# La vue de suppression de partenaires
class PartenaireDeleteView(DeleteView):
    model         = Partenaire
    template_name = "back/partenaires/index.html"
    success_url   = reverse_lazy("partenaires:index")