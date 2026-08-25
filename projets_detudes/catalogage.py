import logging
import os

from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


def publier_projet_termine(projet):
    """
    Crée une publication catalogue + indexation NLP
    lorsqu'un mémoire / une thèse passe au statut « terminé ».
    """
    from publications.models.publication import Publication, PublicationAuteur
    from publications.models.projet_publication import ProjetPublication
    from projets_detudes.models.document import Document

    if ProjetPublication.objects.filter(projet=projet, relation_type="principal").exists():
        return None

    document = (
        projet.documents.filter(type_document=Document.TypeDocument.VERSION_FINALE)
        .order_by("-date_upload")
        .first()
    )
    if document is None:
        document = projet.documents.order_by("-date_upload").first()
    if document is None or not document.fichier:
        logger.warning("Projet %s terminé sans fichier à indexer.", projet.pk)
        return None

    type_pub = (
        Publication.TypePublication.THESE
        if projet.type_projet == projet.TypeProjet.THESE
        else Publication.TypePublication.MEMOIRE
    )
    auteur = projet.candidate.user if projet.candidate_id else projet.createur

    publication = Publication(
        titre=projet.titre,
        type_publication=type_pub,
        resume=projet.description or "",
        user=auteur,
        statut_publication=True,
        statut_indexation=Publication.StatutIndexation.ACCEPTEE,
        licence=Publication.Licence.CC_BY,
    )
    document.fichier.open("rb")
    try:
        nom = os.path.basename(document.fichier.name)
        publication.fichier_pdf.save(nom, ContentFile(document.fichier.read()), save=False)
    finally:
        document.fichier.close()

    publication.save()

    try:
        publication.fichier_pdf.open("rb")
        publication.indexer(publication.fichier_pdf, verifier_international=False)
    finally:
        publication.fichier_pdf.close()

    if not publication.domaine and projet.candidate_id:
        publication.domaine = projet.candidate.domaine or ""
    publication.save()

    if auteur is not None:
        PublicationAuteur.objects.get_or_create(
            publication=publication,
            auteur=auteur,
            defaults={"role": "Auteur principal", "ordre": 1},
        )
    ProjetPublication.objects.create(
        projet=projet,
        publication=publication,
        relation_type="principal",
    )
    return publication
