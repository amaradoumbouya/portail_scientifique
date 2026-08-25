from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import ExtractYear

from institutions.models import Institution
from portail_site.views.dashboard import count_publications_indexees
from publications.models.publication import Publication

User = get_user_model()

PUBLIEE = Q(statut_publication=True)


def _publications_publiees():
    return Publication.objects.filter(PUBLIEE)


def indicateurs():
    qs = _publications_publiees()
    return {
        "nb_publications": qs.count(),
        "nb_articles": qs.filter(type_publication="article").count(),
        "nb_colloques": qs.filter(type_publication="colloque").count(),
        "nb_memoires": qs.filter(type_publication="memoire").count(),
        "nb_theses": qs.filter(type_publication="these").count(),
        "nb_indexees": count_publications_indexees(qs),
        "nb_domaines": (
            qs.exclude(domaine__isnull=True)
            .exclude(domaine="")
            .values("domaine")
            .distinct()
            .count()
        ),
        "nb_institutions": Institution.objects.count(),
        "nb_auteurs": (
            User.objects.filter(publicationauteur__publication__statut_publication=True)
            .distinct()
            .count()
        ),
    }


def par_type():
    labels = dict(Publication.TypePublication.choices)
    rows = []
    for item in (
        _publications_publiees()
        .values("type_publication")
        .annotate(n=Count("id"))
        .order_by("-n")
    ):
        code = item["type_publication"] or "autre"
        rows.append({
            "code": code,
            "libelle": labels.get(code, code or "Non renseigné"),
            "n": item["n"],
        })
    return rows


def par_domaine():
    rows = []
    for item in (
        _publications_publiees()
        .values("domaine")
        .annotate(n=Count("id"))
        .order_by("-n")
    ):
        rows.append({
            "libelle": (item["domaine"] or "").strip() or "Non classé",
            "n": item["n"],
        })
    fusion = {}
    for row in rows:
        fusion[row["libelle"]] = fusion.get(row["libelle"], 0) + row["n"]
    return [
        {"libelle": libelle, "n": n}
        for libelle, n in sorted(fusion.items(), key=lambda x: (-x[1], x[0]))
    ]


def par_annee():
    rows = []
    for item in (
        _publications_publiees()
        .annotate(annee=ExtractYear("date_ajout_systeme"))
        .values("annee")
        .annotate(n=Count("id"))
        .order_by("annee")
    ):
        if item["annee"]:
            rows.append({"annee": item["annee"], "n": item["n"]})
    return rows


def par_institution():
    return list(
        Institution.objects.annotate(
            nb_publications=Count(
                "userprofile__user__publicationauteur__publication",
                filter=Q(
                    userprofile__user__publicationauteur__publication__statut_publication=True
                ),
                distinct=True,
            ),
            nb_auteurs=Count(
                "userprofile__user",
                filter=Q(
                    userprofile__user__publicationauteur__publication__statut_publication=True
                ),
                distinct=True,
            ),
        )
        .filter(nb_publications__gt=0)
        .order_by("-nb_publications", "nom_institution")
    )


def par_auteur(limit=None):
    qs = (
        User.objects.filter(publicationauteur__publication__statut_publication=True)
        .select_related("profile", "profile__institution")
        .annotate(
            nb_publications=Count(
                "publicationauteur__publication",
                filter=Q(publicationauteur__publication__statut_publication=True),
                distinct=True,
            )
        )
        .filter(nb_publications__gt=0)
        .order_by("-nb_publications", "nom", "prenoms")
    )
    if limit:
        qs = qs[:limit]
    return list(qs)
