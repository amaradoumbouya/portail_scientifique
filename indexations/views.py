from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from indexations.models import Indexation


@method_decorator(login_required, name='dispatch')
class IndexationTemplateView(ListView):
    model = Indexation
    template_name = 'back/indexations/index.html'
    context_object_name = 'indexations'
    ordering = ['-date_indexation']

    def get_queryset(self):
        return (
            Indexation.objects
            .select_related('publication')
            .order_by('-date_indexation')
        )
