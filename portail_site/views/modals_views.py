from email.mime import message

from django.shortcuts import render
from django.contrib import messages
from accounts.models import UserProfile, CustumerUser
from accounts.forms import UserProfileForm, CustumerUserForm
from django.contrib.auth.decorators import login_required



# Vue UserProfile pour la modification du profil de l'utilisateur
def modal_profil(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form_custumer_user = CustumerUserForm( request.POST, instance=user)
        form_user_profile = UserProfileForm(request.POST, request.FILES, instance=profile)
        print("Formulaire CustumerUser valide :", form_custumer_user.is_valid())
        print("Formulaire UserProfile valide :", form_user_profile.is_valid())
        if form_custumer_user.is_valid() and form_user_profile.is_valid():
            form_custumer_user.save()
            form_user_profile.save()
            messages.success(request, 'Profil mis à jour avec succès.')

    else:
        form_custumer_user = CustumerUserForm(instance=user)
        form_user_profile = UserProfileForm(instance=profile)
    return render(request, 'back/modals/profil.html', {'form_custumer_user': form_custumer_user, 'form_user_profile': form_user_profile})

# Vue pour le modal de biographie
def modal_biographie(request):
    return render(request, 'back/modals/biographie.html')

# Vue pour le modal d'emploi
def modal_emploi(request):
    return render(request, 'back/modals/emploi.html')

# Vue pour le modal education_qualification
def modal_education_qualification(request):
    return render(request, 'back/modals/education_qualification.html')

# Vue pour le modal experience_professionnelle
def modal_experience_professionnelle(request):
    return render(request, 'back/modals/experience_professionnelle.html')

# Vue pour le modal travaux_recherche
def modal_travaux_recherche(request):
    return render(request, 'back/modals/travaux_recherche.html')

# Vue pour le modal reseaux_sociaux
def modal_reseaux_sociaux(request):
    return render(request, 'back/modals/reseaux_sociaux.html')