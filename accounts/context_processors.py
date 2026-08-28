from django.conf import settings


def session_idle(request):
    return {
        "SESSION_IDLE_TIMEOUT": int(getattr(settings, "SESSION_IDLE_TIMEOUT", 30 * 60)),
    }
