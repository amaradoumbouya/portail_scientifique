from django.shortcuts import render, get_object_or_404
from publications.models.publication import Publication, PublicationLike, PublicationComment, PublicationDownload
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required



# La vue de like d'une publication
@require_POST
@login_required
def like_publication(request, pk):
    publication = get_object_or_404(Publication, pk=pk)
    like, created = PublicationLike.objects.get_or_create(publication=publication, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({
        'liked': liked,
        'like_count': publication.likes.count()
    })


# La vue de commentaire d'une publication
@require_POST
@login_required
def comment_publication(request, pk):
    publication = get_object_or_404(Publication, pk=pk)
    content = request.POST.get('content')
    comment = PublicationComment.objects.create(publication=publication, user=request.user, contenu=content)
    return JsonResponse({
        'user': request.user.full_name(),
        'content': comment.contenu,
        'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M')
    })

# La vue de téléchargement d'une publication
@require_POST
def download_publication(request, pk):
    publication = get_object_or_404(Publication, pk=pk)
    user = request.user if request.user.is_authenticated else None
    ip = request.META.get('REMOTE_ADDR')
    PublicationDownload.objects.create(publication=publication, user=user, ip_address=ip)
    return JsonResponse({'status': 'ok'})