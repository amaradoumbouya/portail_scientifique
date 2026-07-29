from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.core.mail import send_mass_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from actualites.models import Actualite
from actualites.forms import ActualiteForm
from projets_detudes.models.candidate import Candidate

User = get_user_model()

ROLES_A_NOTIFIER = [
    'enseignant',
    'enseignant chercheur',
    'responsable institution',
]


def _is_admin(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'role', None) == 'admin')


def _emails_destinataires_actualite():
    """Emails des étudiants, enseignants, enseignants-chercheurs et responsables d'institution."""
    emails_roles = User.objects.filter(
        is_active=True,
        profile__role__in=ROLES_A_NOTIFIER,
    ).exclude(email='').values_list('email', flat=True)

    emails_etudiants = Candidate.objects.filter(
        user__is_active=True,
    ).exclude(user__email='').values_list('user__email', flat=True)

    return sorted({email.strip().lower() for email in list(emails_roles) + list(emails_etudiants) if email})


def _envoyer_notification_publication_actualite(request, actualite):
    emails = _emails_destinataires_actualite()
    if not emails:
        return 0

    lien = request.build_absolute_uri(
        reverse('actualites:detail', kwargs={'slug': actualite.slug})
    )
    date_label = actualite.date_publication.strftime('%d/%m/%Y')
    subject = f"Nouvelle actualité scientifique – {actualite.titre}"
    message = f"""
Bonjour,

Une nouvelle actualité scientifique vient d'être publiée sur le Portail Scientifique :

Titre : {actualite.titre}
Date  : {date_label}

Résumé :
{actualite.resume}

Consulter l'actualité :
{lien}

Cordialement,
L'équipe Technique du CRICT
(Centre de Recherche en Informatique et Cyber-Technologie)
"""
    datatuple = [
        (subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        for email in emails
    ]
    return send_mass_mail(datatuple, fail_silently=False)


@login_required
def actualites_index(request):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Accès réservé à l'administrateur.")

    actualites = Actualite.objects.order_by('-date_publication', '-created_at')
    return render(request, 'back/actualites/index.html', {'actualites': actualites})


@login_required
def modal_actualite(request, slug=None):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Accès réservé à l'administrateur.")

    actualite = get_object_or_404(Actualite, slug=slug) if slug else None
    etait_actif = bool(actualite and actualite.is_actif)

    if request.method == 'POST':
        form = ActualiteForm(request.POST, request.FILES, instance=actualite)
        if form.is_valid():
            actualite_saved = form.save()
            vient_detre_publiee = actualite_saved.is_actif and not etait_actif

            if vient_detre_publiee:
                try:
                    nb = _envoyer_notification_publication_actualite(request, actualite_saved)
                    messages.success(
                        request,
                        f"Actualité publiée avec succès. Notification envoyée à {nb} destinataire(s).",
                    )
                except Exception:
                    messages.warning(
                        request,
                        "Actualité enregistrée, mais l'envoi des emails de notification a échoué.",
                    )
            else:
                messages.success(
                    request,
                    "Actualité modifiée avec succès." if actualite else "Actualité ajoutée avec succès.",
                )
            return redirect('actualites:index')

        for field, errors in form.errors.items():
            for error in errors:
                label = form.fields[field].label if field in form.fields else field
                messages.error(request, f"{label} : {error}")
        return redirect('actualites:index')

    form = ActualiteForm(instance=actualite)
    return render(
        request,
        'back/modals_actualites/actualite.html',
        {'form': form, 'actualite': actualite},
    )


@login_required
@require_POST
def update_actualite_state(request):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Accès réservé à l'administrateur.")

    actualite = get_object_or_404(Actualite, id=request.POST.get('actualite_id'))
    etait_actif = actualite.is_actif
    actualite.is_actif = not actualite.is_actif
    actualite.save()

    if actualite.is_actif and not etait_actif:
        try:
            nb = _envoyer_notification_publication_actualite(request, actualite)
            messages.success(
                request,
                f"Actualité activée. Notification envoyée à {nb} destinataire(s).",
            )
        except Exception:
            messages.warning(
                request,
                "Actualité activée, mais l'envoi des emails de notification a échoué.",
            )

    return redirect('actualites:index')


@login_required
@require_POST
def delete_actualite(request, slug):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Accès réservé à l'administrateur.")

    actualite = get_object_or_404(Actualite, slug=slug)
    actualite.delete()
    messages.success(request, "Actualité supprimée avec succès.")
    return redirect('actualites:index')


@login_required
def detail_actualite_back(request, slug):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Accès réservé à l'administrateur.")

    actualite = get_object_or_404(Actualite, slug=slug)
    return render(request, 'back/actualites/detail.html', {'actualite': actualite})


def detail_actualite(request, slug):
    actualite = get_object_or_404(Actualite, slug=slug, is_actif=True)
    return render(request, 'pages/detail_actualite.html', {'actualite': actualite})
