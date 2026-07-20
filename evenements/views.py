from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.core.mail import send_mail
from django.conf import settings
from evenements.models import Evenement, InscriptionEvenement
from evenements.forms import EvenementForm, InscriptionEvenementForm


def _is_admin(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'role', None) == 'admin')


def _envoyer_email_confirmation_inscription(inscription):
    evenement = inscription.evenement
    type_label = evenement.get_type_evenement_display()
    date_label = evenement.date_evenement.strftime('%d/%m/%Y à %H:%M')
    lieu_label = evenement.lieu or 'Lieu à confirmer'

    subject = f"Confirmation d'inscription – {evenement.titre}"
    message = f"""
Bonjour {inscription.prenoms} {inscription.nom},

Votre inscription à l'{type_label.lower()} suivant(e) a bien été enregistrée :

Titre : {evenement.titre}
Date  : {date_label}
Lieu  : {lieu_label}

Nous vous remercions pour votre participation.
Un rappel pourra vous être envoyé avant la date de l'événement.

Cordialement,
L'équipe Technique du CRICT
(Centre de Recherche en Informatique et Cyber-Technologie)
"""
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[inscription.email],
        fail_silently=False,
    )


@login_required
def evenements_index(request):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Accès réservé à l'administrateur.")

    evenements = Evenement.objects.order_by('-date_evenement')
    return render(request, 'back/evenements/index.html', {'evenements': evenements})


@login_required
def inscriptions_index(request, slug=None):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Accès réservé à l'administrateur.")

    evenement = None
    inscriptions = InscriptionEvenement.objects.select_related('evenement').order_by('-created_at')

    if slug:
        evenement = get_object_or_404(Evenement, slug=slug)
        inscriptions = inscriptions.filter(evenement=evenement)

    return render(
        request,
        'back/evenements/inscriptions.html',
        {
            'inscriptions': inscriptions,
            'evenement': evenement,
            'evenements': Evenement.objects.order_by('-date_evenement'),
        },
    )


@login_required
def modal_evenement(request, slug=None):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Accès réservé à l'administrateur.")

    evenement = get_object_or_404(Evenement, slug=slug) if slug else None

    if request.method == 'POST':
        form = EvenementForm(request.POST, request.FILES, instance=evenement)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Événement modifié avec succès." if evenement else "Événement ajouté avec succès.",
            )
            return redirect('evenements:index')

        for field, errors in form.errors.items():
            for error in errors:
                label = form.fields[field].label if field in form.fields else field
                messages.error(request, f"{label} : {error}")
        return redirect('evenements:index')

    form = EvenementForm(instance=evenement)
    return render(
        request,
        'back/modals_evenements/evenement.html',
        {'form': form, 'evenement': evenement},
    )


@login_required
@require_POST
def update_evenement_state(request):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Accès réservé à l'administrateur.")

    evenement = get_object_or_404(Evenement, id=request.POST.get('evenement_id'))
    evenement.is_actif = not evenement.is_actif
    evenement.save()
    return redirect('evenements:index')


@login_required
@require_POST
def delete_evenement(request, slug):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Accès réservé à l'administrateur.")

    evenement = get_object_or_404(Evenement, slug=slug)
    evenement.delete()
    messages.success(request, "Événement supprimé avec succès.")
    return redirect('evenements:index')


def detail_evenement(request, slug):
    evenement = get_object_or_404(Evenement, slug=slug, is_actif=True)
    return render(request, 'pages/detail_evenement.html', {'evenement': evenement})


@login_required
def detail_evenement_back(request, slug):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Accès réservé à l'administrateur.")

    evenement = get_object_or_404(Evenement, slug=slug)
    inscriptions = evenement.inscriptions.order_by('-created_at')
    return render(
        request,
        'back/evenements/detail.html',
        {
            'evenement': evenement,
            'inscriptions': inscriptions,
            'nb_inscriptions': inscriptions.count(),
        },
    )


def inscription_evenement(request, slug):
    evenement = get_object_or_404(Evenement, slug=slug, is_actif=True)

    if request.method == 'POST':
        form = InscriptionEvenementForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if InscriptionEvenement.objects.filter(evenement=evenement, email=email).exists():
                messages.warning(request, "Vous êtes déjà inscrit(e) à cet événement avec cet email.")
            else:
                inscription = form.save(commit=False)
                inscription.evenement = evenement
                inscription.save()

                try:
                    _envoyer_email_confirmation_inscription(inscription)
                    messages.success(
                        request,
                        f"Votre inscription à « {evenement.titre} » a bien été enregistrée. "
                        "Un email de confirmation vous a été envoyé.",
                    )
                except Exception:
                    messages.warning(
                        request,
                        f"Votre inscription à « {evenement.titre} » a bien été enregistrée, "
                        "mais l'email de confirmation n'a pas pu être envoyé.",
                    )

                return redirect('evenements:detail', slug=evenement.slug)
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'prenoms': getattr(request.user, 'prenoms', ''),
                'nom': getattr(request.user, 'nom', ''),
                'email': getattr(request.user, 'email', ''),
                'telephone': getattr(request.user, 'tel', ''),
            }
        form = InscriptionEvenementForm(initial=initial)

    return render(
        request,
        'pages/inscription_evenement.html',
        {'evenement': evenement, 'form': form},
    )
