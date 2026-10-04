from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()

USERNAME = "donor_alice"
PASSWORD = "S3cure-Pass!word-42"


class LogoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username=USERNAME, password=PASSWORD)

    def test_auth_ut_06_logout_terminates_session(self):
        """AUTH-UT-06: logout ends the authenticated session."""
        self.client.post(
            reverse("authentication:login"),
            {"username": USERNAME, "password": PASSWORD},
        )
        self.assertIn("_auth_user_id", self.client.session)
        session_key = self.client.session.session_key

        response = self.client.post(reverse("authentication:logout"))

        self.assertRedirects(response, reverse("authentication:login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        # The server-side session record is gone ...
        self.assertFalse(Session.objects.filter(session_key=session_key).exists())
        # ... so protected pages are no longer reachable ...
        home = reverse("authentication:home")
        login_redirect = f"{reverse('authentication:login')}?next={home}"
        self.assertRedirects(self.client.get(home), login_redirect)
        # ... even by replaying the old session cookie.
        replay = Client()
        replay.cookies[settings.SESSION_COOKIE_NAME] = session_key
        self.assertRedirects(replay.get(home), login_redirect)

    def test_auth_ut_17_logout_requires_post(self):
        """AUTH-UT-17: GET does not log the user out."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("authentication:logout"))
        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_auth_ut_18_logout_post_requires_csrf_token(self):
        """AUTH-UT-18: logout POST without a CSRF token is refused."""
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(reverse("authentication:logout"))
        self.assertEqual(response.status_code, 403)
        self.assertIn("_auth_user_id", client.session)

    def test_auth_ut_19_logout_when_anonymous_is_harmless(self):
        """AUTH-UT-19: logging out without a session just redirects to login."""
        response = self.client.post(reverse("authentication:logout"))
        self.assertRedirects(response, reverse("authentication:login"))
