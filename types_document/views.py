from django.shortcuts import render
from types_document.models import TypeDocument
from types_document.forms import TypeDocumentForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView, CreateView, ListView, UpdateView, DeleteView


class DocumentCreateView(CreateView):
    model = TypeDocument
    form_class = TypeDocumentForm
    template_name = 'back/types_document/index.html'
    success_url = reverse_lazy("types_document:index")

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
            self.object = form.save()
            messages.success(self.request, "Document ajoutée avec succès !")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documents"] = TypeDocument.objects.order_by('-id')
        return context
    
class DocumentUpdateView(UpdateView):
    model          = TypeDocument
    form_class     = TypeDocumentForm
    template_name = "back/types_document/update.html"
    success_url = reverse_lazy("types_document:index")
    context_object_name = "document"

    def form_valid(self, form):
        messages.success(self.request, f"Document {self.request.POST.get('libelle')} modifié avec succès !")
        return super().form_valid(form)

    
class DocumentDeleteView(DeleteView):
    model         = TypeDocument
    template_name = "back/types_document/index.html"
    success_url   = reverse_lazy("types_document:index")