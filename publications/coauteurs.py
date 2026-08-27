"""
Identification des co-auteurs à partir de l'article (PDF / DOI).

L'article est la source de vérité : on ne redemande pas les noms ni les
affiliations dans le formulaire. Un compte n'est jamais créé ici — le PDF
ne contient pas d'email. Les auteurs cités doivent déjà être inscrits et
rattachés à une institution du portail.
"""
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from accounts.models import CustumerUser
from publications.models.publication import PublicationAuteur
from publications.verification_affiliations import (
    apparier_institution,
    auteurs_correspondent,
    nom_auteur_dans_texte,
    texte_entete,
    _institution_auteur,
)


def extraire_noms_depuis_pdf(texte):
    """Noms de personnes détectés dans l'entête du PDF (spaCy)."""
    tete = texte_entete(texte)
    if not tete or len(tete.strip()) < 20:
        return []
    try:
        from publications.nlp_tools import nlp
    except Exception:
        return []
    doc = nlp(tete[:5000])
    noms = []
    vus = set()
    for ent in doc.ents:
        if ent.label_ not in ("PER", "PERSON"):
            continue
        parts = [p for p in ent.text.replace(",", " ").split() if p]
        if len(parts) < 2:
            continue
        item = {"prenoms": " ".join(parts[:-1]), "nom": parts[-1], "affiliations": []}
        cle = (item["prenoms"].lower(), item["nom"].lower())
        if cle not in vus:
            vus.add(cle)
            noms.append(item)
    return noms


def _libelle_cite(cite):
    return f"{cite.get('prenoms') or ''} {cite.get('nom') or ''}".strip() or "auteur cité"


def _trouver_utilisateurs(prenoms, nom):
    if not (nom or "").strip():
        return []
    candidats = (
        CustumerUser.objects.filter(nom__iexact=str(nom).strip())
        .select_related("profile", "profile__institution")
    )
    return [
        user for user in candidats
        if auteurs_correspondent(user, prenoms or "", nom or "")
    ]


def _choisir_utilisateur(matches, affiliations):
    if not matches:
        return None, None
    if len(matches) == 1:
        return matches[0], None
    if affiliations:
        for user in matches:
            institution = _institution_auteur(user)
            if not institution:
                continue
            for affiliation in affiliations:
                if apparier_institution(affiliation, [institution]):
                    return user, None
    noms = ", ".join(u.full_name for u in matches[:4])
    return None, (
        f"plusieurs comptes correspondent à cet auteur ({noms}). "
        "Impossible de l'identifier de façon univoque."
    )


def _auteurs_cites(texte_pdf, meta_externes):
    cites = []
    for auteur in (meta_externes or {}).get("auteurs") or []:
        if (auteur.get("nom") or "").strip():
            cites.append({
                "prenoms": (auteur.get("prenoms") or "").strip(),
                "nom": (auteur.get("nom") or "").strip(),
                "affiliations": list(auteur.get("affiliations") or []),
            })
    if cites:
        return cites, "doi"

    cites = extraire_noms_depuis_pdf(texte_pdf)
    return cites, "pdf"


def _utilisateurs_mentionnes_dans_pdf(texte_pdf, deposant):
    tete = texte_entete(texte_pdf)
    if not tete:
        return []
    qs = CustumerUser.objects.select_related("profile", "profile__institution")
    if deposant and getattr(deposant, "pk", None):
        qs = qs.exclude(pk=deposant.pk)
    trouves = []
    for user in qs:
        if nom_auteur_dans_texte(user, tete):
            trouves.append(user)
    return trouves


def resoudre_auteurs_cites(texte_pdf="", meta_externes=None, deposant=None):
    """
    Relie les auteurs cités dans l'article aux comptes déjà inscrits.

    Ne crée aucun compte : sans email (absent du PDF), un nouvel auteur
    ne peut pas être inscrit automatiquement.
    """
    cites, source = _auteurs_cites(texte_pdf, meta_externes)
    existants = []
    rejets = []
    vus = set()
    deposant_pk = getattr(deposant, "pk", None)

    def ajouter_existant(user, role, ordre):
        if not user or user.pk in vus or user.pk == deposant_pk:
            return
        institution = _institution_auteur(user)
        if institution is None:
            rejets.append(
                f"{user.full_name} est cité(e) dans l'article et inscrit(e) "
                "sur la plateforme, mais n'est rattaché(e) à aucune institution."
            )
            return
        vus.add(user.pk)
        existants.append({"user": user, "role": role, "ordre": ordre})

    if source == "doi" or cites:
        for index, cite in enumerate(cites):
            matches = _trouver_utilisateurs(cite.get("prenoms"), cite.get("nom"))
            user, ambigu = _choisir_utilisateur(
                matches, cite.get("affiliations") or []
            )
            libelle = _libelle_cite(cite)
            if ambigu:
                rejets.append(f"{libelle} : {ambigu}")
                continue
            if user is None:
                if deposant and auteurs_correspondent(
                    deposant, cite.get("prenoms") or "", cite.get("nom") or ""
                ):
                    continue
                rejets.append(
                    f"{libelle} est cité(e) dans l'article mais n'a pas de compte "
                    "sur la plateforme. Aucun compte n'a été créé : l'article ne "
                    "contient pas d'email. Cette personne doit d'abord s'inscrire "
                    "et rattacher son institution."
                )
                continue
            ajouter_existant(user, "Co-auteur", index + 2)
    else:
        for index, user in enumerate(_utilisateurs_mentionnes_dans_pdf(texte_pdf, deposant)):
            ajouter_existant(user, "Co-auteur", index + 2)

    return {
        "existants": existants,
        "a_creer": [],
        "rejets": rejets,
        "source": source,
    }


def enregistrer_coauteurs(publication, analyse, request, sujet_existant):
    """Lie les co-auteurs déjà inscrits et les notifie."""
    current_site = get_current_site(request)

    for item in analyse.get("existants") or []:
        publication_auteur, _created = PublicationAuteur.objects.get_or_create(
            auteur=item["user"],
            publication=publication,
            defaults={"role": item["role"], "ordre": item["ordre"]},
        )
        login_url = f"http://{current_site.domain}/connexion/"
        message = render_to_string(
            "emails/information_participant.html",
            {
                "user": item["user"],
                "role": publication_auteur.role,
                "login_url": login_url,
            },
        )
        send_mail(
            sujet_existant,
            "",
            settings.DEFAULT_FROM_EMAIL,
            [item["user"].email],
            html_message=message,
            fail_silently=False,
        )
