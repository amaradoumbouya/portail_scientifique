from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import Resolver404, resolve, reverse
from django.utils import timezone


class SessionIdleTimeoutMiddleware:
    """Déconnecte l'utilisateur après une période d'inactivité (30 min par défaut)."""

    EXEMPT_URL_NAMES = {
        "portail_site:connexion",
        "portail_site:deconnexion",
        "portail_site:activation",
        "portail_site:inscription",
        "portail_site:inscription_institution",
        "portail_site:inscription_enseignant",
        "portail_site:inscription_etudiant",
        "admin:login",
        "admin:logout",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, "user", None) and request.user.is_authenticated:
            path = request.path_info or ""
            if not self._is_asset(path):
                url_name = self._url_name(path)
                if url_name not in self.EXEMPT_URL_NAMES:
                    timeout = int(getattr(settings, "SESSION_IDLE_TIMEOUT", 30 * 60))
                    now = timezone.now().timestamp()
                    last = request.session.get("last_activity")
                    if last is not None and (now - float(last)) > timeout:
                        logout(request)
                        login_url = reverse("portail_site:connexion")
                        return redirect(f"{login_url}?inactivite=1")
                    request.session["last_activity"] = now
                    request.session.modified = True

        return self.get_response(request)

    def _is_asset(self, path):
        for url in (
            getattr(settings, "STATIC_URL", "/static/"),
            getattr(settings, "MEDIA_URL", "/media/"),
        ):
            prefix = url or "/"
            if not prefix.startswith("/"):
                prefix = "/" + prefix
            if path.startswith(prefix):
                return True
        return False

    def _url_name(self, path):
        try:
            match = resolve(path)
        except Resolver404:
            return None
        if match.namespace:
            return f"{match.namespace}:{match.url_name}"
        return match.url_name
