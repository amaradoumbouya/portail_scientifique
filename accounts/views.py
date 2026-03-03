from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from accounts.models import CustumerUser
from accounts.forms import CustumerUserForm
from django.core.paginator import Paginator
from django.views.generic import TemplateView, CreateView, ListView, UpdateView, DeleteView, DetailView





class AccountCreateView(CreateView):
    model = CustumerUser
    form_class = CustumerUserForm
    template_name = 'back/accounts/index.html'
    success_url = reverse_lazy('accounts:index')
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f" {self.request.role} ajouté avec succès !")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer tous les utilisateurs
        custumer_list = CustumerUser.objects.order_by('-id')
        
        # Initialiser le paginator
        paginator = Paginator(custumer_list, 6)  # 6 éléments par page

        # Récupérer le numéro de page depuis l'URL
        page_number = self.request.GET.get("page")
        
        # Extraire la page courante
        page_obj = paginator.get_page(page_number)

        # Ajouter dans le contexte
        context["page_obj"] = page_obj
        return context
    

def Update_state(request):
    if request.method == 'POST':
        state = request.POST.get('is_active')
        id_state = request.POST.get('id_state')
        state_object = CustumerUser.objects.get( id=id_state,is_active=state)
        if state_object.is_active == 0:
            state_object.is_active = True
            state_object.save()
        else:
            state_object.is_active = False
            state_object.save()
    return redirect('accounts:index')


class CustumUserUpdateView(UpdateView):
    model          = CustumerUser
    form_class     = CustumerUserForm
    template_name = "back/accounts/update.html"
    success_url = reverse_lazy("accounts:index")
    context_object_name = "custumer"

    def form_valid(self, form):
        messages.success(self.request, f"{self.request.POST.get('role')} {self.request.POST.get('prenoms')} {self.request.POST.get('nom')} modifié avec succès !")
        return super().form_valid(form)

    

class CustumUserDeleteView(DeleteView):
    model         = CustumerUser
    template_name = "back/accounts/index.html"
    success_url   = reverse_lazy("accounts:index")