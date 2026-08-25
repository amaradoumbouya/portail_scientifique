"""Métadonnées d'export : Dublin Core (oai_dc) et JSON style HAL."""

import json
from xml.sax.saxutils import escape

from django.urls import reverse
from django.utils.safestring import mark_safe

PUBLISHER = "Portail Scientifique CRICT"

TYPE_OPENAIRE = {
    "article": "info:eu-repo/semantics/article",
    "colloque": "info:eu-repo/semantics/conferenceObject",
    "memoire": "info:eu-repo/semantics/masterThesis",
    "these": "info:eu-repo/semantics/doctoralThesis",
}

TYPE_HAL = {
    "article": "ART",
    "colloque": "COMM",
    "memoire": "MEM",
    "these": "THESE",
}

TYPE_SCHEMA = {
    "article": "ScholarlyArticle",
    "colloque": "ScholarlyArticle",
    "memoire": "Thesis",
    "these": "Thesis",
}

OAI_DC_NS = "http://www.openarchives.org/OAI/2.0/oai_dc/"
DC_NS = "http://purl.org/dc/elements/1.1/"


def _orcid(user):
    profile = getattr(user, "profile", None)
    raw = (getattr(profile, "orcid", None) or "").strip()
    if not raw:
        return ""
    if raw.startswith("http"):
        return raw
    return f"https://orcid.org/{raw}"


def _auteurs(publication):
    auteurs = []
    for lien in publication.publicationauteur_set.all():
        user = lien.auteur
        if not user:
            continue
        auteurs.append({
            "nom": user.nom or "",
            "prenoms": user.prenoms or "",
            "citation": f"{user.nom}, {user.prenoms}".strip(", "),
            "full": user.full_name,
            "orcid": _orcid(user),
        })
    if not auteurs and publication.user:
        user = publication.user
        auteurs.append({
            "nom": user.nom or "",
            "prenoms": user.prenoms or "",
            "citation": f"{user.nom}, {user.prenoms}".strip(", "),
            "full": user.full_name,
            "orcid": _orcid(user),
        })
    return auteurs


def _mots_cles(publication):
    return [m.strip() for m in (publication.mots_cles or "").split(",") if m.strip()]


def metadonnees_publication(publication, request):
    """Dictionnaire unique consommé par XML DC, JSON HAL et JSON-LD."""
    real = publication.get_real_instance()
    html_url = request.build_absolute_uri(publication.get_absolute_url())
    pdf_url = (
        request.build_absolute_uri(publication.fichier_pdf.url)
        if publication.fichier_pdf
        else ""
    )
    dc_url = request.build_absolute_uri(
        reverse("portail_site:publication_dc_xml", kwargs={"slug": publication.slug})
    )
    json_url = request.build_absolute_uri(
        reverse("portail_site:publication_hal_json", kwargs={"slug": publication.slug})
    )
    date_iso = ""
    if publication.date_ajout_systeme:
        date_iso = publication.date_ajout_systeme.date().isoformat()

    type_code = publication.type_publication or "article"
    return {
        "slug": publication.slug,
        "title": publication.titre or "",
        "auteurs": _auteurs(publication),
        "subjects": _mots_cles(publication),
        "description": (publication.resume or "").strip(),
        "publisher": PUBLISHER,
        "date": date_iso,
        "updated": publication.updated_at.date().isoformat() if publication.updated_at else date_iso,
        "language": publication.citation_language,
        "type_code": type_code,
        "type_label": publication.get_type_publication_display() or "",
        "type_openaire": TYPE_OPENAIRE.get(type_code, "info:eu-repo/semantics/other"),
        "type_hal": TYPE_HAL.get(type_code, "ART"),
        "type_schema": TYPE_SCHEMA.get(type_code, "ScholarlyArticle"),
        "format": "application/pdf" if pdf_url else "",
        "html_url": html_url,
        "pdf_url": pdf_url,
        "dc_url": dc_url,
        "json_url": json_url,
        "doi": publication.doi_identifiant,
        "doi_url": publication.doi_url,
        "licence": publication.get_licence_display() if publication.licence else "",
        "licence_code": publication.licence or "",
        "licence_url": publication.licence_url or "",
        "domaine": publication.domaine or "",
        "source": getattr(real, "nom_revue", None) or getattr(real, "nom_colloque", None) or "",
        "oai_id": f"oai:portailscientifique.crict.edu.gn:publication/{publication.slug}",
    }


def oai_dc_xml(meta, xml_declaration=True):
    lines = []
    if xml_declaration:
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        f'<oai_dc:dc xmlns:oai_dc="{OAI_DC_NS}" xmlns:dc="{DC_NS}" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        f'xsi:schemaLocation="{OAI_DC_NS} http://www.openarchives.org/OAI/2.0/oai_dc.xsd">'
    )

    def add(name, value):
        if value:
            lines.append(f"  <dc:{name}>{escape(str(value))}</dc:{name}>")

    add("title", meta["title"])
    for auteur in meta["auteurs"]:
        add("creator", auteur["citation"])
    add("subject", meta["domaine"])
    for mot in meta["subjects"]:
        add("subject", mot)
    add("description", meta["description"])
    add("publisher", meta["publisher"])
    add("date", meta["date"])
    add("type", "Text")
    add("type", meta["type_openaire"])
    add("type", meta["type_label"])
    add("format", meta["format"])
    add("identifier", meta["html_url"])
    add("identifier", meta["oai_id"])
    if meta["doi"]:
        add("identifier", f"doi:{meta['doi']}")
        add("identifier", meta["doi_url"])
    if meta["pdf_url"]:
        add("identifier", meta["pdf_url"])
    add("source", meta["source"])
    add("language", meta["language"])
    add("coverage", meta["domaine"])
    add("rights", meta["licence"])
    add("rights", meta["licence_url"])
    lines.append("</oai_dc:dc>")
    return "\n".join(lines)


def catalogue_oai_dc_xml(metas):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<records xmlns:oai_dc="%s" xmlns:dc="%s">' % (OAI_DC_NS, DC_NS),
    ]
    for meta in metas:
        lines.append("  <record>")
        lines.append("    <header>")
        lines.append(f'      <identifier>{escape(meta["oai_id"])}</identifier>')
        if meta["updated"]:
            lines.append(f'      <datestamp>{escape(meta["updated"])}</datestamp>')
        lines.append("    </header>")
        lines.append("    <metadata>")
        inner = oai_dc_xml(meta, xml_declaration=False)
        for line in inner.splitlines():
            lines.append("      " + line)
        lines.append("    </metadata>")
        lines.append("  </record>")
    lines.append("</records>")
    return "\n".join(lines)


def json_hal(meta):
    """Document JSON proche des champs HAL (docType, authFullName, doiId…)."""
    return {
        "docType_s": meta["type_hal"],
        "title_s": meta["title"],
        "authFullName_s": [a["full"] for a in meta["auteurs"]],
        "doiId_s": meta["doi"] or None,
        "abstract_s": meta["description"] or None,
        "keyword_s": meta["subjects"],
        "language_s": meta["language"],
        "licence_s": meta["licence_code"] or None,
        "producedDate_s": meta["date"] or None,
        "domain_s": meta["domaine"] or None,
        "journalTitle_s": meta["source"] if meta["type_code"] == "article" else None,
        "conferenceTitle_s": meta["source"] if meta["type_code"] == "colloque" else None,
        "uri_s": meta["html_url"],
        "fileMain_s": meta["pdf_url"] or None,
        "publisher_s": meta["publisher"],
        "halId_s": meta["oai_id"],
    }


def json_ld(meta):
    authors = []
    for auteur in meta["auteurs"]:
        person = {"@type": "Person", "name": auteur["full"]}
        if auteur["orcid"]:
            person["identifier"] = auteur["orcid"]
        authors.append(person)
    data = {
        "@context": "https://schema.org",
        "@type": meta["type_schema"],
        "name": meta["title"],
        "headline": meta["title"],
        "author": authors,
        "datePublished": meta["date"] or None,
        "inLanguage": meta["language"],
        "url": meta["html_url"],
        "publisher": {"@type": "Organization", "name": meta["publisher"]},
    }
    if meta["description"]:
        data["abstract"] = meta["description"]
    if meta["subjects"]:
        data["keywords"] = ", ".join(meta["subjects"])
    if meta["doi_url"]:
        data["identifier"] = meta["doi_url"]
    if meta["licence_url"]:
        data["license"] = meta["licence_url"]
    if meta["pdf_url"]:
        data["encoding"] = {
            "@type": "MediaObject",
            "contentUrl": meta["pdf_url"],
            "encodingFormat": "application/pdf",
        }
    return data


def json_ld_script(data):
    payload = json.dumps(data, ensure_ascii=False)
    payload = (
        payload.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    return mark_safe(payload)
