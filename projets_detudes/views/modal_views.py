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
from django.core import signing
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from notifications.models import Notification
from projets_detudes.models.chat import MessageChat


INVITATION_SALT = 'invitation-participant-encadrant'
INVITATION_MAX_AGE = 60 * 60 * 24 * 30  # 30 jours


def _build_absolute_url(request, path):
    return f"{request.scheme}://{request.get_host()}{path}"


def _auteurs_du_projet(projet):
    return Participant.objects.filter(
        projet=projet,
        role__in=[Participant.Role.AUTEUR, Participant.Role.CO_AUTEUR],
    ).select_related('user')


def _notifier_utilisateur(user, objectif, detail, email_subject=None, email_body=None):
    """Notification interne (+ email optionnel) pour un utilisateur."""
    if not user:
        return
    Notification.objects.create(user=user, objectif=objectif, detail=detail)
    if email_subject and email_body and user.email:
        send_mail(
            email_subject,
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )


def _notifier_auteurs(projet, objectif, detail, email_subject=None, email_body_builder=None):
    """Notifie les auteurs / co-auteurs d'un projet (cloche + email)."""
    for participant in _auteurs_du_projet(projet):
        body = email_body_builder(participant.user) if email_body_builder else None
        _notifier_utilisateur(
            participant.user,
            objectif,
            detail,
            email_subject=email_subject,
            email_body=body,
        )


def _est_encadrant_du_projet(user, projet):
    return Participant.objects.filter(
        projet=projet,
        user=user,
        role__in=[
            Participant.Role.DIRECTEUR,
            Participant.Role.CO_DIRECTEUR,
            "Co-Directeur",
        ],
        has_accepted=Participant.Statut.ACCEPTE,
    ).exists()


def _make_invitation_token(participant):
    return signing.dumps(
        {'pid': participant.pk, 'uid': participant.user_id},
        salt=INVITATION_SALT,
    )


def _build_invitation_urls(request, participant):
    token = _make_invitation_token(participant)
    accept_path = reverse(
        'projets_detudes:reponse_invitation',
        kwargs={'token': token, 'action': Participant.Statut.ACCEPTE},
    )
    refuse_path = reverse(
        'projets_detudes:reponse_invitation',
        kwargs={'token': token, 'action': Participant.Statut.REFUSE},
    )
    return (
        _build_absolute_url(request, accept_path),
        _build_absolute_url(request, refuse_path),
    )


def reponse_invitation_participant(request, token, action):
    """
    Lien email pour qu'un encadrant accepte ou refuse l'invitation.
    action: 'accepte' | 'refuse'
    """
    if action not in (Participant.Statut.ACCEPTE, Participant.Statut.REFUSE):
        raise Http404("Action d'invitation invalide.")

    try:
        data = signing.loads(token, salt=INVITATION_SALT, max_age=INVITATION_MAX_AGE)
        participant = Participant.objects.select_related('user', 'projet').get(
            pk=data['pid'],
            user_id=data['uid'],
        )
    except (signing.BadSignature, signing.SignatureExpired, KeyError, Participant.DoesNotExist):
        return render(
            request,
            'pages/reponse_invitation.html',
            {
                'success': False,
                'message': (
                    "Ce lien d'invitation est invalide ou a expiré. "
                    "Veuillez contacter l'auteur du projet."
                ),
            },
        )

    if participant.has_accepted != Participant.Statut.EN_ATTENTE:
        deja = "acceptée" if participant.has_accepted == Participant.Statut.ACCEPTE else "refusée"
        return render(
            request,
            'pages/reponse_invitation.html',
            {
                'success': True,
                'deja_traite': True,
                'action': participant.has_accepted,
                'participant': participant,
                'message': f"Cette invitation a déjà été {deja}.",
            },
        )

    participant.has_accepted = action
    participant.save(update_fields=['has_accepted', 'updated_at'])
    projet = participant.projet
    projet.synchroniser_apres_reponse_invitation(participant, action)
    projet.refresh_from_db(fields=['statut', 'date_validation'])

    if action == Participant.Statut.ACCEPTE:
        message = (
            f"Vous avez accepté l'invitation en tant que {participant.role} "
            f"pour le projet « {participant.projet.titre} »."
        )
    else:
        message = (
            f"Vous avez refusé l'invitation en tant que {participant.role} "
            f"pour le projet « {participant.projet.titre} »."
        )

    return render(
        request,
        'pages/reponse_invitation.html',
        {
            'success': True,
            'deja_traite': False,
            'action': action,
            'participant': participant,
            'message': message,
        },
    )


def projet_etude_index(request):
    if not request.user.is_authenticated:
        return redirect('portail_site:dashboard')

    user = request.user

    # Superuser : tous les projets ; sinon projets où l'utilisateur participe ou est créateur
    projets_qs = (
        ProjetEtude.objects
        .select_related(
            'candidate',
            'candidate__user',
            'candidate__institution',
            'createur',
        )
        .prefetch_related('projet__user')
        .order_by('-date_soumission')
    )

    if not user.is_superuser:
        projets_qs = projets_qs.filter(
            Q(createur=user) | Q(projet__user=user)
        ).distinct()

    projets = list(projets_qs)
    for projet in projets:
        projet.rafraichir_statut_depuis_relations()

    return render(
        request,
        'back/projet_etude/index.html',
        {'projets': projets},
    )

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

                        # Ajouter user comme l'auteur principal (accepté automatiquement)
                        Participant.objects.get_or_create(
                            user=user,
                            projet=memoire,
                            defaults={
                                'role': Participant.Role.AUTEUR,
                                'has_accepted': Participant.Statut.ACCEPTE,
                            },
                        )

                        # Ajout des auteurs / co-auteurs (acceptés automatiquement)
                        i = 0
                        while True:
                            nom = request.POST.get(f"auteurs[{i}][nom]")
                            if not nom:
                                break
                            prenoms = request.POST.get(f"auteurs[{i}][prenoms]")
                            email = request.POST.get(f"auteurs[{i}][email]")
                            tel = request.POST.get(f"auteurs[{i}][tel]")
                            role = request.POST.get(f"auteurs[{i}][role]") or Participant.Role.CO_AUTEUR

                            participant_as_user = CustumerUser.objects.filter(email=email).first()

                            if not participant_as_user:
                                password_par_defaut = get_random_string(10)
                                participant_as_user = CustumerUser.objects.create_user(
                                    email=email, prenoms=prenoms, nom=nom, tel=tel, password=password_par_defaut
                                )

                                Participant.objects.get_or_create(
                                    user=participant_as_user,
                                    projet=memoire,
                                    defaults={
                                        'role': role,
                                        'has_accepted': Participant.Statut.ACCEPTE,
                                    },
                                )

                                current_site = get_current_site(request)
                                mail_subject = 'Activation de votre compte'
                                uid = urlsafe_base64_encode(force_bytes(participant_as_user.pk))
                                token = default_token_generator.make_token(participant_as_user)
                                activation_link = reverse('portail_site:activation', kwargs={'uidb64': uid, 'token': token})
                                activation_url = _build_absolute_url(request, activation_link)
                                message = render_to_string(
                                    'emails/activation_email_participant.html',
                                    {
                                        'user': participant_as_user,
                                        'role': role,
                                        'password': password_par_defaut,
                                        'activation_url': activation_url,
                                        'titre_projet': memoire.titre,
                                        'type_projet_label': 'Mémoire de master',
                                    },
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
                                Participant.objects.get_or_create(
                                    user=participant_as_user,
                                    projet=memoire,
                                    defaults={
                                        'role': role,
                                        'has_accepted': Participant.Statut.ACCEPTE,
                                    },
                                )

                                login_url = _build_absolute_url(request, '/connexion/')
                                mail_subject = 'Information de participation au projet de mémoire'
                                message = render_to_string(
                                    'emails/information_participant.html',
                                    {
                                        'user': participant_as_user,
                                        'login_url': login_url,
                                        'role': role,
                                        'titre_projet': memoire.titre,
                                        'type_projet_label': 'Mémoire de master',
                                    },
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

                        # Ajout des encadrants (statut en attente + liens accepter/refuser)
                        j = 0
                        while True:
                            nom = request.POST.get(f"encadreurs[{j}][nom]")
                            if not nom:
                                break
                            prenoms = request.POST.get(f"encadreurs[{j}][prenoms]")
                            email = request.POST.get(f"encadreurs[{j}][email]")
                            tel = request.POST.get(f"encadreurs[{j}][tel]")
                            role = request.POST.get(f"encadreurs[{j}][role]") or Participant.Role.DIRECTEUR

                            encadrant_as_user = CustumerUser.objects.filter(email=email).first()

                            if not encadrant_as_user:
                                password_par_defaut = get_random_string(10)
                                encadrant_as_user = CustumerUser.objects.create_user(
                                    email=email, prenoms=prenoms, nom=nom, tel=tel, password=password_par_defaut
                                )

                                encadrant_participant, _ = Participant.objects.get_or_create(
                                    user=encadrant_as_user,
                                    projet=memoire,
                                    defaults={
                                        'role': role,
                                        'has_accepted': Participant.Statut.EN_ATTENTE,
                                    },
                                )
                                accept_url, refuse_url = _build_invitation_urls(request, encadrant_participant)

                                uid = urlsafe_base64_encode(force_bytes(encadrant_as_user.pk))
                                token = default_token_generator.make_token(encadrant_as_user)
                                activation_link = reverse('portail_site:activation', kwargs={'uidb64': uid, 'token': token})
                                activation_url = _build_absolute_url(request, activation_link)
                                message = render_to_string(
                                    'emails/activation_email_participant.html',
                                    {
                                        'user': encadrant_as_user,
                                        'role': role,
                                        'password': password_par_defaut,
                                        'activation_url': activation_url,
                                        'titre_projet': memoire.titre,
                                        'type_projet_label': 'Mémoire de master',
                                        'accept_url': accept_url,
                                        'refuse_url': refuse_url,
                                    },
                                )
                                send_mail(
                                    'Invitation d\'encadrement — activez votre compte',
                                    '',
                                    settings.DEFAULT_FROM_EMAIL,
                                    [encadrant_as_user.email],
                                    html_message=message,
                                    fail_silently=False,
                                )

                            else:
                                encadrant_participant, _ = Participant.objects.get_or_create(
                                    user=encadrant_as_user,
                                    projet=memoire,
                                    defaults={
                                        'role': role,
                                        'has_accepted': Participant.Statut.EN_ATTENTE,
                                    },
                                )
                                accept_url, refuse_url = _build_invitation_urls(request, encadrant_participant)

                                login_url = _build_absolute_url(request, '/connexion/')
                                message = render_to_string(
                                    'emails/information_participant.html',
                                    {
                                        'user': encadrant_as_user,
                                        'role': role,
                                        'login_url': login_url,
                                        'titre_projet': memoire.titre,
                                        'type_projet_label': 'Mémoire de master',
                                        'accept_url': accept_url,
                                        'refuse_url': refuse_url,
                                    },
                                )
                                send_mail(
                                    'Invitation d\'encadrement — réponse requise',
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

                    return render(request, 'back/modals_projet/memoire.html', {"form_memoire": form_memoire, "error": str(e)})

            
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

                        # Ajouter user comme l'auteur principal (accepté automatiquement)
                        Participant.objects.get_or_create(
                            user=user,
                            projet=these,
                            defaults={
                                'role': Participant.Role.AUTEUR,
                                'has_accepted': Participant.Statut.ACCEPTE,
                            },
                        )

                        # Ajout des auteurs / co-auteurs (acceptés automatiquement)
                        i = 0
                        while True:
                            nom = request.POST.get(f"auteurs[{i}][nom]")
                            if not nom:
                                break
                            prenoms = request.POST.get(f"auteurs[{i}][prenoms]")
                            email = request.POST.get(f"auteurs[{i}][email]")
                            tel = request.POST.get(f"auteurs[{i}][tel]")
                            role = request.POST.get(f"auteurs[{i}][role]") or Participant.Role.CO_AUTEUR

                            participant_as_user = CustumerUser.objects.filter(email=email).first()

                            if not participant_as_user:
                                password_par_defaut = get_random_string(10)
                                participant_as_user = CustumerUser.objects.create_user(
                                    email=email, prenoms=prenoms, nom=nom, tel=tel, password=password_par_defaut
                                )

                                Participant.objects.get_or_create(
                                    user=participant_as_user,
                                    projet=these,
                                    defaults={
                                        'role': role,
                                        'has_accepted': Participant.Statut.ACCEPTE,
                                    },
                                )

                                uid = urlsafe_base64_encode(force_bytes(participant_as_user.pk))
                                token = default_token_generator.make_token(participant_as_user)
                                activation_link = reverse('portail_site:activation', kwargs={'uidb64': uid, 'token': token})
                                activation_url = _build_absolute_url(request, activation_link)
                                message = render_to_string(
                                    'emails/activation_email_participant.html',
                                    {
                                        'user': participant_as_user,
                                        'role': role,
                                        'password': password_par_defaut,
                                        'activation_url': activation_url,
                                        'titre_projet': these.titre,
                                        'type_projet_label': 'Thèse de doctorat',
                                    },
                                )
                                send_mail(
                                    'Activation de votre compte',
                                    '',
                                    settings.DEFAULT_FROM_EMAIL,
                                    [participant_as_user.email],
                                    html_message=message,
                                    fail_silently=False,
                                )

                            else:
                                Participant.objects.get_or_create(
                                    user=participant_as_user,
                                    projet=these,
                                    defaults={
                                        'role': role,
                                        'has_accepted': Participant.Statut.ACCEPTE,
                                    },
                                )

                                login_url = _build_absolute_url(request, '/connexion/')
                                message = render_to_string(
                                    'emails/information_participant.html',
                                    {
                                        'user': participant_as_user,
                                        'login_url': login_url,
                                        'role': role,
                                        'titre_projet': these.titre,
                                        'type_projet_label': 'Thèse de doctorat',
                                    },
                                )
                                send_mail(
                                    'Information de participation au projet de thèse',
                                    '',
                                    settings.DEFAULT_FROM_EMAIL,
                                    [participant_as_user.email],
                                    html_message=message,
                                    fail_silently=False,
                                )
                            i += 1

                        # Ajout des encadrants (statut en attente + liens accepter/refuser)
                        j = 0
                        while True:
                            nom = request.POST.get(f"encadreurs[{j}][nom]")
                            if not nom:
                                break
                            prenoms = request.POST.get(f"encadreurs[{j}][prenoms]")
                            email = request.POST.get(f"encadreurs[{j}][email]")
                            tel = request.POST.get(f"encadreurs[{j}][tel]")
                            role = request.POST.get(f"encadreurs[{j}][role]") or Participant.Role.DIRECTEUR

                            encadrant_as_user = CustumerUser.objects.filter(email=email).first()

                            if not encadrant_as_user:
                                password_par_defaut = get_random_string(10)
                                encadrant_as_user = CustumerUser.objects.create_user(
                                    email=email, prenoms=prenoms, nom=nom, tel=tel, password=password_par_defaut
                                )

                                encadrant_participant, _ = Participant.objects.get_or_create(
                                    user=encadrant_as_user,
                                    projet=these,
                                    defaults={
                                        'role': role,
                                        'has_accepted': Participant.Statut.EN_ATTENTE,
                                    },
                                )
                                accept_url, refuse_url = _build_invitation_urls(request, encadrant_participant)

                                uid = urlsafe_base64_encode(force_bytes(encadrant_as_user.pk))
                                token = default_token_generator.make_token(encadrant_as_user)
                                activation_link = reverse('portail_site:activation', kwargs={'uidb64': uid, 'token': token})
                                activation_url = _build_absolute_url(request, activation_link)
                                message = render_to_string(
                                    'emails/activation_email_participant.html',
                                    {
                                        'user': encadrant_as_user,
                                        'role': role,
                                        'password': password_par_defaut,
                                        'activation_url': activation_url,
                                        'titre_projet': these.titre,
                                        'type_projet_label': 'Thèse de doctorat',
                                        'accept_url': accept_url,
                                        'refuse_url': refuse_url,
                                    },
                                )
                                send_mail(
                                    'Invitation d\'encadrement — activez votre compte',
                                    '',
                                    settings.DEFAULT_FROM_EMAIL,
                                    [encadrant_as_user.email],
                                    html_message=message,
                                    fail_silently=False,
                                )

                            else:
                                encadrant_participant, _ = Participant.objects.get_or_create(
                                    user=encadrant_as_user,
                                    projet=these,
                                    defaults={
                                        'role': role,
                                        'has_accepted': Participant.Statut.EN_ATTENTE,
                                    },
                                )
                                accept_url, refuse_url = _build_invitation_urls(request, encadrant_participant)

                                login_url = _build_absolute_url(request, '/connexion/')
                                message = render_to_string(
                                    'emails/information_participant.html',
                                    {
                                        'user': encadrant_as_user,
                                        'role': role,
                                        'login_url': login_url,
                                        'titre_projet': these.titre,
                                        'type_projet_label': 'Thèse de doctorat',
                                        'accept_url': accept_url,
                                        'refuse_url': refuse_url,
                                    },
                                )
                                send_mail(
                                    'Invitation d\'encadrement — réponse requise',
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

        # Projets où l'utilisateur est encadrant et a accepté l'invitation
        participants = Participant.objects.filter(
            user=user,
            role__in=[
                Participant.Role.DIRECTEUR,
                Participant.Role.CO_DIRECTEUR,
                "Co-Directeur",
            ],
            has_accepted=Participant.Statut.ACCEPTE,
        ).select_related(
            "projet",
            "projet__candidate",
            "projet__candidate__user",
            "projet__candidate__institution",
        ).distinct()

        for participant in participants:
            participant.projet.rafraichir_statut_depuis_relations()

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
    
def _utilisateur_peut_gerer_projet(user, projet):
    if not user.is_authenticated:
        return False
    if user.is_superuser or projet.createur_id == user.id:
        return True
    return Participant.objects.filter(projet=projet, user=user).exists()


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


def modal_modifier_projet(request, slug):
    projet = get_object_or_404(ProjetEtude, slug=slug)

    if not _utilisateur_peut_gerer_projet(request.user, projet):
        messages.error(request, "Vous n'êtes pas autorisé à modifier ce projet.")
        return redirect('projets_detudes:index')

    if request.method == 'POST':
        form = ProjetForm(request.POST, instance=projet)
        if form.is_valid():
            form.save()
            messages.success(request, "Le projet a été modifié avec succès.")
            return redirect('projets_detudes:index')
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = ProjetForm(instance=projet)

    return render(
        request,
        'back/modals_projet/modifier_projet.html',
        {'form': form, 'projet': projet},
    )


def supprimer_projet(request, slug):
    if request.method != 'POST':
        return redirect('projets_detudes:index')

    projet = get_object_or_404(ProjetEtude, slug=slug)

    if not _utilisateur_peut_gerer_projet(request.user, projet):
        messages.error(request, "Vous n'êtes pas autorisé à supprimer ce projet.")
        return redirect('projets_detudes:index')

    titre = projet.titre
    projet.delete()
    messages.success(request, f"Le projet « {titre} » a été supprimé.")
    return redirect('projets_detudes:index')


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

            objectif = "Nouveau canevas disponible"
            detail = (
                f"Un canevas « {canevas.titre} » a été ajouté "
                f"pour le projet « {projet.titre} »."
            )
            _notifier_auteurs(
                projet,
                objectif,
                detail,
                email_subject="Ajout d'un nouveau canevas",
                email_body_builder=lambda user: (
                    f"Bonjour {user.full_name},\n\n"
                    f"Un nouveau canevas a été ajouté pour votre projet.\n\n"
                    f"Projet : {projet.titre}\n"
                    f"Canevas : {canevas.titre}\n"
                    f"Description : {canevas.description}\n\n"
                    f"Connectez-vous pour consulter le document.\n\n"
                    f"Cordialement,\nPortail Scientifique"
                ),
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

# Vue pour lister les canevas du projet (étudiant + encadrant)
def liste_canevas(request, slug):
    projet = get_object_or_404(
        ProjetEtude.objects.select_related('candidate', 'createur'),
        slug=slug,
    )
    if not _utilisateur_peut_gerer_projet(request.user, projet):
        messages.error(request, "Accès non autorisé à ce projet.")
        return redirect('projets_detudes:index')

    canevas = (
        CanevasProjet.objects.filter(projet=projet)
        .select_related('cree_par')
        .order_by('-created_at')
    )
    return render(
        request,
        "back/projet_etude/liste_canevas.html",
        {
            "projet": projet,
            "canevas_list": canevas,
            "est_encadrant": _est_encadrant_du_projet(request.user, projet),
        },
    )

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

            objectif = "Nouveau planning d'encadrement"
            detail = (
                f"Rendez-vous « {planning.titre} » le "
                f"{planning.date_rendez_vous} pour le projet « {projet.titre} »."
            )
            _notifier_auteurs(
                projet,
                objectif,
                detail,
                email_subject="Nouveau planning d'encadrement",
                email_body_builder=lambda user: (
                    f"Bonjour {user.full_name},\n\n"
                    f"Un nouveau planning a été ajouté pour votre projet.\n\n"
                    f"Projet : {projet.titre}\n"
                    f"Titre : {planning.titre}\n"
                    f"Description : {planning.description}\n"
                    f"Date : {planning.date_rendez_vous}\n"
                    f"Heure : {planning.heure_debut} - {planning.heure_fin}\n"
                    f"Lieu : {planning.lieu or 'Non défini'}\n"
                    f"Visio : {planning.lien_visio or 'Non défini'}\n\n"
                    f"Connectez-vous pour consulter les détails.\n\n"
                    f"Cordialement,\nPortail Scientifique"
                ),
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

    if not _utilisateur_peut_gerer_projet(request.user, projet):
        messages.error(request, "Accès non autorisé à ce projet.")
        return redirect('projets_detudes:index')

    planings = (
        PlanningEncadrement.objects.filter(projet=projet)
        .select_related('cree_par', 'canevas')
        .order_by('date_rendez_vous', 'heure_debut')
    )
    return render(
        request,
        "back/projet_etude/liste_planing.html",
        {
            "projet": projet,
            "planings": planings,
            "est_encadrant": _est_encadrant_du_projet(request.user, projet),
        },
    )

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

            objectif = "Nouvelle tâche assignée"
            detail = (
                f"La tâche « {tache.titre} » vous a été assignée "
                f"sur le projet « {projet.titre} » "
                f"(échéance : {tache.date_fin})."
            )
            _notifier_utilisateur(
                tache.assigne_a,
                objectif,
                detail,
                email_subject="Nouvelle tâche assignée",
                email_body=(
                    f"Bonjour {tache.assigne_a.full_name},\n\n"
                    f"Une nouvelle tâche vous a été assignée.\n\n"
                    f"Projet : {projet.titre}\n"
                    f"Canevas : {tache.canevas.titre}\n"
                    f"Titre : {tache.titre}\n"
                    f"Description : {tache.description}\n"
                    f"Début : {tache.date_debut}\n"
                    f"Fin : {tache.date_fin}\n"
                    f"Priorité : {tache.get_priorite_display()}\n\n"
                    f"Connectez-vous pour consulter la liste des tâches.\n\n"
                    f"Cordialement,\nPortail Scientifique"
                ),
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
    projet = get_object_or_404(ProjetEtude, slug=slug)

    if not _utilisateur_peut_gerer_projet(request.user, projet):
        messages.error(request, "Accès non autorisé à ce projet.")
        return redirect('projets_detudes:index')

    taches = (
        Tache.objects.filter(projet=projet)
        .select_related('assigne_a', 'cree_par', 'canevas')
        .order_by('date_debut', 'date_fin')
    )
    est_encadrant = _est_encadrant_du_projet(request.user, projet)

    context = {
        "projet": projet,
        "taches": taches,
        "total_taches": taches.count(),
        "taches_terminees": taches.filter(statut=Tache.Statut.TERMINE).count(),
        "taches_en_cours": taches.filter(statut=Tache.Statut.EN_COURS).count(),
        "taches_retard": taches.filter(statut=Tache.Statut.RETARD).count(),
        "est_encadrant": est_encadrant,
    }
    return render(request, "back/projet_etude/liste_taches.html", context)

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
def progression_template_view(request, slug):
    projet = get_object_or_404(ProjetEtude, slug=slug)

    if not _utilisateur_peut_gerer_projet(request.user, projet):
        messages.error(request, "Accès non autorisé à ce projet.")
        return redirect('projets_detudes:index')

    taches = Tache.objects.filter(projet=projet)
    total = taches.count()
    terminees = taches.filter(statut=Tache.Statut.TERMINE).count()
    en_cours = taches.filter(statut=Tache.Statut.EN_COURS).count()
    en_attente = taches.filter(statut=Tache.Statut.EN_ATTENTE).count()
    retard = taches.filter(statut=Tache.Statut.RETARD).count()
    progression_moyenne = 0
    if total:
        progression_moyenne = int(
            sum(t.progression or 0 for t in taches) / total
        )

    return render(
        request,
        "back/projet_etude/progression.html",
        {
            "projet": projet,
            "total_taches": total,
            "taches_terminees": terminees,
            "taches_en_cours": en_cours,
            "taches_en_attente": en_attente,
            "taches_retard": retard,
            "progression_moyenne": progression_moyenne,
            "est_encadrant": _est_encadrant_du_projet(request.user, projet),
            "nb_canevas": projet.canevas.count(),
            "nb_planings": projet.planings.count(),
        },
    )

# Vue de demande de soutenance apres l'edition du memoire ou de la thèse
def modal_demande_soutenance(request):
    return render(request, "back/modals_projet/demande_soutenance.html")
# =========================================================
# CHAT ETUDIANT <-> ENCADRANT
# =========================================================
def _encadrants_du_projet(projet):
    return Participant.objects.filter(
        projet=projet,
        role__in=[
            Participant.Role.DIRECTEUR,
            Participant.Role.CO_DIRECTEUR,
            'Co-Directeur',
        ],
        has_accepted=Participant.Statut.ACCEPTE,
    ).select_related('user')


def _notifier_destinataires_chat(projet, expediteur, apercu):
    est_encadrant = _est_encadrant_du_projet(expediteur, projet)
    objectif = 'Nouveau message sur le projet'
    detail = f'{expediteur.full_name} : {apercu}'

    if est_encadrant:
        destinataires = [p.user for p in _auteurs_du_projet(projet)]
        if projet.candidate_id and projet.candidate.user_id:
            destinataires.append(projet.candidate.user)
    else:
        destinataires = [p.user for p in _encadrants_du_projet(projet)]

    vus = set()
    for user in destinataires:
        if not user or user.id == expediteur.id or user.id in vus:
            continue
        vus.add(user.id)
        _notifier_utilisateur(user, objectif, detail)


def _serialize_message(msg, current_user):
    return {
        'id': msg.id,
        'contenu': msg.contenu,
        'auteur': msg.auteur.full_name,
        'auteur_id': msg.auteur_id,
        'est_moi': msg.auteur_id == current_user.id,
        'created_at': msg.created_at.strftime('%d/%m/%Y %H:%M'),
    }


def chat_projet(request, slug):
    if not request.user.is_authenticated:
        return redirect('portail_site:dashboard')

    projet = get_object_or_404(
        ProjetEtude.objects.select_related('candidate', 'candidate__user'),
        slug=slug,
    )

    if not _utilisateur_peut_gerer_projet(request.user, projet):
        messages.error(request, "Accès non autorisé à ce projet.")
        return redirect("projets_detudes:index")

    msgs = (
        MessageChat.objects.filter(projet=projet)
        .select_related("auteur")
        .order_by("created_at")
    )

    MessageChat.objects.filter(projet=projet).exclude(auteur=request.user).filter(
        lu=False
    ).update(lu=True)

    return render(
        request,
        "back/projet_etude/chat.html",
        {
            "projet": projet,
            "messages_chat": msgs,
            "est_encadrant": _est_encadrant_du_projet(request.user, projet),
        },
    )


@require_GET
def chat_messages_api(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Non authentifié"}, status=401)

    projet = get_object_or_404(ProjetEtude, slug=slug)
    if not _utilisateur_peut_gerer_projet(request.user, projet):
        return JsonResponse({"error": "Accès refusé"}, status=403)

    after_id = request.GET.get("after_id") or "0"
    try:
        after_id = int(after_id)
    except (TypeError, ValueError):
        after_id = 0

    qs = (
        MessageChat.objects.filter(projet=projet, id__gt=after_id)
        .select_related("auteur")
        .order_by("created_at")
    )
    data = [_serialize_message(m, request.user) for m in qs]

    if data:
        MessageChat.objects.filter(
            projet=projet, id__in=[m["id"] for m in data]
        ).exclude(auteur=request.user).update(lu=True)

    return JsonResponse({"messages": data})


@require_POST
def chat_envoyer_api(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Non authentifié"}, status=401)

    projet = get_object_or_404(
        ProjetEtude.objects.select_related("candidate", "candidate__user"),
        slug=slug,
    )
    if not _utilisateur_peut_gerer_projet(request.user, projet):
        return JsonResponse({"error": "Accès refusé"}, status=403)

    contenu = (request.POST.get('contenu') or '').strip()
    if not contenu:
        return JsonResponse({'error': 'Message vide'}, status=400)
    if len(contenu) > 4000:
        return JsonResponse({'error': 'Message trop long'}, status=400)

    msg = MessageChat.objects.create(
        projet=projet,
        auteur=request.user,
        contenu=contenu,
    )
    apercu = contenu if len(contenu) <= 80 else contenu[:77] + '...'
    _notifier_destinataires_chat(projet, request.user, apercu)

    return JsonResponse({'message': _serialize_message(msg, request.user)})
