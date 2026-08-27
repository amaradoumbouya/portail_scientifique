from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from accounts.models import CustumerUser
from institutions.models import Institution
from publications.coauteurs import resoudre_auteurs_cites
from publications.models.publication import Publication, PublicationAuteur
from publications.verification_affiliations import (
    apparier_institution,
    normaliser_texte,
    verifier_affiliations_et_auteurs,
)


class AffiliationMatchingTests(TestCase):
    def setUp(self):
        self.uganc = Institution.objects.create(
            nom_institution="Université Gamal Abdel Nasser de Conakry",
            sigle_institution="UGANC",
            email_institution="contact@uganc.edu.gn",
            telephone_institution="620000001",
            adresse_institution="Conakry",
            site_web_institution="https://uganc.edu.gn",
        )

    def test_appariement_par_sigle_et_nom(self):
        institutions = [self.uganc]
        self.assertEqual(
            apparier_institution("UGANC", institutions),
            self.uganc,
        )
        self.assertEqual(
            apparier_institution(
                "Université Gamal Abdel Nasser de Conakry",
                institutions,
            ),
            self.uganc,
        )
        self.assertIsNone(
            apparier_institution("Massachusetts Institute of Technology", institutions)
        )

    def test_normaliser_accents(self):
        self.assertEqual(
            normaliser_texte("Université"),
            normaliser_texte("Universite"),
        )


class VerificationAffiliationsTests(TestCase):
    def setUp(self):
        self.uganc = Institution.objects.create(
            nom_institution="Université Gamal Abdel Nasser de Conakry",
            sigle_institution="UGANC",
            email_institution="contact@uganc.edu.gn",
            telephone_institution="620000001",
            adresse_institution="Conakry",
            site_web_institution="https://uganc.edu.gn",
        )
        self.auteur = CustumerUser.objects.create_user(
            prenoms="Jean",
            nom="Camara",
            email="jean.camara@uganc.edu.gn",
            tel="620000010",
            password="testpass123",
        )
        self.auteur.profile.institution = self.uganc
        self.auteur.profile.role = "enseignant chercheur"
        self.auteur.profile.save()

        self.publication = Publication.objects.create(
            titre="Étude sur la qualité de l'eau",
            type_publication="article",
            user=self.auteur,
            fichier_pdf=SimpleUploadedFile(
                "article.pdf",
                b"%PDF-1.4 test",
                content_type="application/pdf",
            ),
        )
        PublicationAuteur.objects.create(
            publication=self.publication,
            auteur=self.auteur,
            role="Auteur principal",
            ordre=1,
        )
        self.texte_ok = (
            "Jean Camara\n"
            "Université Gamal Abdel Nasser de Conakry (UGANC)\n"
            "Abstract\n"
            "Cette étude analyse la qualité de l'eau en Guinée."
        )

    def test_acceptation_si_institution_inscrite_et_auteur_affilie(self):
        resultat = verifier_affiliations_et_auteurs(
            self.publication,
            texte_pdf=self.texte_ok,
            meta_externes={"auteurs": [], "affiliations": []},
        )
        self.assertEqual(resultat["statut"], "Acceptée")
        self.assertEqual(resultat["motif"], "")

    def test_rejet_si_auteur_sans_institution(self):
        self.auteur.profile.institution = None
        self.auteur.profile.save()
        resultat = verifier_affiliations_et_auteurs(
            self.publication,
            texte_pdf=self.texte_ok,
            meta_externes={"auteurs": [], "affiliations": []},
        )
        self.assertEqual(resultat["statut"], "Rejetée")
        self.assertIn("aucune institution", resultat["motif"].lower())
        self.assertIn("Jean Camara", resultat["motif"])

    def test_rejet_si_aucune_institution_inscrite_citee(self):
        resultat = verifier_affiliations_et_auteurs(
            self.publication,
            texte_pdf=(
                "Jean Camara\n"
                "Massachusetts Institute of Technology\n"
                "Abstract\n"
                "A study on water quality."
            ),
            meta_externes={
                "auteurs": [],
                "affiliations": ["Massachusetts Institute of Technology"],
            },
        )
        self.assertEqual(resultat["statut"], "Rejetée")
        self.assertIn("inscrite sur la plateforme", resultat["motif"])
        self.assertIn("Massachusetts Institute of Technology", resultat["motif"])

    def test_rejet_affiliation_etrangere_meme_si_institution_locale_citee(self):
        resultat = verifier_affiliations_et_auteurs(
            self.publication,
            texte_pdf=(
                "Jean Camara, Alice Smith\n"
                "Université Gamal Abdel Nasser de Conakry ; MIT\n"
                "Abstract\n"
                "Collaborative study."
            ),
            meta_externes={
                "auteurs": [
                    {
                        "prenoms": "Jean",
                        "nom": "Camara",
                        "affiliations": ["Université Gamal Abdel Nasser de Conakry"],
                    },
                    {
                        "prenoms": "Alice",
                        "nom": "Smith",
                        "affiliations": ["Massachusetts Institute of Technology"],
                    },
                ],
                "affiliations": [
                    "Université Gamal Abdel Nasser de Conakry",
                    "Massachusetts Institute of Technology",
                ],
            },
        )
        self.assertEqual(resultat["statut"], "Rejetée")
        self.assertIn("règle nationale stricte", resultat["motif"])
        self.assertIn("Massachusetts Institute of Technology", resultat["motif"])

    def test_rejet_si_auteur_non_affilie_aux_institutions_citees(self):
        autre = Institution.objects.create(
            nom_institution="Centre de Recherche Scientifique de Kindia",
            sigle_institution="CRSK",
            email_institution="contact@crsk.edu.gn",
            telephone_institution="620000002",
            adresse_institution="Kindia",
            site_web_institution="https://crsk.edu.gn",
        )
        self.auteur.profile.institution = autre
        self.auteur.profile.save()
        resultat = verifier_affiliations_et_auteurs(
            self.publication,
            texte_pdf=self.texte_ok,
            meta_externes={
                "affiliations": ["Université Gamal Abdel Nasser de Conakry"],
                "auteurs": [],
            },
        )
        self.assertEqual(resultat["statut"], "Rejetée")
        self.assertIn("ne sont pas affiliés aux institutions citées", resultat["motif"])


class IndexerDeuxNiveauxTests(TestCase):
    def setUp(self):
        self.uganc = Institution.objects.create(
            nom_institution="Université Gamal Abdel Nasser de Conakry",
            sigle_institution="UGANC",
            email_institution="contact@uganc.edu.gn",
            telephone_institution="620000001",
            adresse_institution="Conakry",
            site_web_institution="https://uganc.edu.gn",
        )
        self.auteur = CustumerUser.objects.create_user(
            prenoms="Jean",
            nom="Camara",
            email="jean.camara@uganc.edu.gn",
            tel="620000010",
            password="testpass123",
        )
        self.publication = Publication.objects.create(
            titre="Article sans affiliation valide",
            type_publication="article",
            user=self.auteur,
            fichier_pdf=SimpleUploadedFile(
                "article.pdf",
                b"%PDF-1.4 test",
                content_type="application/pdf",
            ),
        )
        PublicationAuteur.objects.create(
            publication=self.publication,
            auteur=self.auteur,
            role="Auteur principal",
            ordre=1,
        )

    def test_rejet_affiliations_n_interroge_pas_scopus(self):
        with patch(
            "publications.nlp_tools.extraire_texte_du_pdf",
            return_value="Texte trop court.",
        ), patch(
            "publications.nlp_tools.enrichir_meta_depuis_doi",
            return_value={"auteurs": [], "affiliations": []},
        ), patch(
            "publications.nlp_tools.verifier_indexation_internationale",
        ) as mock_scopus:
            self.publication.indexer(self.publication.fichier_pdf)

        mock_scopus.assert_not_called()
        self.assertEqual(self.publication.statut_indexation, "Rejetée")
        self.assertFalse(self.publication.statut_publication)
        self.assertIn("vérification des affiliations", self.publication.motif_rejet.lower())


class CoauteursDepuisArticleTests(TestCase):
    def setUp(self):
        self.uganc = Institution.objects.create(
            nom_institution="Université Gamal Abdel Nasser de Conakry",
            sigle_institution="UGANC",
            email_institution="contact@uganc.edu.gn",
            telephone_institution="620000001",
            adresse_institution="Conakry",
            site_web_institution="https://uganc.edu.gn",
        )
        self.deposant = CustumerUser.objects.create_user(
            prenoms="Jean",
            nom="Camara",
            email="jean.camara@uganc.edu.gn",
            tel="620000010",
            password="testpass123",
        )
        self.deposant.profile.institution = self.uganc
        self.deposant.profile.save()
        self.existant = CustumerUser.objects.create_user(
            prenoms="Mamadou",
            nom="Bah",
            email="mamadou.bah@uganc.edu.gn",
            tel="620000020",
            password="testpass123",
        )
        self.existant.profile.institution = self.uganc
        self.existant.profile.save()

    def test_coauteur_inscrit_est_relie(self):
        analyse = resoudre_auteurs_cites(
            meta_externes={
                "auteurs": [
                    {"prenoms": "Jean", "nom": "Camara", "affiliations": ["UGANC"]},
                    {
                        "prenoms": "Mamadou",
                        "nom": "Bah",
                        "affiliations": ["Université Gamal Abdel Nasser de Conakry"],
                    },
                ],
            },
            deposant=self.deposant,
        )
        self.assertEqual(analyse["rejets"], [])
        self.assertEqual(len(analyse["existants"]), 1)
        self.assertEqual(analyse["existants"][0]["user"], self.existant)
        self.assertEqual(analyse["a_creer"], [])

    def test_inscrit_sans_institution_est_rejete(self):
        self.existant.profile.institution = None
        self.existant.profile.save()
        analyse = resoudre_auteurs_cites(
            meta_externes={
                "auteurs": [
                    {"prenoms": "Mamadou", "nom": "Bah", "affiliations": ["UGANC"]},
                ],
            },
            deposant=self.deposant,
        )
        self.assertTrue(analyse["rejets"])
        self.assertEqual(analyse["existants"], [])
        self.assertIn("aucune institution", analyse["rejets"][0])

    def test_auteur_non_inscrit_n_est_pas_cree(self):
        analyse = resoudre_auteurs_cites(
            meta_externes={
                "auteurs": [
                    {
                        "prenoms": "Alice",
                        "nom": "Smith",
                        "affiliations": ["Massachusetts Institute of Technology"],
                    },
                ],
            },
            deposant=self.deposant,
        )
        self.assertTrue(analyse["rejets"])
        self.assertEqual(analyse["a_creer"], [])
        self.assertFalse(
            CustumerUser.objects.filter(nom__iexact="Smith").exists()
        )
        self.assertIn("n'a pas de compte", analyse["rejets"][0])
        self.assertIn("Aucun compte n'a été créé", analyse["rejets"][0])
