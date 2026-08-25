from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404

from publications.metadata import (
    catalogue_oai_dc_xml,
    json_hal,
    metadonnees_publication,
    oai_dc_xml,
)
from publications.models.publication import Publication


def _publication_publique(slug):
    return get_object_or_404(
        Publication.objects.select_related("indexation").prefetch_related(
            "publicationauteur_set__auteur__profile",
        ),
        slug=slug,
        statut_publication=True,
    )


def publication_dc_xml(request, slug):
    publication = _publication_publique(slug)
    meta = metadonnees_publication(publication, request)
    return HttpResponse(
        oai_dc_xml(meta),
        content_type="application/xml; charset=utf-8",
    )


def publication_hal_json(request, slug):
    publication = _publication_publique(slug)
    meta = metadonnees_publication(publication, request)
    return JsonResponse(
        json_hal(meta),
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


def catalogue_dc_xml(request):
    pubs = (
        Publication.objects.filter(statut_publication=True)
        .select_related("indexation")
        .prefetch_related("publicationauteur_set__auteur__profile")
        .order_by("-date_ajout_systeme")
    )
    metas = [metadonnees_publication(pub, request) for pub in pubs]
    return HttpResponse(
        catalogue_oai_dc_xml(metas),
        content_type="application/xml; charset=utf-8",
    )
