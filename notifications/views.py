from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from notifications.models import Notification


@method_decorator(login_required, name='dispatch')
class NotificationTemplateView(TemplateView):
    template_name = 'back/notifications/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notifications = (
            Notification.objects.filter(user=self.request.user)
            .order_by('-created_at')
        )
        # Marquer comme lues à l'ouverture de la page
        notifications.filter(notif_statut=False).update(notif_statut=True)
        context['notifications'] = notifications
        return context
