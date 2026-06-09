from django.shortcuts import render
from institutions.models import Institution
from institutions.forms import InstitutionForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView, CreateView, ListView, UpdateView, DeleteView
from django.db.models import Count, Q
from publications.models.publication import (
    Publication,
    ArticleScientifique,
    Colloque
)
from accounts.models import CustumerUser, UserProfile


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







def institut_dashboard(request):

    # =====================================================
    # Recuperer l'institution du responsable d'institution
    # =====================================================

    user_institution = request.user.profile.institution


    # Recuperer tous les utilisateurs inscrits au compte de cette institutions

    # user_as_enseignants = UserProfile.objects.filter(institution=user_institution).select_related("user").annotate(nbre_publications=Count('user__publications',distinct=True))

    user_as_enseignants = UserProfile.objects.filter(institution=user_institution).select_related("user").annotate(

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

        nbre_colloques=Count('user__publications', filter=Q(user__publications__type_publication='colloque'),distinct=True)
    )

    # =====================================================
    # STATISTIQUES GENERALES
    # =====================================================

    total_enseignants = user_as_enseignants.count()

    total_chercheurs = user_as_enseignants.filter().count()

    # Total de publication reconnu à l'internations par celle publiée sur cette plateforme
    total_publications = Publication.objects.count()

    enseignants_actifs = user_as_enseignants.filter(nbre_publications__gt=0).count()

    enseignants_inactifs = ((user_as_enseignants.count())- enseignants_actifs)

    # =====================================================
    # ARTICLES SCIENTIFIQUES
    # =====================================================

    total_articles = ArticleScientifique.objects.count()

    # =====================================================
    # COMMUNICATIONS COLLOQUE
    # =====================================================

    total_communications = Colloque.objects.count()

    # =====================================================
    # PRODUCTION SCIENTIFIQUE
    # =====================================================
    total_production_scientifique = (total_articles + total_communications)

    # publications_validees = Publication.objects.filter(statut_indexation="Acceptée").count()

    # publications_attente = Publication.objects.filter(statut_indexation="En attente").count()

    # =====================================================
    # TOP CHERCHEURS
    # =====================================================

    top_chercheurs = user_as_enseignants.order_by("-nbre_publications")[:10]

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        # Table enseignants
        "enseignants": user_as_enseignants,

        # Stats
        "total_enseignants": total_enseignants,
        "total_chercheurs": total_chercheurs,
        "total_publications": 3,
        "enseignants_actifs": enseignants_actifs,
        "enseignants_inactifs": enseignants_inactifs,

        # Publications
        "total_articles": total_articles,
        "total_communications": total_communications,

        # Production scientifique
        "total_production_scientifique": total_production_scientifique,

        # "publications_validees": publications_validees,
        # "publications_attente": publications_attente,

        # Top chercheurs
        "top_chercheurs": top_chercheurs,
    }

    return render(request,"back/institutions/institut_dashboard.html",context)