from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import CustumerUser
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from projets_detudes.forms.projet_forms import ProjetForm
from projets_detudes.forms.canevas_forms import CanevasProjetForm
from projets_detudes.models.projet import ProjetEtude
from projets_detudes.models.participant import Participant
from projets_detudes.models.candidate import Candidate
from projets_detudes.models.planing import PlanningEncadrement
from projets_detudes.forms.planing_forms import PlanningEncadrementForm
from projets_detudes.models.canevas import CanevasProjet
from projets_detudes.models.tache import Tache
from projets_detudes.forms.tache_forms import TacheForm
from django.utils.crypto import get_random_string

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
from django.db.models import Q





def projet_etude_index(request):
    return render(request, 'back/projet_etude/index.html', )

# Vue pour le modal de memoire de master
def modal_memoire_de_master(request):

    if request.method == 'POST':

        form_memoire = ProjetForm(request.POST)

        if form_memoire.is_valid():

            data_memoire = form_memoire.cleaned_data

            titre = data_memoire['titre']
            description = data_memoire['description']

            if request.user.is_authenticated:
                
                user = request.user
                
                # Verification: User doit être un candidat
                if not hasattr(user, 'candidate'):
                    return redirect('portail_site:dashboard')
                    
                candidate = user.candidate

                try:
                    with transaction.atomic():

                        # Creation du projet d'étude
                        memoire = ProjetEtude.objects.create(
                            type_projet=ProjetEtude.TypeProjet.MEMOIRE,
                            titre=titre,
                            description=description,
                            createur=user,
                            candidate=candidate,
                        )

                        # Ajouter user comme l'auteur principal du projet de mémoire
                        Participant.objects.get_or_create(user=user, projet=memoire, defaults={'role': 'Auteur principal'})

                        # Ajout des auteurs
                        i = 0
                        while True:
                            nom = request.POST.get(f"auteurs[{i}][nom]")
                            if not nom:
                                break
                            prenoms = request.POST.get(f"auteurs[{i}][prenoms]")
                            email = request.POST.get(f"auteurs[{i}][email]")
                            tel = request.POST.get(f"auteurs[{i}][tel]")
                            role = request.POST.get(f"auteurs[{i}][role]")

                            # Vérification existence utilisateur 
                            participant_as_user = CustumerUser.objects.filter(email=email).first()


                            # Si utilisateur inexistant
                            if not participant_as_user:
                                password_par_defaut = get_random_string(10)

                                # Ajouter l'auteur en tant qu'utilisateur
                                participant_as_user = CustumerUser.objects.create_user(email=email, prenoms=prenoms, nom=nom,tel=tel, password=password_par_defaut)

                                # Ajouter co-auteur en tant que participant du projet de mémoire
                                Participant.objects.get_or_create(user=participant_as_user, projet=memoire, defaults={'role': role})

                                # Envoi de l’email d’activation
                                current_site = get_current_site(request)
                                mail_subject = 'Activation de votre compte'
                                uid = urlsafe_base64_encode(force_bytes(participant_as_user.pk))
                                token = default_token_generator.make_token(participant_as_user)
                                activation_link = reverse('portail_site:activation', kwargs={'uidb64': uid, 'token': token})
                                activation_url = f"http://{current_site.domain}{activation_link}"
                                message = render_to_string('emails/activation_email_participant.html',
                                    {
                                        'user': participant_as_user,
                                        'role': participant_as_user.participant_set.filter(projet=memoire).first().role,
                                        'password': password_par_defaut,
                                        'activation_url': activation_url,
                                    }
                                )
                                send_mail(
                                    mail_subject,
                                    '',
                                    settings.DEFAULT_FROM_EMAIL,
                                    [participant_as_user.email],
                                    html_message=message,
                                    fail_silently=False,
                                )

                            else:
                                # Si l'utilisateur existe déjà, l'ajouter directement en tant que participant du projet de mémoire
                                Participant.objects.get_or_create(user=participant_as_user, projet=memoire, defaults={'role': role})

                                # Envoi de l’email d'information de participation au projet
                                current_site = get_current_site(request)
                                login_url = (f"http://{current_site.domain}/connexion/")
                                mail_subject = (
                                    'Information de participation '
                                    'au projet de mémoire'
                                )
                                message = render_to_string('emails/information_participant.html',
                                    {
                                        'user': participant_as_user,
                                        'login_url': login_url,
                                        'role': participant_as_user.participant_set.filter(projet=memoire).first().role,
                                    }
                                )
                                send_mail(
                                    mail_subject,
                                    '',
                                    settings.DEFAULT_FROM_EMAIL,
                                    [participant_as_user.email],
                                    html_message=message,
                                    fail_silently=False,
                                )
                            i += 1
            

                        # Ajout des encadrants
                        j = 0
                        while True:
                            nom = request.POST.get(f"encadreurs[{j}][nom]")
                            if not nom:
                                break
                            prenoms = request.POST.get(f"encadreurs[{j}][prenoms]")
                            email = request.POST.get(f"encadreurs[{j}][email]")
                            tel = request.POST.get(f"encadreurs[{j}][tel]")
                            role = request.POST.get(f"encadreurs[{j}][role]")

                            # Vérifier l'existence de l'encadreur dans la table des utilisateurs
                            encadrant_as_user = CustumerUser.objects.filter(email=email).first()

                            # Si encadrant inexistant
                            if not encadrant_as_user:
                                password_par_defaut = get_random_string(10)

                                encadrant_as_user = CustumerUser.objects.create_user(email=email, prenoms=prenoms, nom=nom, tel=tel, password=password_par_defaut)

                                # Ajouter l'encadrant en tant que participant du projet de mémoire
                                Participant.objects.get_or_create(user=encadrant_as_user,projet=memoire,defaults={'role': role})

                                # Envoi de l’email d’activation
                                current_site = get_current_site(request)
                                mail_subject = ('Activation de votre compte')
                                uid = urlsafe_base64_encode(force_bytes(encadrant_as_user.pk))
                                token = default_token_generator.make_token(encadrant_as_user)
                                activation_link = reverse('portail_site:activation', kwargs={'uidb64': uid, 'token': token})
                                activation_url = f"http://{current_site.domain}{activation_link}"
                                message = render_to_string('emails/activation_email_participant.html',
                                    {
                                        'user': encadrant_as_user,
                                        'role': encadrant_as_user.participant_set.filter(projet=memoire).first().role,
                                        'password': password_par_defaut,
                                        'activation_url': activation_url,
                                    }
                                )
                                send_mail(
                                    mail_subject,
                                    '',
                                    settings.DEFAULT_FROM_EMAIL,
                                    [encadrant_as_user.email],
                                    html_message=message,
                                    fail_silently=False,
                                )

                            else:
                                # Si l'encadrant existe déjà, l'ajouter directement en tant que participant du projet de mémoire
                                Participant.objects.get_or_create(user=encadrant_as_user, projet=memoire, defaults={'role': role})


                                # Envoi de l’email d'information de participation au projet
                                current_site = get_current_site(request)
                                login_url = (f"http://{current_site.domain}/connexion/")
                                mail_subject = (
                                    'Information de participation '
                                    'au projet de mémoire'
                                )
                                message = render_to_string(
                                    'emails/information_participant.html',
                                    {
                                        'user': encadrant_as_user,
                                        'role': encadrant_as_user.participant_set.filter(projet=memoire).first().role,
                                        'login_url': login_url,
                                    }
                                )
                                send_mail(
                                    mail_subject,
                                    '',
                                    settings.DEFAULT_FROM_EMAIL,
                                    [encadrant_as_user.email],
                                    html_message=message,
                                    fail_silently=False,
                                )
                            j += 1

                    return redirect("projets_detudes:index")
                
                except Exception as e:

                    print("Erreur :", e)
                    
                    return render(request,'back/modals_projet/memoire.html',{"form_memoire": form_memoire,"error": str(e)})

            
    else:
        form_memoire = ProjetForm()
    return render(request, 'back/modals_projet/memoire.html', {"form_memoire":form_memoire})

# Vue pour le modal de thèse de doctorat
def modal_these_de_doctorat(request):

    if request.method == 'POST':

        form_these = ProjetForm(request.POST)

        if form_these.is_valid():

            data_these = form_these.cleaned_data

            titre = data_these['titre']
            description = data_these['description']

            if request.user.is_authenticated:
                
                user = request.user
                
                # Verification: User doit être un candidat
                if not hasattr(user, 'candidate'):
                    return redirect('portail_site:dashboard')
                    
                candidate = user.candidate

                try:
                    with transaction.atomic():

                        # Creation du projet d'étude
                        these = ProjetEtude.objects.create(
                            type_projet=ProjetEtude.TypeProjet.THESE,
                            titre=titre,
                            description=description,
                            createur=user,
                            candidate=candidate,
                        )

                        # Ajouter user comme l'auteur principal du projet de thèse
                        Participant.objects.get_or_create(user=user, projet=these, defaults={'role': 'Auteur principal'})

                        # Ajout des auteurs
                        i = 0
                        while True:
                            nom = request.POST.get(f"auteurs[{i}][nom]")
                            if not nom:
                                break
                            prenoms = request.POST.get(f"auteurs[{i}][prenoms]")
                            email = request.POST.get(f"auteurs[{i}][email]")
                            tel = request.POST.get(f"auteurs[{i}][tel]")
                            role = request.POST.get(f"auteurs[{i}][role]")

                            # Vérification existence utilisateur 
                            participant_as_user = CustumerUser.objects.filter(email=email).first()


                            # Si utilisateur inexistant
                            if not participant_as_user:
                                password_par_defaut = get_random_string(10)

                                # Ajouter l'auteur en tant qu'utilisateur
                                participant_as_user = CustumerUser.objects.create_user(email=email, prenoms=prenoms, nom=nom,tel=tel, password=password_par_defaut)

                                # Ajouter l'auteur en tant que participant du projet de thèse
                                Participant.objects.get_or_create(user=participant_as_user, projet=these, defaults={'role': role})

                                # Envoi de l’email d’activation
                                current_site = get_current_site(request)
                                mail_subject = 'Activation de votre compte'
                                uid = urlsafe_base64_encode(force_bytes(participant_as_user.pk))
                                token = default_token_generator.make_token(participant_as_user)
                                activation_link = reverse('portail_site:activation', kwargs={'uidb64': uid, 'token': token})
                                activation_url = f"http://{current_site.domain}{activation_link}"
                                message = render_to_string('emails/activation_email_participant.html',
                                    {
                                        'user': participant_as_user,
                                        'role': participant_as_user.participant_set.filter(projet=these).first().role,
                                        'password': password_par_defaut,
                                        'activation_url': activation_url,
                                    }
                                )
                                send_mail(
                                    mail_subject,
                                    '',
                                    settings.DEFAULT_FROM_EMAIL,
                                    [participant_as_user.email],
                                    html_message=message,
                                    fail_silently=False,
                                )

                            else:
                                # Si l'utilisateur existe déjà, l'ajouter directement en tant que participant du projet de thèse
                                Participant.objects.get_or_create(user=participant_as_user, projet=these, defaults={'role': role})

                                # Envoi de l’email d'information de participation au projet
                                current_site = get_current_site(request)
                                login_url = (f"http://{current_site.domain}/connexion/")
                                mail_subject = (
                                    'Information de participation '
                                    'au projet de thèse '
                                )
                                message = render_to_string('emails/information_participant.html',
                                    {
                                        'user': participant_as_user,
                                        'login_url': login_url,
                                        'role': participant_as_user.participant_set.filter(projet=these).first().role,
                                    }
                                )
                                send_mail(
                                    mail_subject,
                                    '',
                                    settings.DEFAULT_FROM_EMAIL,
                                    [participant_as_user.email],
                                    html_message=message,
                                    fail_silently=False,
                                )
                            i += 1
            

                        # Ajout des encadrants
                        j = 0
                        while True:
                            nom = request.POST.get(f"encadreurs[{j}][nom]")
                            if not nom:
                                break
                            prenoms = request.POST.get(f"encadreurs[{j}][prenoms]")
                            email = request.POST.get(f"encadreurs[{j}][email]")
                            tel = request.POST.get(f"encadreurs[{j}][tel]")
                            role = request.POST.get(f"encadreurs[{j}][role]")

                            # Vérifier l'existence de l'encadreur dans la table des utilisateurs
                            encadrant_as_user = CustumerUser.objects.filter(email=email).first()

                            # Si encadrant inexistant
                            if not encadrant_as_user:
                                password_par_defaut = get_random_string(10)

                                encadrant_as_user = CustumerUser.objects.create_user(email=email, prenoms=prenoms, nom=nom, tel=tel, password=password_par_defaut)

                                # Ajouter l'encadrant en tant que participant du projet de thèse
                                Participant.objects.get_or_create(user=encadrant_as_user,projet=these,defaults={'role': role})

                                # Envoi de l’email d’activation
                                current_site = get_current_site(request)
                                mail_subject = ('Activation de votre compte')
                                uid = urlsafe_base64_encode(force_bytes(encadrant_as_user.pk))
                                token = default_token_generator.make_token(encadrant_as_user)
                                activation_link = reverse('portail_site:activation', kwargs={'uidb64': uid, 'token': token})
                                activation_url = f"http://{current_site.domain}{activation_link}"
                                message = render_to_string('emails/activation_email_participant.html',
                                    {
                                        'user': encadrant_as_user,
                                        'role': encadrant_as_user.participant_set.filter(projet=these).first().role,
                                        'password': password_par_defaut,
                                        'activation_url': activation_url,
                                    }
                                )
                                send_mail(
                                    mail_subject,
                                    '',
                                    settings.DEFAULT_FROM_EMAIL,
                                    [encadrant_as_user.email],
                                    html_message=message,
                                    fail_silently=False,
                                )

                            else:
                                # Si l'encadrant existe déjà, l'ajouter directement en tant que participant du projet de thèse
                                Participant.objects.get_or_create(user=encadrant_as_user, projet=these, defaults={'role': role})


                                # Envoi de l’email d'information de participation au projet
                                current_site = get_current_site(request)
                                login_url = (f"http://{current_site.domain}/connexion/")
                                mail_subject = (
                                    'Information de participation '
                                    'au projet de thèse'
                                )
                                message = render_to_string(
                                    'emails/information_participant.html',
                                    {
                                        'user': encadrant_as_user,
                                        'role': encadrant_as_user.participant_set.filter(projet=these).first().role,
                                        'login_url': login_url,
                                    }
                                )
                                send_mail(
                                    mail_subject,
                                    '',
                                    settings.DEFAULT_FROM_EMAIL,
                                    [encadrant_as_user.email],
                                    html_message=message,
                                    fail_silently=False,
                                )
                            j += 1

                    return redirect("projets_detudes:index")
                
                except Exception as e:

                    print("Erreur :", e)
                    
                    return render(request,'back/modals_projet/these.html',{"form_these": form_these,"error": str(e)})

            
    else:
        form_these = ProjetForm()
    return render(request, 'back/modals_projet/these.html', {"form_these":form_these})

# Vue pour récupérer les étudiants liés à l'encadrant connecté
def liste_des_etudiants_a_encadrer(request):

    if request.user.is_authenticated:

        user = request.user

        # Tous les projets où l'utilisateur est directeur ou co-directeur, has_accepted="accepte"
        participants = Participant.objects.filter(user=user, role__in=["Directeur", "Co-directeur"]).select_related(
            "projet",
            "projet__candidate",
            "projet__candidate__user",
            "projet__candidate__institution"
        ).distinct()

        # Liste des projets
        projets = [participant.projet for participant in participants]

        # Liste des étudiants (sans doublons)
        etudiants = []
        ids_etudiants = []

        for projet in projets:
            if projet.candidate.id not in ids_etudiants:
                etudiants.append(projet.candidate)
                ids_etudiants.append(projet.candidate.id)

        # =========================
        # STATISTIQUES
        # =========================

        total_etudiants = len(etudiants)

        total_master = len([etudiant for etudiant in etudiants if etudiant.niveau == "master"])

        total_doctorat = len([etudiant for etudiant in etudiants if etudiant.niveau == "doctorat"])

        total_projets = len(projets)

        projets_en_cours = len([projet for projet in projets if projet.statut == "en_cours"])

        projets_termines = len([projet for projet in projets if projet.statut == "termine"])

        projets_soutenus = len([projet for projet in projets if projet.statut == "valide"])

        context = {
            "participants": participants,
            "projets": projets,
            "etudiants": etudiants,

            # Statistiques
            'total_etudiants': total_etudiants,
            'total_master': total_master,
            'total_doctorat': total_doctorat,
            'total_projets': total_projets,
            'projets_en_cours': projets_en_cours,
            'projets_termines': projets_termines,
            'projets_soutenus': projets_soutenus,
        }

        return render(
            request,
            "back/projet_etude/encadrements.html",
            context
        )
    
# Vue pour afficher le detail du projet d'etude ajouté par l'etudiant
def modal_voir_plus(request, slug):

    # Projet
    projet = get_object_or_404(ProjetEtude.objects.select_related('candidate','createur'), slug=slug)

    # Auteurs
    auteurs = Participant.objects.filter(projet=projet,role=Participant.Role.AUTEUR).select_related('user')

    # Co-auteurs
    coauteurs = Participant.objects.filter(projet=projet, role=Participant.Role.CO_AUTEUR).select_related('user')

    # Directeurs
    directeurs = Participant.objects.filter(projet=projet, role=Participant.Role.DIRECTEUR).select_related('user')

    # Co-directeurs
    codirecteurs = Participant.objects.filter(projet=projet, role=Participant.Role.CO_DIRECTEUR).select_related('user')

    context = {

        "projet": projet,

        "auteurs": auteurs,

        "coauteurs": coauteurs,

        "directeurs": directeurs,

        "codirecteurs": codirecteurs,

    }

    return render(request, "back/modals_projet/voir_plus.html", context)

# =========================================================
# AJOUT DU CANEVAS + ENVOI EMAIL
# =========================================================
def modal_canevas(request, slug):

    projet = get_object_or_404(ProjetEtude, slug=slug)

    canevas_form = CanevasProjetForm()
    
    if request.method == "POST":

        canevas_form = CanevasProjetForm(request.POST,request.FILES)

        if canevas_form.is_valid():
            canevas = canevas_form.save(commit=False)
            canevas.projet = projet
            canevas.cree_par = request.user
            canevas.save()

            # =====================================================
            # RECUPERATION ETUDIANT + CO-AUTEURS
            # =====================================================

            participants = Participant.objects.filter(projet=projet,
                role__in=[
                    Participant.Role.AUTEUR,
                    Participant.Role.CO_AUTEUR]).select_related('user')

            # =====================================================
            # ENVOI EMAIL
            # =====================================================

            for participant in participants:

                if participant.user.email:

                    sujet = ("Ajout d'un nouveau canevas")

                    message = f"""
                    Bonjour {participant.user.full_name},

                    Un nouveau canevas a été ajouté pour votre projet :

                    Titre du projet :{projet.titre}

                    Titre du canevas :{canevas.titre}

                    Description :{canevas.description}

                    Veuillez vous connecter à la plateforme pour consulter le document.

                    Cordialement,
                    Portail Scientifique
                    """

                    send_mail(

                        sujet,

                        message,

                        settings.DEFAULT_FROM_EMAIL,

                        [participant.user.email],

                        fail_silently=True

                    )

            messages.success(request, "Canevas ajouté avec succès.")

            return redirect('projets_detudes:etudiants_a_encadrer')

    context = {
        "canevas_form": canevas_form,
        "projet": projet
    }
    return render(request, "back/modals_projet/canevas.html", context)

# =========================================================
# MODIFIER UN CANEVAS
# =========================================================
def modal_canevas_modification(request, slug):

    canevas = get_object_or_404(CanevasProjet, slug=slug)

    form = CanevasProjetForm(instance=canevas)

    if request.method == "POST":

        form = CanevasProjetForm(request.POST, request.FILES, instance=canevas)

        if form.is_valid():
            form.save()
            messages.success(request, "Canevas modifié avec succès.")

            return redirect("projets_detudes:etudiants_a_encadrer")

    context = {
        "form": form,
        "canevas": canevas
    }
    return render(request, "back/modals_projet/canevas_modification.html", context)

# Vue pour lister ou afficher le canevas du processus à suivre pour l'elaboration du memoire ou de la thèse
def modal_canevas_liste(request, slug):

    # Projet concerné
    projet = get_object_or_404(ProjetEtude.objects.select_related('candidate','createur'),slug=slug)

    # Canevas associés au projet
    canevas = CanevasProjet.objects.filter(projet=projet).select_related('cree_par').order_by('-created_at')

    context = {
        "projet": projet,
        "canevas": canevas,
    }

    return render(request, "back/modals_projet/canevas_liste.html", context)

# =========================================================
# Vue pour ajouter le programme sur chaque etape du canevas
# AJOUT PLANNING D'ENCADREMENT
# + ENVOI EMAIL AUX AUTEURS / CO-AUTEURS
# =========================================================
def modal_planing(request, slug):

    # Projet
    projet = get_object_or_404(ProjetEtude, slug=slug)

    # Formulaire
    planning_form = PlanningEncadrementForm()

    if request.method == "POST":

        planning_form = PlanningEncadrementForm(request.POST)

        if planning_form.is_valid():
            planning = planning_form.save(commit=False)
            planning.projet = projet
            planning.cree_par = request.user
            planning.save()

            # =================================================
            # RECUPERATION AUTEURS + CO-AUTEURS
            # =================================================
            participants = Participant.objects.filter(projet=projet,
                role__in=[
                    Participant.Role.AUTEUR,
                    Participant.Role.CO_AUTEUR]).select_related('user')

            # =================================================
            # ENVOI EMAIL
            # =================================================
            for participant in participants:

                if participant.user.email:

                    sujet = ("Nouveau Programme")

                    message = f"""
                    Bonjour M/Mme {participant.user.full_name},

                    Un nouveau planning d'encadrement a été ajouté pour votre projet.

                    =====================================

                    Projet : {projet.titre}

                    Titre : {planning.titre}

                    Description : {planning.description}

                    Date du rendez-vous : {planning.date_rendez_vous}

                    Heure début : {planning.heure_debut}

                    Heure fin : {planning.heure_fin}

                    Lieu : {planning.lieu if planning.lieu else 'Non défini'}

                    Lien visioconférence : {planning.lien_visio if planning.lien_visio else 'Non défini'}

                    =====================================

                    Veuillez vous connecter à la plateforme pour consulter les détails.

                    Cordialement, Portail Scientifique
                    """

                    send_mail(

                        sujet,

                        message,

                        settings.DEFAULT_FROM_EMAIL,

                        [participant.user.email],

                        fail_silently=True

                    )

            messages.success(request, "Planning ajouté avec succès.")

            return redirect('projets_detudes:etudiants_a_encadrer')

    context = {
        "planning_form": planning_form,
        "projet": projet
    }
    return render(request, "back/modals_projet/planing.html", context)

# =========================================================
# LISTE DES PLANNINGS
# =========================================================
def liste_planing(request, slug):

    projet = get_object_or_404(ProjetEtude, slug=slug)

    planings = PlanningEncadrement.objects.filter(projet=projet).select_related('cree_par', 'canevas').order_by('date_rendez_vous', 'heure_debut')

    context = {
        "projet": projet,
        "planings": planings,
    }
    return render(request, "back/modals_projet/liste_planing.html", context)

# =========================================================
# MODIFICATION DU PLANNING
# =========================================================
def modal_modification_planing(request, slug):

    planning = get_object_or_404(PlanningEncadrement, slug=slug)

    projet = planning.projet

    planning_form = PlanningEncadrementForm(instance=planning)

    if request.method == "POST":
        planning_form = PlanningEncadrementForm(request.POST, instance=planning)

        if planning_form.is_valid():

            planning = planning_form.save()

            # =================================================
            # RECUPERATION AUTEURS + CO-AUTEURS
            # =================================================
            participants = Participant.objects.filter(projet=projet,
                role__in=[
                    Participant.Role.AUTEUR,
                    Participant.Role.CO_AUTEUR]).select_related('user')

            # =================================================
            # ENVOI EMAIL MODIFICATION
            # =================================================
            for participant in participants:

                if participant.user.email:

                    sujet = ("Modification du programme")

                    message = f"""
                    Bonjour M/Mme {participant.user.full_name},

                    Le planning d'encadrement de votre projet a été modifié.

                    =====================================

                    Projet :
                    {projet.titre}

                    Titre :
                    {planning.titre}

                    Description :
                    {planning.description}

                    Date du rendez-vous :
                    {planning.date_rendez_vous}

                    Heure début :
                    {planning.heure_debut}

                    Heure fin :
                    {planning.heure_fin}

                    Lieu :
                    {planning.lieu if planning.lieu else 'Non défini'}

                    Lien visioconférence :
                    {planning.lien_visio if planning.lien_visio else 'Non défini'}

                    Statut :
                    {planning.get_statut_display()}

                    =====================================

                    Veuillez consulter la plateforme
                    pour voir les modifications.

                    Cordialement,
                    Portail Scientifique
                    """

                    send_mail(

                        sujet,

                        message,

                        settings.DEFAULT_FROM_EMAIL,

                        [participant.user.email],

                        fail_silently=True

                    )

            messages.success(request, "Planning modifié avec succès.")

            return redirect('projets_detudes:etudiants_a_encadrer')

        else:

            print(planning_form.errors)

    context = {

        "planning_form": planning_form,

        "planning": planning,

        "projet": projet

    }

    return render(request, "back/modals_projet/modification_planing.html", context)

# =========================================================
# Vue pour assigner une tache l'etudiant
# AJOUTER UNE TACHE
# =========================================================
def modal_tache(request, slug):

    # Projet
    projet = get_object_or_404(ProjetEtude, slug=slug)

    # Formulaire
    tache_form = TacheForm(projet=projet)

    if request.method == "POST":

        tache_form = TacheForm(request.POST, request.FILES, projet=projet)

        if tache_form.is_valid():

            tache = tache_form.save(commit=False)

            # Association projet
            tache.projet = projet

            # Créateur
            tache.cree_par = request.user

            # Vérification sécurité canevas
            if tache.canevas.projet != projet:

                messages.error(request, "Le canevas sélectionné est invalide.")

                return redirect(request.META.get('HTTP_REFERER'))

            tache.save()

            # =========================================
            # EMAIL
            # =========================================
            if tache.assigne_a.email:

                sujet = ("Nouvelle tâche assignée")

                message = f"""
                Bonjour {tache.assigne_a.full_name},

                Une nouvelle tâche vous a été assignée.

                =====================================

                Projet : {projet.titre}

                Canevas : {tache.canevas.titre}

                Titre : {tache.titre}

                Description : {tache.description}

                Date début : {tache.date_debut}

                Date fin : {tache.date_fin}

                Priorité : {tache.get_priorite_display()}

                =====================================

                Veuillez consulter la plateforme.

                Cordialement,
                Portail Scientifique
                """

                send_mail(

                    sujet,

                    message,

                    settings.DEFAULT_FROM_EMAIL,

                    [tache.assigne_a.email],

                    fail_silently=True

                )

            messages.success(request, "Tâche ajoutée avec succès.")

            return redirect('projets_detudes:etudiants_a_encadrer')

        else:

            print(tache_form.errors)

    context = {
        
        "tache_form": tache_form,

        "projet": projet
    }
    return render(request, "back/modals_projet/tache.html", context)

# =========================================================
# Vue pour afficher la liste des tâches assignées à un etudiant
# LISTE DES TACHES
# =========================================================
def liste_des_taches_template_view(request, slug):

    # Projet
    projet = get_object_or_404(ProjetEtude, slug=slug)

    # Liste des tâches
    taches = Tache.objects.filter(projet=projet).select_related('assigne_a', 'cree_par', 'canevas').order_by('date_debut', 'date_fin')

    context = {
        "projet": projet,
        "taches": taches,
        "total_taches": taches.count(),
        "taches_terminees": taches.filter(statut=Tache.Statut.TERMINE).count(),
        "taches_en_cours": taches.filter(statut=Tache.Statut.EN_COURS).count(),
        "taches_retard": taches.filter(statut=Tache.Statut.RETARD).count(),
    }
    return render(request,"back/projet_etude/liste_taches.html",context)

# =========================================================
# MODIFIER UNE TACHE
# =========================================================
def modal_modification_tache(request, slug):

    # Tâche
    tache = get_object_or_404(Tache, slug=slug)

    # Projet
    projet = tache.projet

    # Formulaire
    tache_form = TacheForm(instance=tache, projet=projet)

    if request.method == "POST":
        tache_form = TacheForm(request.POST, request.FILES, instance=tache, projet=projet)

        if tache_form.is_valid():

            tache = tache_form.save(commit=False)

            # =========================================
            # SECURITE CANEVAS
            # =========================================
            if tache.canevas.projet != projet:

                messages.error(request, "Le canevas sélectionné est invalide.")

                return redirect(request.META.get('HTTP_REFERER'))

            tache.save()

            # =========================================
            # EMAIL MODIFICATION
            # =========================================
            if tache.assigne_a.email:

                sujet = ("Modification d'une tâche")

                message = f"""
                Bonjour {tache.assigne_a.full_name},

                Une tâche vous concernant a été modifiée.

                =====================================

                Projet :
                {projet.titre}

                Canevas :
                {tache.canevas.titre}

                Titre :
                {tache.titre}

                Description :
                {tache.description}

                Date début :
                {tache.date_debut}

                Date fin :
                {tache.date_fin}

                Progression :
                {tache.progression} %

                Statut :
                {tache.get_statut_display()}

                Priorité :
                {tache.get_priorite_display()}

                =====================================

                Veuillez consulter la plateforme.

                Cordialement,
                Portail Scientifique
                """

                send_mail(
                    sujet,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [tache.assigne_a.email],
                    fail_silently=True
                )

            messages.success(request, "Tâche modifiée avec succès.")

            return redirect('projets_detudes:etudiants_a_encadrer')

        else:

            print(tache_form.errors)

    context = {
        "tache_form": tache_form,
        "tache": tache,
        "projet": projet
    }
    return render(request, "back/modals_projet/modification_tache.html", context)

# Vue pour afficher la progression du projet d'etude
def progression_template_view(request):
    return render(request, "back/projet_etude/progression.html")

# Vue de demande de soutenance apres l'edition du memoire ou de la thèse
def modal_demande_soutenance(request):
    return render(request, "back/modals_projet/demande_soutenance.html")