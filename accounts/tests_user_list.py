"""Admin user list search and filters (coverage gap 4.3, BBMS-F-021)."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()
LIST = reverse("accounts:list")


class UserListFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("root_admin", "root@example.com", "S3cure-Pass!word-42")
        User.objects.create_user("alice_staff", "alice@example.com", "S3cure-Pass!word-42", is_staff=True)
        User.objects.create_user("bob_donor", "bob@example.com", "S3cure-Pass!word-42")
        User.objects.create_user("carol_inactive", "carol@example.com", "S3cure-Pass!word-42", is_active=False)

    def _usernames(self, params):
        self.client.force_login(self.admin)
        response = self.client.get(LIST, params)
        self.assertEqual(response.status_code, 200)
        return [u.username for u in response.context["page_obj"].object_list]

    def test_search_matches_username(self):
        self.assertEqual(self._usernames({"q": "alice"}), ["alice_staff"])

    def test_search_matches_email(self):
        self.assertEqual(self._usernames({"q": "bob@example"}), ["bob_donor"])

    def test_role_filter_staff_excludes_admins_and_donors(self):
        self.assertEqual(self._usernames({"role": "staff"}), ["alice_staff"])

    def test_role_filter_admin(self):
        self.assertEqual(self._usernames({"role": "admin"}), ["root_admin"])

    def test_role_filter_donor(self):
        self.assertEqual(self._usernames({"role": "donor"}), ["bob_donor", "carol_inactive"])
