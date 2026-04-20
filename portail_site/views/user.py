from django.shortcuts import render, redirect
from accounts.forms import CustumerUserForm, UserProfileForm
from institutions.forms import InstitutionForm
from accounts.models import CustumerUser
from django.contrib import messages
from django.contrib.auth import authenticate, login


# Envoi d'un email apres l'inscription sur le portail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.db import transaction

# Pour la vue d'activation du compte apres l'inscription
from django.utils.encoding import force_str




# La vue d'inscription au portail scientifique
def inscriptionTemplateView(request):
    if request.method == 'POST':
        form = CustumerUserForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            password1 = data['password1']
            password2 = data['password2']

            if password1 != password2:
                messages.error(request, 'Les mots de passe ne correspondent pas.')
            else:
                new_custumer = CustumerUser.objects.create(
                    prenoms=data['prenoms'],
                    nom=data['nom'],
                    email=data['email'],
                    tel=data['tel'],
                    sexe=data['sexe'],
                    is_active=False,  # important
                )
                new_custumer.set_password(password1)
                new_custumer.save()

                # Envoi de l’email d’activation
                current_site = get_current_site(request)
                mail_subject = 'Activation de votre compte'
                uid = urlsafe_base64_encode(force_bytes(new_custumer.pk))
                token = default_token_generator.make_token(new_custumer)
                activation_link = reverse('portail_site:activation', kwargs={'uidb64': uid, 'token': token})
                activation_url = f"http://{current_site.domain}{activation_link}"

                message = render_to_string('emails/activation_email.html', {
                    'user': new_custumer,
                    'activation_url': activation_url,
                })

                send_mail(
                    mail_subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [new_custumer.email],
                    fail_silently=False,
                )

                messages.success(request, "Inscription réussie. Veuillez vérifier votre email pour activer votre compte.")
                return redirect('portail_site:connexion')
        else:
            messages.error(request, "Formulaire invalide.")
    else:
        form = CustumerUserForm()

    return render(request, 'pages/inscription.html', {'form': form})


def inscription_compte_institution(request):
    form_institution = InstitutionForm()
    form_custumer = CustumerUserForm()
    form_user_profile = UserProfileForm()


    if request.method == 'POST':
        form_custumer = CustumerUserForm(request.POST)
        form_institution = InstitutionForm(request.POST)
        form_user_profile = UserProfileForm(request.POST, request.FILES)

        if form_custumer.is_valid() and form_institution.is_valid() and form_user_profile.is_valid():
            data_custumer = form_custumer.cleaned_data
            data_institution = form_institution.cleaned_data
            data_user_profile = form_user_profile.cleaned_data


            password1 = data_custumer['password1']
            password2 = data_custumer['password2']
            email = data_custumer['email']
            email_institution = data_institution['email_institution']
            site_web_institution = data_institution['site_web_institution'] 

            def domaine_email(email, site_web_institution):
                email_domain = email.split('@')[-1]
                institution_domain = site_web_institution.split('//')[-1].split('/')[0]
                return email_domain == institution_domain
            
            def domaine_email_institution(site_web_institution, email_institution):
                email_institution_domain = email_institution.split('@')[-1]
                institution_domain = site_web_institution.split('//')[-1].split('/')[0]
                return email_institution_domain == institution_domain
            
            if not domaine_email(email, site_web_institution):
                messages.error(request, "Votre email n'est pas un email professionnel de l'institution.")
                return redirect('portail_site:inscription_institution')

            elif not domaine_email_institution(site_web_institution, email_institution):
                messages.error(request, "L'email de l'institution doit appartenir à son site web.")
                return redirect('portail_site:inscription_institution')

            elif password1 != password2:
                messages.error(request, "Les mots de passe ne correspondent pas.")
                return redirect('portail_site:inscription_institution')
            
            else:
                with transaction.atomic():
                    new_custumer = CustumerUser.objects.create_user(
                        prenoms=data_custumer['prenoms'],
                        nom=data_custumer['nom'],
                        email=data_custumer['email'],
                        tel=data_custumer['tel'],
                        sexe=data_custumer['sexe'],
                        password=password1,
                        is_active=False,
                    )

                    user_profil = new_custumer.profile  # récupère le profil créé par le signal

                    # mise à jour des champs
                    for field, value in data_user_profile.items():
                        setattr(user_profil, field, value)
                    user_profil.save()

                    institution = form_institution.save(commit=False)
                    institution.user = new_custumer
                    institution.save()

                    user_profil.institution = institution
                    user_profil.save()

                    # Envoi de l’email d’activation
                    current_site = get_current_site(request)
                    mail_subject = 'Activation de votre compte'
                    uid = urlsafe_base64_encode(force_bytes(new_custumer.pk))
                    token = default_token_generator.make_token(new_custumer)
                    activation_link = reverse('portail_site:activation', kwargs={'uidb64': uid, 'token': token})
                    activation_url = f"http://{current_site.domain}{activation_link}"

                    message = render_to_string('emails/activation_email.html', {
                        'user': new_custumer,
                        'activation_url': activation_url,
                    })

                    send_mail(
                        mail_subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [new_custumer.email],
                        fail_silently=False,
                    )

                    messages.success(request, "Inscription réussie. Veuillez vérifier votre email pour activer votre compte.")
                    return redirect('portail_site:connexion')
        else:
            print("Formulaire CustumerUser:", form_custumer.errors)
            print("Formulaire Institution:", form_institution.errors)
            print("Formulaire Profil Utilisateur:", form_user_profile.errors)
    else:
        form_custumer = CustumerUserForm()
        form_institution = InstitutionForm()
        form_user_profile = UserProfileForm()

    return render(request, 'pages/compte_institution.html', {'form_custumer': form_custumer, 'form_institution': form_institution, 'form_user_profile': form_user_profile})



def inscription_compte_enseignant(request):
    form_custumer = CustumerUserForm()
    form_user_profile = UserProfileForm()

    if request.method == 'POST':
        form_custumer = CustumerUserForm(request.POST)
        form_user_profile = UserProfileForm(request.POST, request.FILES)

        if form_custumer.is_valid() and form_user_profile.is_valid():

            data_custumer = form_custumer.cleaned_data
            data_user_profile = form_user_profile.cleaned_data

            password1 = data_custumer['password1']
            password2 = data_custumer['password2']
            email = data_custumer['email']
            data_institution = data_user_profile['institution']
            email_institution = data_institution.email_institution
            site_web_institution = data_institution.site_web_institution

            def domaine_email(email, site_web_institution):
                email_domain = email.split('@')[-1]
                institution_domain = site_web_institution.split('//')[-1].split('/')[0]
                return email_domain == institution_domain
            
            def domaine_email_institution(site_web_institution, email_institution):
                email_institution_domain = email_institution.split('@')[-1]
                institution_domain = site_web_institution.split('//')[-1].split('/')[0]
                return email_institution_domain == institution_domain
            
            if not domaine_email(email, site_web_institution):
                messages.error(request, "Votre email n'est pas un email professionnel de l'institution.")
                return redirect('portail_site:inscription_enseignant')
            
            elif not domaine_email_institution(site_web_institution, email_institution):
                messages.error(request, "L'email de l'institution doit appartenir à son site web.")
                return redirect('portail_site:inscription_enseignant')
            
            elif password1 != password2:
                messages.error(request, "Les mots de passe ne correspondent pas.")
                return redirect('portail_site:inscription_enseignant')

            else:
                with transaction.atomic():
                    new_custumer = CustumerUser.objects.create_user(
                        prenoms=data_custumer['prenoms'],
                        nom=data_custumer['nom'],
                        email=data_custumer['email'],
                        tel=data_custumer['tel'],
                        sexe=data_custumer['sexe'],
                        password=password1,
                        is_active=False,
                    )

                    user_profil = new_custumer.profile  # récupère le profil créé par le signal
                    institution = data_user_profile['institution']
                    user_profil.institution = institution  # Associe l'institution au profil utilisateur

                    # mise à jour des champs
                    for field, value in data_user_profile.items():
                        setattr(user_profil, field, value)
                    user_profil.save()

                    institution.user = new_custumer
                    institution.save()

                    # Envoi de l’email d’activation
                    current_site = get_current_site(request)
                    mail_subject = 'Activation de votre compte'
                    uid = urlsafe_base64_encode(force_bytes(new_custumer.pk))
                    token = default_token_generator.make_token(new_custumer)
                    activation_link = reverse('portail_site:activation', kwargs={'uidb64': uid, 'token': token})
                    activation_url = f"http://{current_site.domain}{activation_link}"

                    message = render_to_string('emails/activation_email.html', {
                        'user': new_custumer,
                        'activation_url': activation_url,
                    })

                    send_mail(
                        mail_subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [new_custumer.email],
                        fail_silently=False,
                    )

                    messages.success(request, "Inscription réussie. Veuillez vérifier votre email pour activer votre compte.")
                    return redirect('portail_site:connexion')
        else:
            print("Formulaire CustumerUser:", form_custumer.errors)
            print("Formulaire Profil Utilisateur:", form_user_profile.errors)
    else:
        form_custumer = CustumerUserForm()
        form_user_profile = UserProfileForm()

    return render(request, 'pages/compte_enseignant.html', {'form_custumer': form_custumer, 'form_user_profile': form_user_profile })



# La vue d'activation du compte au portail
def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustumerUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustumerUser.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Votre compte a été activé avec succès. Vous pouvez maintenant vous connecter.")
        return redirect('portail_site:connexion')
    else:
        messages.error(request, "Le lien d’activation est invalide ou a expiré.")
        return redirect('portail_site:inscription')




# La vue de connexion au portail 
def user_login_view(request, *args, **kwargs):
    
    if request.method == 'POST':
        
        email = request.POST.get('email')
        
        password = request.POST.get('password')
        
        user = CustumerUser.objects.filter(email=email)
        
        if user.exists():
            
            if user.first().is_active:
                
                user = authenticate(request, email=email, password=password)
                
                if user is not None:
                    
                    login(request, user)
                    
                    messages.success(request, 'Vous êtes connectés.')
                    
                else:
                    messages.error(request, "Le nom d'utilisateur ou le mot de passe est incorrecte.")
                    
            else:
                messages.error(request, "Votre compte n'est pas encore activé. Veuillez vérifier votre boite de reception email.")
                
        else:
            messages.error(request, "Le nom d'utilisateur ou le mot de passe est incorrecte.")
            
        return redirect('accounts:profil_user')  
         
    return render(request, 'registration/login.html', {})