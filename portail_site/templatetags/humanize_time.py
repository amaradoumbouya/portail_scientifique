import ast

from django import template

register = template.Library()


@register.filter
def split_keywords(value):
    """Transforme les mots-clés (liste Python stockée en texte ou chaîne
    séparée par des virgules/points-virgules) en une liste propre."""
    if not value:
        return []

    if isinstance(value, (list, tuple)):
        items = value
    else:
        text = str(value).strip()
        items = None
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = ast.literal_eval(text)
                if isinstance(parsed, (list, tuple)):
                    items = list(parsed)
            except (ValueError, SyntaxError):
                items = None
        if items is None:
            text = text.strip("[]")
            separator = ";" if ";" in text else ","
            items = text.split(separator)

    cleaned = []
    for item in items:
        mot = str(item).strip().strip("'\"").strip()
        if mot:
            cleaned.append(mot)
    return cleaned

@register.filter
def humanize_seconds(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return ""
    days, remainder = divmod(value, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}j")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)