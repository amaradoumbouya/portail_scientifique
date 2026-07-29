from django.conf import settings
from django.shortcuts import redirect
from django.urls import Resolver404, resolve, reverse


class ScreenLockMiddleware:
    """Redirige vers l'écran de déverrouillage si la session est verrouillée."""

    ALLOWED_URL_NAMES = {
        'accounts:deverrouiller',
        'accounts:verrouiller',
        'portail_site:deconnexion',
        'portail_site:connexion',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            getattr(request, 'user', None)
            and request.user.is_authenticated
            and request.session.get('screen_locked')
        ):
            path = request.path_info
            static_url = getattr(settings, 'STATIC_URL', '/static/') or '/static/'
            media_url = getattr(settings, 'MEDIA_URL', '/media/') or '/media/'

            if not (path.startswith(static_url) or path.startswith(media_url)):
                try:
                    match = resolve(path)
                    url_name = (
                        f'{match.namespace}:{match.url_name}'
                        if match.namespace
                        else match.url_name
                    )
                except Resolver404:
                    url_name = None

                if url_name not in self.ALLOWED_URL_NAMES:
                    return redirect(reverse('accounts:deverrouiller'))

        return self.get_response(request)
