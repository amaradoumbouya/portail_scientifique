from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse, reverse_lazy
from accounts.models import CustumerUser
from accounts.forms import CustumerUserForm, CustumerUserChangeForm, CustumerUserChangePasswordForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import CreateView, UpdateView, DeleteView


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

        custumer_list = CustumerUser.objects.order_by('-id')
        q = self.request.GET.get('q', '').strip()
        if q:
            custumer_list = custumer_list.filter(
                Q(prenoms__icontains=q)
                | Q(nom__icontains=q)
                | Q(email__icontains=q)
                | Q(tel__icontains=q)
            )

        paginator = Paginator(custumer_list, 6)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        context["page_obj"] = page_obj
        return context


def Update_state(request):
    if request.method == 'POST':
        state = request.POST.get('is_active')
        id_state = request.POST.get('id_state')
        state_object = CustumerUser.objects.get(id=id_state, is_active=state)
        if state_object.is_active == 0:
            state_object.is_active = True
            state_object.save()
        else:
            state_object.is_active = False
            state_object.save()
    return redirect('accounts:index')


class CustumUserUpdateView(UpdateView):
    model = CustumerUser
    form_class = CustumerUserChangeForm
    template_name = "back/accounts/update.html"
    success_url = reverse_lazy("accounts:index")
    context_object_name = "custumer"

    def form_valid(self, form):
        messages.success(
            self.request,
            f"{self.request.POST.get('role')} {self.request.POST.get('prenoms')} {self.request.POST.get('nom')} modifié avec succès !",
        )
        return super().form_valid(form)


class CustumUserDeleteView(DeleteView):
    model = CustumerUser
    template_name = "back/accounts/index.html"
    success_url = reverse_lazy("accounts:index")


@login_required
def profil_user_template_view(request):
    if hasattr(request.user, "profile"):
        profile = request.user.profile
        if not profile.slug:
            profile.save()
    return render(request, 'back/accounts/profil_user.html')


@login_required
def changer_mot_de_passe(request):
    if request.method == 'POST':
        form = CustumerUserChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Votre mot de passe a été modifié avec succès.")
            return redirect('accounts:profil_user')
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = CustumerUserChangePasswordForm(request.user)

    return render(request, 'back/accounts/changer_mot_de_passe.html', {'form': form})


@login_required
def verrouiller(request):
    """Verrouille l'écran sans déconnecter l'utilisateur."""
    request.session['screen_locked'] = True
    referer = request.META.get('HTTP_REFERER')
    if referer and request.get_host() in referer:
        request.session['screen_lock_next'] = referer
    else:
        request.session['screen_lock_next'] = reverse('accounts:profil_user')
    return redirect('accounts:deverrouiller')


@login_required
def deverrouiller(request):
    """Demande le mot de passe pour déverrouiller l'écran."""
    if not request.session.get('screen_locked'):
        next_url = request.session.pop('screen_lock_next', reverse('accounts:profil_user'))
        return redirect(next_url)

    if request.method == 'POST':
        password = request.POST.get('password', '')
        if password and request.user.check_password(password):
            request.session['screen_locked'] = False
            next_url = request.session.pop('screen_lock_next', reverse('accounts:profil_user'))
            messages.success(request, "Écran déverrouillé.")
            return redirect(next_url)
        messages.error(request, "Mot de passe incorrect.")

    return render(request, 'back/accounts/verrouiller.html')
