from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustumerUser


@override_settings(SESSION_IDLE_TIMEOUT=1800)
class SessionIdleTimeoutTests(TestCase):
    def setUp(self):
        self.user = CustumerUser.objects.create_user(
            email="idle@test.gn",
            password="MotDePasse123",
            prenoms="Idle",
            nom="User",
            tel="620000099",
        )
        self.keepalive_url = reverse("accounts:session_keepalive")
        self.login_url = reverse("portail_site:connexion")

    def test_activite_enregistre_la_session(self):
        self.client.force_login(self.user)
        response = self.client.get(self.keepalive_url)
        self.assertEqual(response.status_code, 204)
        self.assertIn("last_activity", self.client.session)
        self.assertEqual(self.client.session.get("_auth_user_id"), str(self.user.pk))

    def test_inactivite_deconnecte_et_redirige(self):
        self.client.force_login(self.user)
        session = self.client.session
        session["last_activity"] = timezone.now().timestamp() - 1801
        session.save()

        response = self.client.get(self.keepalive_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("inactivite=1", response.url)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_message_inactivite_sur_la_page_connexion(self):
        response = self.client.get(f"{self.login_url}?inactivite=1")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "déconnecté")
        self.assertContains(response, "inactivité")
