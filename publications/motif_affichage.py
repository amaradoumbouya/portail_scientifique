"""Découpe le motif de rejet brut en blocs lisibles pour l'affichage."""
from __future__ import annotations

import re

PREFIX_AFFILIATIONS = "Rejet (vérification des affiliations) :"

_NOUVEAU_POINT = re.compile(
    r"(?:"
    r"les auteurs suivants|"
    r"les affiliations suivantes|"
    r"aucune des institutions|"
    r"aucune institution inscrite|"
    r"l'affiliation déclarée|"
    r"les auteurs cités suivants|"
    r"affiliations ou auteurs non conformes|"
    r"publication non reconnue|"
    r"vérification d['']indexation|"
    r"vérification des affiliations|"
    r"texte pdf court|"
    r"enrichissement nlp"
    r")",
    re.I,
)

_NOM_CITE = re.compile(
    r"^[A-ZÀ-Ÿ][\w'’.\-]+(?:\s+[A-ZÀ-Ÿ][\w'’.\-]+){0,4}\s+est cité",
    re.I,
)


def _capitaliser(texte):
    texte = (texte or "").strip(" \t-•")
    if not texte:
        return ""
    return texte[0].upper() + texte[1:] if len(texte) > 1 else texte.upper()


def _est_nouveau_point(fragment):
    texte = (fragment or "").strip()
    if not texte:
        return False
    if PREFIX_AFFILIATIONS.lower() in texte.lower()[:80]:
        return True
    if _NOUVEAU_POINT.match(texte):
        return True
    if _NOM_CITE.match(texte):
        return True
    return False


def _segments_bruts(corps):
    if not corps:
        return []
    blocs = []
    for bloc in re.split(r"\n+", corps):
        bloc = bloc.strip(" \t-•")
        if not bloc:
            continue
        morceaux = re.split(r"(?<=[.!?])\s+", bloc)
        courant = ""
        for morceau in morceaux:
            morceau = morceau.strip()
            if not morceau:
                continue
            if not courant:
                courant = morceau
                continue
            if _est_nouveau_point(morceau):
                blocs.append(courant)
                courant = morceau
            else:
                courant = f"{courant} {morceau}"
        if courant:
            blocs.append(courant)
    return blocs


def structurer_motif_rejet(texte, statut=""):
    """
    Retourne un dict pour le template :
      titre, kicker, niveau (affiliations|indexation|attente),
      intro, points (list[str]), conseil
    """
    brut = re.sub(r"\s+", " ", (texte or "").strip())
    brut_original = (texte or "").strip()
    source = brut_original if "\n" in brut_original else brut

    if not source:
        return None

    source_l = source.lower()
    if (
        "vérification des affiliations" in source_l
        or "règle nationale" in source_l
        or "institution inscrite" in source_l
        or "n'a pas de compte" in source_l
    ):
        niveau = "affiliations"
        titre = "Motif de rejet"
        kicker = "Vérification des affiliations"
        intro = (
            "La publication a été rejetée dès le contrôle des institutions "
            "et des auteurs (niveau 1), avant l'interrogation de Scopus, "
            "WoS, DOAJ et AJOL."
        )
        conseil = (
            "Chaque auteur cité doit déjà être inscrit sur le portail et "
            "rattaché à une institution enregistrée. Une affiliation "
            "étrangère non inscrite entraîne le rejet."
        )
    elif any(mot in source_l for mot in ("scopus", "doaj", "ajol", "web of science", "wos")):
        niveau = "indexation"
        titre = "Motif de rejet"
        kicker = "Indexation internationale"
        intro = (
            "Le contrôle des affiliations est passé, mais la publication "
            "n'a pas été reconnue dans les bases internationales."
        )
        conseil = (
            "L'article ou la revue doit être indexé dans Scopus, "
            "Web of Science (WoS), DOAJ ou AJOL."
        )
    elif statut == "En attente" or "en cours" in source_l or "en attente" in source_l:
        niveau = "attente"
        titre = "Vérification en cours"
        kicker = "Statut"
        intro = "La publication a été enregistrée ; le contrôle n'est pas encore terminé."
        conseil = ""
    else:
        niveau = "rejet"
        titre = "Motif"
        kicker = "Examen de la publication"
        intro = ""
        conseil = ""

    corps = source
    corps = re.sub(
        re.escape(PREFIX_AFFILIATIONS),
        "\n",
        corps,
        flags=re.I,
    )
    points = []
    vus = set()
    for segment in _segments_bruts(corps):
        point = _capitaliser(segment)
        point = re.sub(
            r"^Rejet\s*\(vérification des affiliations\)\s*:\s*",
            "",
            point,
            flags=re.I,
        ).strip()
        if not point:
            continue
        if point.endswith("…"):
            pass
        elif not point.endswith("."):
            point += "."
        cle = point.lower()
        if cle in vus:
            continue
        vus.add(cle)
        points.append(point)

    if not points and brut:
        points = [_capitaliser(brut)]

    return {
        "titre": titre,
        "kicker": kicker,
        "niveau": niveau,
        "intro": intro,
        "points": points,
        "conseil": conseil,
    }
