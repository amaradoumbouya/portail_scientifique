from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.utils.crypto import get_random_string


class ProjetEtude(models.Model):

    class TypeProjet(models.TextChoices):
        MEMOIRE = "memoire", "Mémoire"
        THESE = "these", "Thèse"

    class StatutProjet(models.TextChoices):
        SOUMIS = "soumis", "Soumis"
        EN_COURS = "en_cours", "En cours"
        EN_REVUE = "en_revue", "En revue"
        VALIDE = "valide", "Validé"
        TERMINE = "termine", "Terminé"
        REJETE = "rejete", "Rejeté"

    type_projet     = models.CharField(max_length=20, choices=TypeProjet.choices)
    titre           = models.CharField(max_length=255, verbose_name="Titre du projet")
    description     = models.TextField(verbose_name="Description du projet")
    createur        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    candidate       = models.ForeignKey("projets_detudes.Candidate", on_delete=models.CASCADE, related_name="etudiant")
    statut          = models.CharField(
        max_length=20,
        choices=StatutProjet.choices,
        default=StatutProjet.SOUMIS,
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    slug            = models.SlugField(max_length=255, unique=True, editable=False, blank=True, null=True)
    date_soumission = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titre) + '-' + get_random_string(5)
        super().save(*args, **kwargs)

    def _changer_statut(self, nouveau_statut, *, set_date_validation=False):
        """Applique un statut si différent ; retourne True si modifié."""
        if self.statut == nouveau_statut:
            return False
        self.statut = nouveau_statut
        update_fields = ['statut', 'updated_at']
        if set_date_validation:
            self.date_validation = timezone.now()
            update_fields.append('date_validation')
        self.save(update_fields=update_fields)
        return True

    def passer_en_cours(self):
        """soumis → en_cours (1er encadrant qui accepte)."""
        if self.statut != self.StatutProjet.SOUMIS:
            return False
        return self._changer_statut(self.StatutProjet.EN_COURS)

    def passer_en_revue(self):
        """en_cours (ou soumis) → en_revue (demande de soutenance)."""
        if self.statut not in (self.StatutProjet.SOUMIS, self.StatutProjet.EN_COURS):
            return False
        return self._changer_statut(self.StatutProjet.EN_REVUE)

    def passer_en_valide(self):
        """en_revue → valide (soutenance planifiée / validation)."""
        if self.statut not in (
            self.StatutProjet.EN_REVUE,
            self.StatutProjet.EN_COURS,
        ):
            return False
        return self._changer_statut(self.StatutProjet.VALIDE, set_date_validation=True)

    def passer_en_termine(self):
        """valide → termine (délibération enregistrée)."""
        if self.statut not in (self.StatutProjet.VALIDE, self.StatutProjet.EN_REVUE):
            return False
        return self._changer_statut(self.StatutProjet.TERMINE)

    def passer_en_rejete(self):
        """soumis / en_cours → rejeté (refus du directeur)."""
        if self.statut not in (self.StatutProjet.SOUMIS, self.StatutProjet.EN_COURS):
            return False
        return self._changer_statut(self.StatutProjet.REJETE)

    _ORDRE_STATUTS = (
        StatutProjet.SOUMIS,
        StatutProjet.EN_COURS,
        StatutProjet.EN_REVUE,
        StatutProjet.VALIDE,
        StatutProjet.TERMINE,
    )

    def _rang_statut(self, statut):
        try:
            return self._ORDRE_STATUTS.index(statut)
        except ValueError:
            return -1

    def synchroniser_apres_reponse_invitation(self, participant, action):
        """
        Met à jour le statut après acceptation / refus d'un encadrant.
        - acceptation → en_cours
        - refus du directeur (sans autre directeur accepté) → rejeté
        """
        from projets_detudes.models.participant import Participant

        roles_encadrant = (
            Participant.Role.DIRECTEUR,
            Participant.Role.CO_DIRECTEUR,
            "Co-Directeur",
        )

        if participant.role not in roles_encadrant:
            return False

        if action == Participant.Statut.ACCEPTE:
            return self.passer_en_cours()

        if action == Participant.Statut.REFUSE and participant.role in (
            Participant.Role.DIRECTEUR,
            "Directeur",
        ):
            autre_directeur_accepte = (
                Participant.objects.filter(
                    projet=self,
                    role=Participant.Role.DIRECTEUR,
                    has_accepted=Participant.Statut.ACCEPTE,
                )
                .exclude(pk=participant.pk)
                .exists()
            )
            if not autre_directeur_accepte:
                return self.passer_en_rejete()

        return False

    def rafraichir_statut_depuis_relations(self):
        """
        Aligne le statut sur l'état réel du projet (progression uniquement).
        Corrige les cas où un encadrant a accepté mais le statut est resté « soumis ».
        """
        from projets_detudes.models.participant import Participant

        try:
            from soutenance.models.soutenance import DemandeSoutenance, Soutenance
            from soutenance.models.deliberation_soutenance import DeliberationSoutenance
        except Exception:
            DemandeSoutenance = Soutenance = DeliberationSoutenance = None

        roles_encadrant = (
            Participant.Role.DIRECTEUR,
            Participant.Role.CO_DIRECTEUR,
            "Co-Directeur",
        )

        # Cible calculée d'après les faits
        cible = self.StatutProjet.SOUMIS

        encadrants_acceptes = self.projet.filter(
            role__in=roles_encadrant,
            has_accepted=Participant.Statut.ACCEPTE,
        ).exists()
        if encadrants_acceptes:
            cible = self.StatutProjet.EN_COURS

        if DemandeSoutenance is not None:
            demande = (
                DemandeSoutenance.objects.filter(projet=self)
                .exclude(statut="Rejetée")
                .first()
            )
            if demande:
                if demande.statut == "Acceptée" or (
                    Soutenance is not None
                    and Soutenance.objects.filter(projet=self).exists()
                ):
                    cible = self.StatutProjet.VALIDE
                else:
                    cible = self.StatutProjet.EN_REVUE

            if (
                DeliberationSoutenance is not None
                and DeliberationSoutenance.objects.filter(soutenance__projet=self).exists()
            ):
                cible = self.StatutProjet.TERMINE

        # Rejet : directeur a refusé et aucun encadrant accepté
        if not encadrants_acceptes and self.statut in (
            self.StatutProjet.SOUMIS,
            self.StatutProjet.EN_COURS,
        ):
            directeur_refuse = self.projet.filter(
                role=Participant.Role.DIRECTEUR,
                has_accepted=Participant.Statut.REFUSE,
            ).exists()
            if directeur_refuse:
                return self._changer_statut(self.StatutProjet.REJETE)

        # Progression seulement (ne pas reculer)
        if self._rang_statut(cible) > self._rang_statut(self.statut):
            return self._changer_statut(
                cible,
                set_date_validation=(cible == self.StatutProjet.VALIDE and not self.date_validation),
            )

        return False
