from django.contrib.auth import authenticate, get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()

USERNAME = "donor_alice"
EMAIL = "alice@example.com"
PASSWORD = "S3cure-Pass!word-42"


class LoginTestCase(TestCase):
    """Shared fixtures and helpers for login tests."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username=USERNAME, email=EMAIL, password=PASSWORD
        )

    def post_login(self, identifier, password, client=None, **extra):
        client = client or self.client
        data = {"username": identifier, "password": password, **extra}
        return client.post(reverse("authentication:login"), data)

    def assertNotLoggedIn(self):
        self.assertNotIn("_auth_user_id", self.client.session)

    def assertLoggedInAs(self, user):
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)


class ValidLoginTests(LoginTestCase):
    def test_auth_ut_01_valid_credentials_authenticate(self):
        """AUTH-UT-01: valid credentials authenticate successfully."""
        self.assertEqual(authenticate(username=USERNAME, password=PASSWORD), self.user)

    def test_auth_ut_01_valid_credentials_log_the_user_in(self):
        """AUTH-UT-01: posting valid credentials starts a session and redirects."""
        response = self.post_login(USERNAME, PASSWORD)
        self.assertRedirects(response, reverse("authentication:home"))
        self.assertLoggedInAs(self.user)

    def test_auth_ut_09_login_with_email(self):
        """AUTH-UT-09: login works with the e-mail address (case-insensitive)."""
        response = self.post_login("Alice@EXAMPLE.com", PASSWORD)
        self.assertRedirects(response, reverse("authentication:home"))
        self.assertLoggedInAs(self.user)

    def test_login_page_renders_with_csrf_token(self):
        response = self.client.get(reverse("authentication:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "authentication/login.html")
        self.assertContains(response, "csrfmiddlewaretoken")


class InvalidLoginTests(LoginTestCase):
    def test_auth_ut_02_invalid_password_rejected(self):
        """AUTH-UT-02: wrong password is rejected."""
        response = self.post_login(USERNAME, "wrong-password")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "authentication/login.html")
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertNotLoggedIn()
        self.assertIsNone(authenticate(username=USERNAME, password="wrong-password"))

    def test_auth_ut_03_invalid_username_rejected(self):
        """AUTH-UT-03: unknown username is rejected."""
        response = self.post_login("nobody", PASSWORD)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertNotLoggedIn()

    def test_auth_ut_03_invalid_email_rejected(self):
        """AUTH-UT-03: unknown e-mail address is rejected."""
        response = self.post_login("nobody@example.com", PASSWORD)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertNotLoggedIn()

    def test_auth_ut_04_empty_username_rejected(self):
        """AUTH-UT-04: empty username/email is rejected."""
        response = self.post_login("", PASSWORD)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"], "username", "This field is required."
        )
        self.assertNotLoggedIn()

    def test_auth_ut_05_empty_password_rejected(self):
        """AUTH-UT-05: empty password is rejected."""
        response = self.post_login(USERNAME, "")
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"], "password", "This field is required."
        )
        self.assertNotLoggedIn()

    def test_auth_ut_10_ambiguous_email_rejected(self):
        """AUTH-UT-10: an e-mail shared by several accounts cannot be used to log in."""
        User.objects.create_user(
            username="alice_two", email=EMAIL, password=PASSWORD
        )
        response = self.post_login(EMAIL, PASSWORD)
        self.assertEqual(response.status_code, 200)
        self.assertNotLoggedIn()
        # Each account can still log in with its own username.
        response = self.post_login("alice_two", PASSWORD)
        self.assertRedirects(response, reverse("authentication:home"))

    def test_auth_ut_11_inactive_user_rejected(self):
        """AUTH-UT-11: a deactivated account cannot log in."""
        User.objects.create_user(
            username="inactive", email="inactive@example.com",
            password=PASSWORD, is_active=False,
        )
        for identifier in ("inactive", "inactive@example.com"):
            with self.subTest(identifier=identifier):
                response = self.post_login(identifier, PASSWORD)
                self.assertEqual(response.status_code, 200)
                self.assertNotLoggedIn()


class LoginSecurityTests(LoginTestCase):
    def test_auth_ut_12_password_is_hashed_not_plaintext(self):
        """AUTH-UT-12: passwords are stored hashed (SR-004 groundwork)."""
        stored = User.objects.get(pk=self.user.pk).password
        self.assertNotEqual(stored, PASSWORD)
        self.assertNotIn(PASSWORD, stored)
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_auth_ut_13_login_post_requires_csrf_token(self):
        """AUTH-UT-13: login POST without a CSRF token is refused."""
        client = Client(enforce_csrf_checks=True)
        response = self.post_login(USERNAME, PASSWORD, client=client)
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("_auth_user_id", client.session)

    def test_auth_ut_14_safe_next_url_is_honoured(self):
        """AUTH-UT-14: a same-site ?next target is followed after login."""
        response = self.post_login(USERNAME, PASSWORD, next="/admin/")
        self.assertRedirects(response, "/admin/", fetch_redirect_response=False)

    def test_auth_ut_15_external_next_url_is_ignored(self):
        """AUTH-UT-15: an off-site ?next target is ignored (no open redirect)."""
        response = self.post_login(USERNAME, PASSWORD, next="https://evil.example/")
        self.assertRedirects(response, reverse("authentication:home"))

    def test_auth_ut_16_logged_in_user_is_redirected_from_login_page(self):
        """AUTH-UT-16: an already authenticated user is sent to the landing page."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("authentication:login"))
        self.assertRedirects(response, reverse("authentication:home"))
