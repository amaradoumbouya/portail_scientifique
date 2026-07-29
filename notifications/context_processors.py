from notifications.models import Notification


def topbar_notifications(request):
    """Notifications de l'utilisateur connecté pour la barre supérieure."""
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {
            'topbar_notifications': [],
            'topbar_notifications_unread': 0,
        }

    qs = Notification.objects.filter(user=request.user).order_by('-created_at')
    return {
        'topbar_notifications': qs[:5],
        'topbar_notifications_unread': qs.filter(notif_statut=False).count(),
    }
