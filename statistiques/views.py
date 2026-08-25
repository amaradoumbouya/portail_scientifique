from django.shortcuts import render

from statistiques.aggregates import (
    indicateurs,
    par_annee,
    par_auteur,
    par_domaine,
    par_institution,
    par_type,
)


def _pct(value, maximum):
    if not maximum:
        return 0
    return round(100.0 * value / maximum)


def statistiques_publiques(request):
    """Page publique OS5 : production par type, domaine, institution, auteur."""
    kpis = indicateurs()
    types = par_type()
    domaines = par_domaine()
    annees = par_annee()
    institutions = par_institution()
    auteurs = par_auteur()

    max_type = max((row["n"] for row in types), default=0)
    max_domaine = max((row["n"] for row in domaines), default=0)
    max_institution = max((inst.nb_publications for inst in institutions), default=0)
    max_auteur = max((a.nb_publications for a in auteurs), default=0)

    for row in types:
        row["pct"] = _pct(row["n"], max_type)
    for row in domaines:
        row["pct"] = _pct(row["n"], max_domaine)
    for inst in institutions:
        inst.pct = _pct(inst.nb_publications, max_institution)
    for auteur in auteurs:
        auteur.pct = _pct(auteur.nb_publications, max_auteur)

    return render(
        request,
        "pages/statistiques.html",
        {
            **kpis,
            "types": types,
            "domaines": domaines,
            "annees": annees,
            "institutions": institutions,
            "auteurs": auteurs,
            "chart_types": {
                "labels": [row["libelle"] for row in types],
                "values": [row["n"] for row in types],
            },
            "chart_domaines": {
                "labels": [row["libelle"] for row in domaines],
                "values": [row["n"] for row in domaines],
            },
            "chart_annees": {
                "labels": [str(row["annee"]) for row in annees],
                "values": [row["n"] for row in annees],
            },
        },
    )
