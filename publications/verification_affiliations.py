"""
Vérification de niveau 1 (avant Scopus / WoS / DOAJ / AJOL) :

Portail national — règle stricte :
1. Toute institution citée dans l'article doit être inscrite sur la plateforme.
   Une affiliation étrangère non enregistrée entraîne le rejet.
2. Les auteurs doivent être affiliés, sur la plateforme, à ces institutions.

Un échec à ce niveau est un motif prioritaire de rejet : les bases internationales
ne sont interrogées que si ces contrôles passent.
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

from django.contrib.auth import get_user_model

from institutions.models import Institution


User = get_user_model()

MOTIFS_PREFIXE = "Rejet (vérification des affiliations) :"

_STOP_INST = {
    "universite", "university", "univ", "institut", "institute",
    "centre", "center", "college", "ecole", "school", "faculte",
    "faculty", "laboratoire", "laboratory", "lab", "hopital",
    "hospital", "academie", "academy", "departement", "department",
    "recherche", "research", "national", "internationale",
    "international", "de", "du", "des", "la", "le", "les", "the",
    "of", "and", "et", "en", "sur", "pour", "au", "aux", "d", "l",
    "a", "à",
}

_MOTS_AFFILIATION = re.compile(
    r"universit|institut|center|centre|laborato|college|école|ecole|"
    r"hospital|hôpital|acad[ée]mie|facult|department|d[ée]partement|"
    r"research|recherche|school",
    re.I,
)

_COUPURE_ENTETE = re.compile(
    r"\b(abstract|résumé|resume|introduction|keywords|mots[-\s]?cl[ée]s)\b",
    re.I,
)


def normaliser_texte(valeur):
    texte = unicodedata.normalize("NFKD", str(valeur or ""))
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    texte = texte.lower()
    texte = re.sub(r"[^a-z0-9\s]", " ", texte)
    return re.sub(r"\s+", " ", texte).strip()


def normaliser_sigle(valeur):
    return re.sub(r"[^a-z0-9]", "", normaliser_texte(valeur))


def texte_entete(texte, max_chars=12000):
    if not texte:
        return ""
    tete = str(texte)[:max_chars]
    match = _COUPURE_ENTETE.search(tete)
    if match and match.start() > 80:
        tete = tete[: match.start()]
    return tete


def decouper_affiliations(valeur):
    if not valeur:
        return []
    parties = re.split(r"\s*[;|/]\s*", str(valeur))
    return [p.strip(" ,·•-") for p in parties if p and p.strip(" ,·•-")]


_MOTS_INSTITUTION_STRICTE = re.compile(
    r"universit|institut|center|centre|college|école|ecole|"
    r"hospital|hôpital|acad[ée]mie",
    re.I,
)


_ENTETES_IGNORER = {
    "abstract", "resume", "resume", "introduction", "keywords",
    "references", "acknowledgements", "remerciements", "conclusion",
}


def affiliation_doit_etre_inscrite(texte):
    """True si la chaîne désigne une institution (pas un simple département)."""
    brut = (texte or "").strip()
    if len(brut) < 3:
        return False
    if normaliser_texte(brut) in _ENTETES_IGNORER:
        return False
    if _MOTS_INSTITUTION_STRICTE.search(brut) and len(brut) >= 8:
        return True
    compact = normaliser_sigle(brut)
    lettres = re.sub(r"[^A-Za-z]", "", brut)
    if (
        2 <= len(compact) <= 8
        and compact.isalpha()
        and lettres.isupper()
        and len(lettres) >= 2
    ):
        return True
    return False


def extraire_lignes_affiliation(texte):
    """Lignes de l'entête qui ressemblent à une affiliation institutionnelle."""
    lignes = []
    for brute in texte_entete(texte).splitlines():
        ligne = re.sub(r"\s+", " ", brute).strip(" ,;·•-")
        for partie in decouper_affiliations(ligne) or ([ligne] if ligne else []):
            if 8 <= len(partie) <= 240 and _MOTS_AFFILIATION.search(partie):
                if partie not in lignes:
                    lignes.append(partie)
            elif affiliation_doit_etre_inscrite(partie) and partie not in lignes:
                lignes.append(partie)
    return lignes


def _tokens_significatifs(texte_norm):
    return [
        tok for tok in (texte_norm or "").split()
        if len(tok) > 3 and tok not in _STOP_INST
    ]


def score_correspondance_institution(texte_affiliation, institution):
    """Score 0–1 entre une chaîne extraite et une institution inscrite."""
    cible = normaliser_texte(texte_affiliation)
    nom = normaliser_texte(institution.nom_institution)
    sigle = normaliser_sigle(institution.sigle_institution)
    cible_sigle = normaliser_sigle(texte_affiliation)

    if not cible:
        return 0.0

    if sigle and len(sigle) >= 3 and (cible_sigle == sigle or sigle in cible.split() or sigle in cible_sigle):
        return 1.0

    if nom and (nom == cible or nom in cible or (len(cible) >= 8 and cible in nom)):
        return 0.96

    if nom:
        ratio = SequenceMatcher(None, cible, nom).ratio()
        tokens_nom = _tokens_significatifs(nom)
        tokens_cible = set(_tokens_significatifs(cible))
        if tokens_nom:
            recouvrement = sum(1 for tok in tokens_nom if tok in tokens_cible) / len(tokens_nom)
            return max(ratio, recouvrement)
        return ratio
    return 0.0


def apparier_institution(texte_affiliation, institutions, seuil=0.82):
    meilleur = None
    meilleur_score = 0.0
    for institution in institutions:
        score = score_correspondance_institution(texte_affiliation, institution)
        if score > meilleur_score:
            meilleur_score = score
            meilleur = institution
    if meilleur and meilleur_score >= seuil:
        return meilleur
    return None


def institutions_mentionnees_dans_texte(texte, institutions):
    """Institutions inscrites dont le nom ou le sigle apparaît dans le texte."""
    if not texte:
        return []
    texte_norm = normaliser_texte(texte)
    texte_sigle = normaliser_sigle(texte)
    trouvees = []
    for institution in institutions:
        nom = normaliser_texte(institution.nom_institution)
        sigle = normaliser_sigle(institution.sigle_institution)
        if sigle and len(sigle) >= 3:
            if re.search(rf"\b{re.escape(sigle)}\b", texte_norm) or sigle in texte_sigle:
                trouvees.append(institution)
                continue
        if nom and len(nom) >= 8 and nom in texte_norm:
            trouvees.append(institution)
            continue
        tokens = _tokens_significatifs(nom)
        if len(tokens) >= 2:
            presents = sum(1 for tok in tokens if tok in texte_norm)
            if presents >= max(2, len(tokens) - 1):
                trouvees.append(institution)
    return trouvees


def nom_auteur_dans_texte(user, texte):
    if not user or not texte:
        return False
    texte_norm = normaliser_texte(texte)
    nom = normaliser_texte(user.nom)
    prenoms = normaliser_texte(user.prenoms)
    if not nom or nom not in texte_norm:
        return False
    if not prenoms:
        return len(nom) >= 4
    if prenoms in texte_norm:
        return True
    initiales = " ".join(p[0] for p in prenoms.split() if p)
    if initiales and f"{initiales} {nom}" in texte_norm:
        return True
    premier = prenoms.split()[0]
    if premier and (
        f"{premier[0]} {nom}" in texte_norm
        or f"{premier[0]} {nom}" in texte_norm.replace(".", " ")
    ):
        return True
    return len(nom) >= 5


def auteurs_correspondent(user, prenoms, nom):
    if not user:
        return False
    nom_u = normaliser_texte(user.nom)
    prenoms_u = normaliser_texte(user.prenoms)
    nom_c = normaliser_texte(nom)
    prenoms_c = normaliser_texte(prenoms)
    if not nom_u or not nom_c or nom_u != nom_c:
        if not (
            nom_u and nom_c and (
                nom_u in nom_c or nom_c in nom_u
            ) and min(len(nom_u), len(nom_c)) >= 4
        ):
            return False
    if not prenoms_c or not prenoms_u:
        return bool(nom_u)
    if prenoms_u == prenoms_c or prenoms_u in prenoms_c or prenoms_c in prenoms_u:
        return True
    init_u = "".join(p[0] for p in prenoms_u.split() if p)
    init_c = "".join(p[0] for p in prenoms_c.split() if p)
    return bool(init_u and init_c and init_u == init_c)


def _institution_auteur(user):
    profile = getattr(user, "profile", None)
    return getattr(profile, "institution", None) if profile else None


def _libelle_auteur(user):
    if not user:
        return "auteur inconnu"
    return (user.full_name or user.email or "auteur").strip()


def _uniques(institutions):
    vus = set()
    resultat = []
    for inst in institutions:
        if inst and inst.pk not in vus:
            vus.add(inst.pk)
            resultat.append(inst)
    return resultat


def _auteurs_depot(publication):
    liens = list(
        publication.publicationauteur_set.select_related(
            "auteur",
            "auteur__profile",
            "auteur__profile__institution",
        ).order_by("ordre")
    )
    auteurs = [lien.auteur for lien in liens if lien.auteur]
    if auteurs:
        return auteurs
    if publication.user:
        return [publication.user]
    return []


def _identifier_auteur_plateforme(prenoms, nom, auteurs_connus):
    for user in auteurs_connus:
        if auteurs_correspondent(user, prenoms, nom):
            return user
    if not nom:
        return None
    candidats = (
        User.objects.filter(nom__iexact=str(nom).strip())
        .select_related("profile", "profile__institution")
    )
    for user in candidats:
        if auteurs_correspondent(user, prenoms, nom):
            return user
    return None


def verifier_affiliations_et_auteurs(publication, texte_pdf="", meta_externes=None):
    """
    Contrôle prioritaire des institutions et des affiliations d'auteurs.

    Retourne un dict :
      - statut: 'Acceptée' | 'Rejetée'
      - motif: str
      - institutions_reconnues: list[Institution]
      - details: dict
    """
    meta_externes = meta_externes or {}
    texte = texte_pdf or getattr(publication, "texte_integral", "") or ""
    institutions = list(Institution.objects.all())
    auteurs = _auteurs_depot(publication)
    motifs = []

    if not institutions:
        return {
            "statut": "Rejetée",
            "motif": (
                f"{MOTIFS_PREFIXE} aucune institution n'est inscrite sur la "
                "plateforme. Impossible de valider les affiliations."
            ),
            "institutions_reconnues": [],
            "details": {},
        }

    if not auteurs:
        return {
            "statut": "Rejetée",
            "motif": (
                f"{MOTIFS_PREFIXE} aucun auteur n'est associé à cette soumission."
            ),
            "institutions_reconnues": [],
            "details": {},
        }

    auteurs_sans_institution = []
    institutions_auteurs = []
    for auteur in auteurs:
        institution = _institution_auteur(auteur)
        if institution is None:
            auteurs_sans_institution.append(_libelle_auteur(auteur))
        else:
            institutions_auteurs.append(institution)

    if auteurs_sans_institution:
        noms = ", ".join(auteurs_sans_institution)
        motifs.append(
            "les auteurs suivants ne sont affiliés à aucune institution "
            f"inscrite sur la plateforme : {noms}. Chaque auteur doit être "
            "rattaché à une institution déjà enregistrée."
        )

    affiliations_extraites = []
    for brute in list(meta_externes.get("affiliations") or []):
        for partie in decouper_affiliations(brute) or [brute]:
            if partie and partie not in affiliations_extraites:
                affiliations_extraites.append(partie)
    for ligne in extraire_lignes_affiliation(texte):
        if ligne not in affiliations_extraites:
            affiliations_extraites.append(ligne)

    institutions_citees = []
    institutions_citees.extend(
        institutions_mentionnees_dans_texte(texte[:12000], institutions)
    )
    for affiliation in affiliations_extraites:
        appariee = apparier_institution(affiliation, institutions)
        if appariee:
            institutions_citees.append(appariee)

    institutions_citees = _uniques(institutions_citees)
    institutions_auteurs = _uniques(institutions_auteurs)

    affiliations_non_inscrites = []
    for affiliation in affiliations_extraites:
        if apparier_institution(affiliation, institutions) is None:
            if affiliation_doit_etre_inscrite(affiliation):
                affiliations_non_inscrites.append(affiliation)

    if affiliations_non_inscrites:
        apercu = "; ".join(affiliations_non_inscrites[:5])
        motifs.append(
            "les affiliations suivantes ne correspondent à aucune institution "
            "inscrite sur la plateforme (règle nationale stricte) : "
            f"{apercu}."
        )

    if not institutions_citees:
        if affiliations_extraites and not affiliations_non_inscrites:
            apercu = "; ".join(affiliations_extraites[:5])
            motifs.append(
                "aucune des institutions citées dans l'article n'est inscrite "
                f"sur la plateforme. Institutions détectées : {apercu}."
            )
        elif not affiliations_extraites:
            motifs.append(
                "aucune institution inscrite sur la plateforme n'a pu être "
                "identifiée dans l'article. Les affiliations citées doivent "
                "correspondre à des institutions déjà enregistrées."
            )

    auteurs_hors_institutions_citees = []
    if institutions_citees:
        ids_cites = {inst.pk for inst in institutions_citees}
        for auteur in auteurs:
            institution = _institution_auteur(auteur)
            if institution and institution.pk not in ids_cites:
                auteurs_hors_institutions_citees.append(
                    f"{_libelle_auteur(auteur)} ({institution.nom_institution})"
                )
        if auteurs_hors_institutions_citees:
            noms = ", ".join(auteurs_hors_institutions_citees)
            cites = ", ".join(inst.nom_institution for inst in institutions_citees)
            motifs.append(
                "les auteurs suivants ne sont pas affiliés aux institutions "
                f"citées dans l'article ({cites}) : {noms}."
            )
    elif institutions_auteurs and not affiliations_extraites:
        # Texte sans affiliation exploitable : exiger au moins le nom / sigle
        # de l'institution déclarée dans le document.
        manquants = []
        for auteur in auteurs:
            institution = _institution_auteur(auteur)
            if institution and institution not in institutions_mentionnees_dans_texte(
                texte[:12000], [institution]
            ):
                manquants.append(
                    f"{_libelle_auteur(auteur)} ({institution.nom_institution})"
                )
        if manquants:
            motifs.append(
                "l'affiliation déclarée n'apparaît pas dans l'article pour : "
                f"{', '.join(manquants)}."
            )

    auteurs_externes = meta_externes.get("auteurs") or []
    auteurs_cites_incoherents = []
    if institutions_citees:
        ids_cites = {inst.pk for inst in institutions_citees}
        for item in auteurs_externes:
            user = _identifier_auteur_plateforme(
                item.get("prenoms") or "",
                item.get("nom") or "",
                auteurs,
            )
            if not user:
                continue
            institution = _institution_auteur(user)
            if institution is None or institution.pk not in ids_cites:
                auteurs_cites_incoherents.append(_libelle_auteur(user))
        if auteurs_cites_incoherents:
            noms = ", ".join(dict.fromkeys(auteurs_cites_incoherents))
            motifs.append(
                "les auteurs cités suivants, identifiés sur la plateforme, "
                "ne sont pas affiliés aux institutions citées dans l'article : "
                f"{noms}."
            )

    if motifs:
        return {
            "statut": "Rejetée",
            "motif": f"{MOTIFS_PREFIXE} " + " ".join(motifs),
            "institutions_reconnues": institutions_citees,
            "details": {
                "auteurs_sans_institution": auteurs_sans_institution,
                "affiliations_extraites": affiliations_extraites,
                "affiliations_non_inscrites": affiliations_non_inscrites,
            },
        }

    return {
        "statut": "Acceptée",
        "motif": "",
        "institutions_reconnues": institutions_citees,
        "details": {
            "auteurs_sans_institution": [],
            "affiliations_extraites": affiliations_extraites,
            "affiliations_non_inscrites": affiliations_non_inscrites,
        },
    }
