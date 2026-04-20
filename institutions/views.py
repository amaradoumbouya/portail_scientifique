from django.shortcuts import render
from institutions.models import Institution
from institutions.forms import InstitutionForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView, CreateView, ListView, UpdateView, DeleteView


class InstitutionCreateView(CreateView):
    model = Institution
    form_class = InstitutionForm
    template_name = 'back/institutions/index.html'
    success_url = reverse_lazy("institutions:index")

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
            self.object = form.save()
            messages.success(self.request, "Institution ajoutée avec succès !")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["institutions"] = Institution.objects.order_by('-id')
        return context
    
class InstitutionUpdateView(UpdateView):
    model          = Institution
    form_class     = InstitutionForm
    template_name = "back/institutions/update.html"
    success_url = reverse_lazy("institutions:index")
    context_object_name = "institution"

    def form_valid(self, form):
        messages.success(self.request, f"Institution {self.request.POST.get('nom_institution')} modifié avec succès !")
        return super().form_valid(form)

    
class InstitutionDeleteView(DeleteView):
    model         = Institution
    template_name = "back/institutions/index.html"
    success_url   = reverse_lazy("institutions:index")