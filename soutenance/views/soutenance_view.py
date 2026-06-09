from django.shortcuts import (render, redirect, get_object_or_404)
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from soutenance.forms.demande_soutenance_forms import (DemandeSoutenanceForm)
from soutenance.models.jury import JuryMember
from projets_detudes.models.projet import ProjetEtude
from projets_detudes.models.participant import Participant
from soutenance.models.soutenance import (DemandeSoutenance, Soutenance)
from soutenance.models.deliberation_soutenance import DeliberationSoutenance
from soutenance.forms.deliberation_soutenance_forms import DeliberationSoutenanceForm
from soutenance.utils import calculer_mention
from soutenance.models.jury import JuryMember
from soutenance.forms.soutenance_forms import (SoutenanceForm)
from accounts.models import CustumerUser
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.db.models import Q
from django.db.models import Count
from django.utils import timezone



def modal_soutenance(request):
    # ==========================================
    # SUPERUSER : VOIT TOUTES LES DEMANDES
    # ==========================================
    if request.user.is_superuser:

        demandes = (DemandeSoutenance.objects.select_related(
            'projet',
            'candidat',
            'candidat__user',
            'candidat__institution',
            'responsable_institution').order_by('-date_demande'))

    # ==========================================
    # RESPONSABLE D'INSTITUTION :
    # VOIT UNIQUEMENT LES DEMANDES
    # QUI LUI SONT ADRESSÉES
    # ==========================================
    else:

        demandes = (DemandeSoutenance.objects.filter(responsable_institution=request.user).select_related(
            'projet',
            'candidat',
            'candidat__user',
            'candidat__institution',
            'responsable_institution'
        ).order_by('-date_demande'))

    # ==========================================
    # STATISTIQUES
    # ==========================================
    total_demandes = demandes.count()
    demandes_en_attente = (demandes.filter(statut="En attente").count())
    demandes_validees = (demandes.filter(directeur_validation=True, responsable_validation=True).count())
    demandes_rejetees = (demandes.filter(statut="Rejetée").count())

    context = {
        "demandes": demandes,
        "total_demandes": total_demandes,
        "demandes_en_attente": demandes_en_attente,
        "demandes_validees": demandes_validees,
        "demandes_rejetees": demandes_rejetees,
    }
    return render(request, "back/soutenance/index_demande_soutenance.html", context)

def modal_voir_plus_soutenance(request, slug):
    
    demande = get_object_or_404(DemandeSoutenance,slug=slug)

    context = {

        "demande": demande,

        "projet": demande.projet,

        "candidat": demande.candidat,

        "responsable": demande.responsable_institution,

    }
    return render(request, "back/modals_soutenance/voir_plus_soutenance.html", context)

@transaction.atomic
def modal_planifier_soutenance(request, slug):

    demande = get_object_or_404(DemandeSoutenance.objects.select_related("projet", "candidat", "responsable_institution"), slug=slug)

    form_soutenance = SoutenanceForm()

    if request.method == "POST":

        form_soutenance = SoutenanceForm(request.POST)

        print("Erreurs soutenance :", form_soutenance.errors)

        if form_soutenance.is_valid():

            try:

                current_site = get_current_site(request)

                # ==========================================
                # VERIFICATION SOUTENANCE EXISTANTE
                # ==========================================
                soutenance_existante = Soutenance.objects.filter(projet=demande.projet).first()

                if soutenance_existante:

                    messages.warning(request, f"Une soutenance est déjà planifiée pour le projet '{demande.projet.titre}'.")

                    return redirect("soutenance:modal_soutenance")

                # ==========================================
                # CREATION DE LA SOUTENANCE
                # ==========================================
                soutenance = form_soutenance.save(commit=False)

                soutenance.projet = demande.projet

                soutenance.responsable_planification = request.user

                soutenance.statut = "Planifiée"

                soutenance.save()

                print("Soutenance créée")

                # ==========================================
                # TRAITEMENT DES MEMBRES DU JURY
                # ==========================================
                i = 0

                while True:

                    nom = request.POST.get(f"juries[{i}][nom]")

                    if not nom:
                        break

                    prenoms = request.POST.get(f"juries[{i}][prenoms]")

                    email = request.POST.get(f"juries[{i}][email]")

                    tel = request.POST.get(f"juries[{i}][tel]")

                    role = request.POST.get(f"juries[{i}][role]")

                    if not email:

                        i += 1

                        continue

                    # ==========================================
                    # RECHERCHE UTILISATEUR
                    # ==========================================
                    jury_user = (CustumerUser.objects.filter(Q(email=email) | Q(tel=tel)).first())

                    # ==========================================
                    # UTILISATEUR INEXISTANT
                    # ==========================================
                    if not jury_user:

                        password_par_defaut = (get_random_string(10))

                        jury_user = (CustumerUser.objects.create_user(nom=nom, prenoms=prenoms, email=email, tel=tel, password=password_par_defaut))

                        # ==========================================
                        # PROFIL ENSEIGNANT
                        # ==========================================
                        jury_user.profile.role = ("enseignant")

                        jury_user.profile.save()

                        # ==========================================
                        # AJOUT MEMBRE JURY
                        # ==========================================
                        JuryMember.objects.create(soutenance=soutenance, enseignant=jury_user, created_by=request.user, role=role)

                        # ==========================================
                        # EMAIL ACTIVATION
                        # ==========================================
                        uid = (urlsafe_base64_encode(force_bytes(jury_user.pk)))

                        token = (default_token_generator.make_token(jury_user))

                        activation_link = reverse("portail_site:activation", kwargs={"uidb64": uid, "token": token})

                        activation_url = (f"http://{current_site.domain}" f"{activation_link}")

                        mail_subject = ("Invitation à participer à un jury de soutenance")

                        html_message = f"""
                        Bonjour {jury_user.full_name},

                        Vous avez été désigné comme  {role} dans un jury de soutenance.

                        Projet : {demande.projet.titre}

                        Vos identifiants :

                        Email : {email}

                        Mot de passe : {password_par_defaut}

                        Activez votre compte : {activation_url}
                        """

                        send_mail(
                            mail_subject,
                            "",
                            settings.DEFAULT_FROM_EMAIL,
                            [jury_user.email],
                            html_message=html_message,
                            fail_silently=False
                        )

                    # ==========================================
                    # UTILISATEUR EXISTANT
                    # ==========================================
                    else:

                        JuryMember.objects.get_or_create( soutenance=soutenance, enseignant=jury_user, role=role, defaults={"created_by": request.user})

                        login_url = (f"http://{current_site.domain}/connexion/")

                        mail_subject = ("Désignation comme membre du jury")

                        html_message = f"""
                        Bonjour {jury_user.full_name},

                        Vous avez été désigné comme {role} dans un jury de soutenance.

                        Projet : {demande.projet.titre}

                        Date : {soutenance.date}

                        Heure : {soutenance.heure}

                        Lieu : {soutenance.lieu}

                        Connectez-vous : {login_url}
                        """

                        send_mail(
                            mail_subject,
                            "",
                            settings.DEFAULT_FROM_EMAIL,
                            [jury_user.email],
                            html_message=html_message,
                            fail_silently=False
                        )

                    i += 1

                print("Membres du jury enregistrés")

                # ==========================================
                # MISE A JOUR DEMANDE
                # ==========================================
                demande.statut = "Acceptée"

                demande.save()

                # ==========================================
                # SUCCESS
                # ==========================================
                messages.success(request, "Soutenance planifiée avec succès.")

                return redirect("soutenance:modal_soutenance")

            except Exception as e:

                print("ERREUR PLANIFICATION :", str(e))

                messages.error(request, f"Erreur : {str(e)}")

    return render(request, "back/modals_soutenance/planifier_soutenance.html", {"form_soutenance": form_soutenance, "demande": demande})

def modal_ajouter_membres_jury(request, slug):
    return render(request, "back/modals_soutenance/ajout_membre_jury.html")

def modal_liste_membres_jury(request, slug):

    demande = get_object_or_404(DemandeSoutenance.objects.select_related("projet", "candidat", "responsable_institution"), slug=slug)

    soutenance = get_object_or_404(Soutenance.objects.select_related("projet", "responsable_planification"), projet=demande.projet)

    jury = JuryMember.objects.filter(soutenance=soutenance).select_related("created_by", "enseignant")

    participant_directeur = Participant.objects.filter(projet=demande.projet, role=Participant.Role.DIRECTEUR).select_related("user").first()

    context = {

        "demande": demande,

        "soutenance": soutenance,

        "projet": demande.projet,

        "candidat": demande.candidat,

        "directeur": participant_directeur.user if participant_directeur else None,

        "responsable": demande.responsable_institution,

        "membres_jury": jury,

        "presidents": jury.filter(role=JuryMember.RoleJury.PRESIDENT),

        "rapporteurs": jury.filter(role=JuryMember.RoleJury.RAPPORTEUR),

        "examinateurs": jury.filter(role=JuryMember.RoleJury.EXAMINATEUR),

        "membres_simples": jury.filter(role__in=[JuryMember.RoleJury.DIRECTEUR, JuryMember.RoleJury.CO_DIRECTEUR]),
    }
    return render(request, "back/modals_soutenance/liste_membres_jury.html", context)

def liste_soutenances(request):

    # ==========================================
    # ADMINISTRATEUR
    # ==========================================
    if request.user.is_superuser:

        participants = (Participant.objects.filter(
                role=Participant.Role.DIRECTEUR
            ).select_related(
                'projet',
                'projet__candidate',
                'projet__candidate__user',
                'projet__candidate__institution'
            ).order_by('-date_ajout')
        )

    # ==========================================
    # DIRECTEUR
    # ==========================================
    else:

        participants = (
            Participant.objects.filter(
                user=request.user,
                role=Participant.Role.DIRECTEUR
            ).select_related(
                'projet',
                'projet__candidate',
                'projet__candidate__user',
                'projet__candidate__institution'
            ).order_by('-date_ajout'))

    # ==========================================
    # STATISTIQUES
    # ==========================================

    projets_ids = participants.values_list('projet_id', flat=True)

    demandes_soutenance = (DemandeSoutenance.objects.filter(projet_id__in=projets_ids).count())

    demandes_validees = (DemandeSoutenance.objects.filter(
            projet_id__in=projets_ids,
            directeur_validation=True,
            responsable_validation=True).count())

    soutenances_prevues = (Soutenance.objects.filter(projet_id__in=projets_ids).count())

    soutenances_effectuees = (Soutenance.objects.filter(projet_id__in=projets_ids, statut="effectuee").count())

    context = {

        "participants": participants,

        "demandes_soutenance": demandes_soutenance,

        "demandes_validees": demandes_validees,

        "soutenances_prevues": soutenances_prevues,

        "soutenances_effectuees": soutenances_effectuees,

    }

    return render(request, "back/soutenance/index_demande_soutenance.html", context)

def modal_demande_soutenance(request, slug):

    projet = get_object_or_404(ProjetEtude, slug=slug)

    form = DemandeSoutenanceForm()

    if request.method == "POST":

        form = DemandeSoutenanceForm(request.POST)

        if form.is_valid():

            # ==================================
            # VERIFICATION DEMANDE EXISTANTE
            # ==================================

            demande_existante = (
                DemandeSoutenance.objects.filter(projet=projet).exclude(statut="Rejetée").first())

            if demande_existante:

                messages.warning(request,
                    f"Une demande de soutenance existe déjà pour ce projet "
                    f"(Statut : {demande_existante.statut})."
                )

                return redirect('projets_detudes:etudiants_a_encadrer')

            # ==================================
            # CREATION DE LA DEMANDE
            # ==================================

            demande = form.save(commit=False)

            demande.projet = projet

            demande.candidat = projet.candidate

            demande.responsable_institution = request.user

            demande.save()

            # ==================================
            # RECUPERATION DES DIRECTEURS
            # ==================================

            directeurs = (
                Participant.objects.filter(projet=projet, role__in=[Participant.Role.DIRECTEUR, Participant.Role.CO_DIRECTEUR]).select_related("user"))

            destinataires = []

            for directeur in directeurs:

                if directeur.user.email:

                    destinataires.append(directeur.user.email)

            if (demande.responsable_institution and demande.responsable_institution.email):

                destinataires.append(demande.responsable_institution.email)

            # Suppression des doublons
            destinataires = list(set(destinataires))

            # ==================================
            # ENVOI EMAIL
            # ==================================

            if destinataires:

                send_mail(

                    subject="Nouvelle demande de soutenance",

                    message=f"""
                    Bonjour,

                    Une nouvelle demande de soutenance vient d'être soumise.

                    Projet : {projet.titre}

                    Étudiant : {projet.candidate}

                    Date de la demande : {demande.date_demande.strftime('%d/%m/%Y %H:%M')}

                    Statut : {demande.statut}

                    Observation :
                    {demande.observations_directeur}

                    Veuillez vous connecter à la plateforme pour traiter cette demande.

                    Portail Scientifique
                    """,

                    from_email=settings.DEFAULT_FROM_EMAIL,

                    recipient_list=destinataires,

                    fail_silently=True

                )

            # ==================================
            # MESSAGE SUCCES
            # ==================================

            messages.success(request, "Votre demande de soutenance a été envoyée avec succès.")

            return redirect('projets_detudes:etudiants_a_encadrer')

        else:

            messages.error(request, "Veuillez corriger les erreurs du formulaire.")

    context = {

        "form": form,

        "projet": projet,
    }
    return render(request, "back/modals_projet/demande_soutenance.html", context)

def modal_modification_demande_soutenance(request, slug):
    
    demande = get_object_or_404(DemandeSoutenance, slug=slug)

    form = DemandeSoutenanceForm(instance=demande)

    if request.method == "POST":

        form = DemandeSoutenanceForm(

            request.POST,

            instance=demande

        )

        if form.is_valid():

            demande = form.save()

            # ==================================
            # DIRECTEURS
            # ==================================

            directeurs = Participant.objects.filter(

                projet=demande.projet,

                role__in=[

                    Participant.Role.DIRECTEUR,

                    Participant.Role.CO_DIRECTEUR

                ]

            ).select_related('user')

            destinataires = []

            for directeur in directeurs:

                if directeur.user.email:

                    destinataires.append(directeur.user.email)

            if demande.responsable_institution.email:

                destinataires.append(demande.responsable_institution.email)

            if destinataires:

                send_mail(

                    subject=("Modification d'une demande de soutenance"),

                    message=f"""

                    Bonjour,

                    Une demande de soutenance
                    a été modifiée.

                    Projet :
                    {demande.projet.titre}

                    Observation :
                    {demande.observations_directeur}

                    Statut :
                    {demande.statut}

                    Veuillez consulter
                    la plateforme.

                    Portail Scientifique

                    """,

                    from_email=settings.DEFAULT_FROM_EMAIL,

                    recipient_list=destinataires,

                    fail_silently=True

                )

            messages.success(request, "Demande modifiée avec succès.")

            return redirect('projets_detudes:etudiants_a_encadrer')
        
    context = {
        "form": form,
        "demande": demande
    }
    return render(request, "back/modals_projet/modification_demande_soutenance.html", context)

def index_soutenance(request):

    if request.user.is_superuser:

        soutenances = (Soutenance.objects.select_related(
                "projet",
                "projet__candidate",
                "projet__candidate__user",
                "responsable_planification"
            ).order_by("-created_at"))

    else:

        soutenances = (Soutenance.objects.filter(responsable_planification=request.user
            ).select_related(
                "projet",
                "projet__candidate",
                "projet__candidate__user",
                "responsable_planification"
            ).order_by("-created_at"))

    total_soutenances = soutenances.count()

    soutenances_planifiees = (soutenances.filter(statut="Planifiée").count())

    soutenances_realisees = (soutenances.filter(statut="Terminée").count())

    soutenances_annulees = (soutenances.filter(statut="Annulée").count())

    context = {

        "soutenances": soutenances,

        "total_soutenances": total_soutenances,

        "soutenances_planifiees": soutenances_planifiees,

        "soutenances_realisees": soutenances_realisees,

        "soutenances_annulees": soutenances_annulees,

    }
    return render(request, "back/soutenance/index_soutenance.html", context)

def ajouter_deliberation(request, slug):

    soutenance = get_object_or_404(Soutenance, slug=slug)

    # Vérifie si une délibération existe déjà
    if hasattr(soutenance, "deliberation"):

        messages.warning(request, "Une délibération existe déjà pour cette soutenance.")

        return redirect("detail_deliberation", pk=soutenance.deliberation.pk)

    if request.method == "POST":

        deliberation_form = DeliberationSoutenanceForm(request.POST)

        if deliberation_form.is_valid():

            deliberation = deliberation_form.save(commit=False)

            deliberation.soutenance = soutenance

            deliberation.saisi_par = request.user

            deliberation.mention = calculer_mention(float(deliberation.note_finale))

            deliberation.save()

            messages.success(request, "La délibération a été enregistrée avec succès.")

            # return redirect("detail_deliberation", slug=deliberation.slug)

        else:

            messages.error(request, "Veuillez corriger les erreurs du formulaire.")

    else:

        deliberation_form = DeliberationSoutenanceForm()

    context = {

        "soutenance": soutenance,

        "projet": soutenance.projet,

        # "demande": soutenance.demande_soutenance,

        "deliberation_form": deliberation_form,

    }
    return render(request, "back/modals_soutenance/ajout_deliberation.html", context)

def liste_deliberations(request):

    deliberations = (

        DeliberationSoutenance.objects

        .select_related(
            "soutenance",

            "soutenance__projet",

            "saisi_par"
        )

        .order_by("-date_deliberation"))

    context = {

        "deliberations": deliberations

    }
    return render(request, "deliberations/liste.html", context)

def voir_plus_deliberation(request, slug):

    soutenance = get_object_or_404(Soutenance.objects.select_related("projet"),slug=slug)

    deliberation = get_object_or_404(DeliberationSoutenance.objects.select_related(

            "soutenance",

            "soutenance__projet",

            "saisi_par"

        ),soutenance=soutenance)
    
    return render(request, "back/modals_soutenance/voir_plus_deliberation.html", {"deliberation": deliberation})

def modifier_deliberation(request, pk):

    deliberation = get_object_or_404(DeliberationSoutenance, pk=pk)

    if deliberation.resultat_publie:

        messages.error(request, "Impossible de modifier une délibération publiée.")

        return redirect("detail_deliberation", deliberation.pk)

    if request.method == "POST":

        deliberation.note_finale = request.POST.get("note_finale")

        deliberation.decision = request.POST.get("decision")

        deliberation.observations = request.POST.get("observations")

        deliberation.mention = calculer_mention(float(deliberation.note_finale))

        deliberation.save()

        messages.success(request, "Délibération modifiée.")

        return redirect("detail_deliberation", deliberation.pk)

    return render(request, "deliberations/modifier.html", {"deliberation": deliberation})

def publier_resultat(request, pk):

    deliberation = get_object_or_404(DeliberationSoutenance, pk=pk)

    if not deliberation.resultat_publie:

        deliberation.resultat_publie = True

        deliberation.date_publication = (timezone.now())

        deliberation.save()

        messages.success(request, "Résultat publié avec succès.")

    return redirect("detail_deliberation", deliberation.pk)