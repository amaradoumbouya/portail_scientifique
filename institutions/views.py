from django.shortcuts import render
from institutions.models import Institution
from institutions.forms import InstitutionForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView, CreateView, ListView, UpdateView, DeleteView, DetailView
from django.db.models import Count, Q
from publications.models.publication import (
    Publication,
    ArticleScientifique,
    Colloque
)
from accounts.models import CustumerUser, UserProfile
from projets_detudes.models.candidate import Candidate


def _etudiants_queryset(is_superuser, user_institution=None):
    qs = Candidate.objects.select_related("user", "institution")

    if not is_superuser and user_institution:
        institution_user_ids = UserProfile.objects.filter(
            institution=user_institution
        ).values_list("user_id", flat=True)

        qs = qs.filter(
            Q(institution=user_institution) |
            Q(etudiant__projet__user_id__in=institution_user_ids)
        ).distinct()

    return qs


def _filter_etudiants_par_niveau(qs, niveau):
    if niveau == "master":
        return qs.filter(
            Q(niveau__iexact="master") | Q(etudiant__type_projet="memoire")
        ).distinct()
    if niveau == "doctorat":
        return qs.filter(
            Q(niveau__iexact="doctorat") | Q(etudiant__type_projet="these")
        ).distinct()
    return qs.filter(
        Q(niveau__iexact="master") | Q(niveau__iexact="doctorat") |
        Q(etudiant__type_projet__in=["memoire", "these"])
    ).distinct()


class InstitutionCreateView(CreateView):
    model = Institution
    form_class = InstitutionForm
    template_name = 'back/institutions/index.html'
    success_url = reverse_lazy("institutions:index")

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
            self.object = form.save()
            messages.success(self.request, "Institution ajoutée avec succès !")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["institutions"] = Institution.objects.order_by('-id')
        return context


class InstitutionUpdateView(UpdateView):
    model          = Institution
    form_class     = InstitutionForm
    template_name = "back/institutions/update.html"
    success_url = reverse_lazy("institutions:index")
    context_object_name = "institution"

    def form_valid(self, form):
        messages.success(self.request, f"Institution {self.request.POST.get('nom_institution')} modifié avec succès !")
        return super().form_valid(form)

    
class InstitutionDeleteView(DeleteView):
    model         = Institution
    template_name = "back/institutions/index.html"
    success_url   = reverse_lazy("institutions:index")

class ChercheurDeleteView(DeleteView):
    model         = UserProfile
    template_name = "back/institutions/institut_dashboard.html"
    success_url   = reverse_lazy("institutions:institution_dashboard")


class ChercheurDetailView(DetailView):
    model               = UserProfile
    template_name       = "back/institutions/detail_chercheur.html"
    context_object_name = "chercheur"
    slug_field          = "slug"
    slug_url_kwarg      = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chercheur = self.object

        publications = (
            Publication.objects
            .filter(user=chercheur.user)
            .order_by("-date_ajout_systeme")
        )

        context["publications"] = publications
        context["nbre_publications"] = publications.count()
        context["nbre_articles"] = publications.filter(type_publication="article").count()
        context["nbre_colloques"] = publications.filter(type_publication="colloque").count()
        return context

def institut_dashboard(request):

    # =====================================================
    # Determiner le perimetre d'affichage selon le role
    #   - superuser            -> toute la plateforme
    #   - responsable institution -> uniquement son institution
    # =====================================================

    is_superuser = request.user.is_superuser
    user_institution = None

    user_as_enseignants = (
        UserProfile.objects
        .select_related("user", "institution")
        .annotate(

            # ============================================
            # Nombre total publications
            # ============================================

            nbre_publications=Count('user__publications', distinct=True),

            # ============================================
            # Nombre articles scientifiques
            # ============================================

            nbre_articles=Count('user__publications', filter=Q(user__publications__type_publication='article'), distinct=True),

            # ============================================
            # Nombre communications colloque
            # ============================================

            nbre_colloques=Count('user__publications', filter=Q(user__publications__type_publication='colloque'), distinct=True),
        )
    )

    if not is_superuser:
        # Le responsable d'institution ne voit que son institution
        user_institution = request.user.profile.institution
        user_as_enseignants = user_as_enseignants.filter(institution=user_institution)

    # =====================================================
    # STATISTIQUES GENERALES
    # =====================================================

    total_enseignants = user_as_enseignants.filter(role='enseignant').count()

    total_chercheurs = user_as_enseignants.filter(role='enseignant chercheur').count()

    enseignants_actifs = user_as_enseignants.filter(nbre_publications__gt=0).count()

    enseignants_inactifs = (user_as_enseignants.count() - enseignants_actifs)

    # =====================================================
    # ETUDIANTS (MASTER / DOCTORAT)
    # =====================================================

    etudiants_qs = _etudiants_queryset(is_superuser, user_institution)

    total_master = _filter_etudiants_par_niveau(etudiants_qs, "master").count()
    total_doctorat = _filter_etudiants_par_niveau(etudiants_qs, "doctorat").count()

    # =====================================================
    # ARTICLES / COLLOQUES / PUBLICATIONS
    #   Ces totaux suivent aussi le perimetre du role
    # =====================================================

    if is_superuser:
        publications_qs = Publication.objects.all()
    else:
        publications_qs = Publication.objects.filter(user__profile__institution=user_institution)

    total_articles = publications_qs.filter(type_publication='article').count()

    total_communications = publications_qs.filter(type_publication='colloque').count()

    # Total des publications (perimetre du role)
    total_publications = publications_qs.count()

    # =====================================================
    # PRODUCTION SCIENTIFIQUE
    # =====================================================
    total_production_scientifique = (total_articles + total_communications)

    # =====================================================
    # TOP CHERCHEURS
    #   Enseignants chercheurs et responsables d'institution
    #   actifs (nbre_publications > 0).
    # =====================================================

    top_chercheurs = (
        user_as_enseignants
        .filter(
            role__in=['enseignant', 'enseignant chercheur', 'responsable institution'],
            nbre_publications__gt=0,
        )
        .order_by("-nbre_publications")[:10]
    )

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        # Contrôle d'affichage selon le rôle
        "is_superuser": is_superuser,

        # Table enseignants
        "enseignants": user_as_enseignants,

        # Stats
        "total_enseignants": total_enseignants,
        "total_chercheurs": total_chercheurs,
        "total_publications": total_publications,
        "enseignants_actifs": enseignants_actifs,
        "enseignants_inactifs": enseignants_inactifs,
        "total_master": total_master,
        "total_doctorat": total_doctorat,

        # Publications
        "total_articles": total_articles,
        "total_communications": total_communications,

        # Production scientifique
        "total_production_scientifique": total_production_scientifique,

        # Top chercheurs
        "top_chercheurs": top_chercheurs,
    }

    return render(request,"back/institutions/institut_dashboard.html",context)


def liste_etudiants(request, niveau=None):

    is_superuser = request.user.is_superuser
    user_institution = None

    if not is_superuser:
        user_institution = request.user.profile.institution

    etudiants_qs = _etudiants_queryset(is_superuser, user_institution)

    if niveau in ("master", "doctorat"):
        etudiants = _filter_etudiants_par_niveau(etudiants_qs, niveau).order_by("user__nom", "user__prenoms")
        titres = {
            "master": "Liste des étudiants Master",
            "doctorat": "Liste des étudiants Doctorat",
        }
        page_title = titres[niveau]
    else:
        etudiants = _filter_etudiants_par_niveau(etudiants_qs, None).order_by("user__nom", "user__prenoms")
        page_title = "Liste des étudiants (Master / Doctorat)"

    context = {
        "is_superuser": is_superuser,
        "etudiants": etudiants,
        "page_title": page_title,
        "niveau_actif": niveau,
    }

    return render(request, "back/institutions/liste_etudiants.html", context)