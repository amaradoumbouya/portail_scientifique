from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from actualites.models import Actualite
from actualites.forms import ActualiteForm


def _is_admin(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'role', None) == 'admin')


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

    if request.method == 'POST':
        form = ActualiteForm(request.POST, request.FILES, instance=actualite)
        if form.is_valid():
            form.save()
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
    actualite.is_actif = not actualite.is_actif
    actualite.save()
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
