from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()

HOME = reverse("authentication:home")


class ProtectedPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="donor_alice", password="S3cure-Pass!word-42"
        )

    def test_auth_ut_07_unauthenticated_user_cannot_access_protected_page(self):
        """AUTH-UT-07 (SR-001): anonymous requests are redirected to login."""
        response = self.client.get(HOME)
        self.assertRedirects(
            response, f"{reverse('authentication:login')}?next={HOME}"
        )

    def test_auth_ut_08_authenticated_user_can_access_protected_page(self):
        """AUTH-UT-08: a logged-in user can open the protected page."""
        self.client.force_login(self.user)
        response = self.client.get(HOME)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "authentication/home.html")
        self.assertContains(response, "donor_alice")

    def test_protected_page_offers_csrf_protected_logout_form(self):
        self.client.force_login(self.user)
        response = self.client.get(HOME)
        self.assertContains(response, reverse("authentication:logout"))
        self.assertContains(response, "csrfmiddlewaretoken")
