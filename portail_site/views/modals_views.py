from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from accounts.models import *
from accounts.forms import *
from django.contrib.auth.decorators import login_required



def check_owner(request, slug):
    """Helper pour vérifier que le profil appartient bien à l'utilisateur connecté."""
    profile = get_object_or_404(UserProfile, slug=slug)
    if profile.user != request.user:
        return None, HttpResponseForbidden("Vous n'êtes pas autorisé à modifier ce profil.")
    return profile, None

@login_required
def modal_profil(request, slug):
    profile, error = check_owner(request, slug)
    if error: return error
    
    user = profile.user
    if request.method == 'POST':
        form_custumer = CustumerUserChangeForm(request.POST, instance=user)
        form_profile = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form_custumer.is_valid() and form_profile.is_valid():
            form_custumer.save() 
            form_profile.save()
            messages.success(request, 'Informations de profil mises à jour.')
            # return HttpResponse('<script>window.location.reload();</script>')
            return redirect('accounts:profil_user')
    else:
        form_custumer = CustumerUserChangeForm(instance=user)
        form_profile = UserProfileForm(instance=profile)
    
    return render(request, 'back/modals/profil.html', {
        'form_custumer_user': form_custumer, 
        'form_user_profile': form_profile
    })

@login_required
def modal_biographie(request, slug):
    
    profile, error = check_owner(request, slug)
    if error: return error
    
    # Get or create biography for the user
    bio_obj, created = User_biography.objects.get_or_create(user=profile.user)
    
    if request.method == 'POST':
        form = User_biographyForm(request.POST, instance=bio_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Biographie mise à jour.')
            return redirect('accounts:profil_user')
        
    else: 
        form = User_biographyForm(instance=bio_obj)
    
    return render(request, 'back/modals/biographie.html', {'form': form})

@login_required
def modal_emploi(request, slug, pk=None):
    profile, error = check_owner(request, slug)
    if error: return error
    
    if pk:
        emploi_obj = get_object_or_404(User_emploi, pk=pk, user=profile.user)
    else:
        emploi_obj = User_emploi(user=profile.user)
    
    if request.method == 'POST':
        form = User_emploiForm(request.POST, instance=emploi_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Emploi enregistré.')
            return redirect('accounts:profil_user')
    else:
        form = User_emploiForm(instance=emploi_obj)
    
    return render(request, 'back/modals/emploi.html', {'form': form})

@login_required
def modal_education_qualification(request, slug, pk=None):
    profile, error = check_owner(request, slug)
    if error: return error
    
    if pk:
        edu_obj = get_object_or_404(User_etude_academique, pk=pk, user=profile.user)
    else:
        edu_obj = User_etude_academique(user=profile.user)
    
    if request.method == 'POST':
        form = User_etude_academiqueForm(request.POST, instance=edu_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Formation enregistrée.')
            return redirect('accounts:profil_user')
    else:
        form = User_etude_academiqueForm(instance=edu_obj)
    
    return render(request, 'back/modals/education_qualification.html', {'form': form})

@login_required
def modal_experience_professionnelle(request, slug, pk=None):
    profile, error = check_owner(request, slug)
    if error: return error
    
    if pk:
        exp_obj = get_object_or_404(User_experience_professionnelle, pk=pk, user=profile.user)
    else:
        exp_obj = User_experience_professionnelle(user=profile.user)
    
    if request.method == 'POST':
        form = User_experience_professionnelleForm(request.POST, instance=exp_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expérience enregistrée.')
            return redirect('accounts:profil_user')
    else:
        form = User_experience_professionnelleForm(instance=exp_obj)
    
    return render(request, 'back/modals/experience_professionnelle.html', {'form': form})

@login_required
def modal_travaux_recherche(request, slug, pk=None):
    profile, error = check_owner(request, slug)
    if error: return error
    
    if pk:
        travaux_obj = get_object_or_404(User_travaux_recherche, pk=pk, user=profile.user)
    else:
        travaux_obj = User_travaux_recherche(user=profile.user)
    
    if request.method == 'POST':
        form = User_travaux_rechercheForm(request.POST, instance=travaux_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Travaux de recherche enregistrés.')
            return redirect('accounts:profil_user')
    else:
        form = User_travaux_rechercheForm(instance=travaux_obj)
    
    return render(request, 'back/modals/travaux_recherche.html', {'form': form})

@login_required
def modal_reseaux_sociaux(request, slug):
    profile, error = check_owner(request, slug)
    if error: return error
    
    if request.method == 'POST':
        # On utilise UserProfileForm mais on ne traite que les champs réseaux sociaux si on veut être strict, 
        # mais le plus simple est de réutiliser UserProfileForm.
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Réseaux sociaux mis à jour.')
            return redirect('accounts:profil_user')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'back/modals/reseaux_sociaux.html', {'form': form})

@login_required
def modal_detail_activite(request, model_name, pk):
    models_dict = {
        'emploi': User_emploi,
        'education': User_etude_academique,
        'experience': User_experience_professionnelle,
        'travaux': User_travaux_recherche
    }
    
    model = models_dict.get(model_name)
    
    if not model:
        return HttpResponse("Modèle non trouvé", status=404)
    
    # On récupère l'objet en s'assurant qu'il appartient bien à l'utilisateur connecté (sécurité)
    item = get_object_or_404(model, pk=pk, user=request.user)
    
    return render(request, f'back/modals/details/{model_name}.html', {'item': item})