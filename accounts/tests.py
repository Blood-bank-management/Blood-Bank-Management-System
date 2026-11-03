from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AdminUserManagementAccessTests(TestCase):
    """Part 3.F: only administrators (is_superuser) reach these views."""

    def setUp(self):
        self.admin = User.objects.create_superuser(username="root-admin", password="pass12345", email="a@a.com")
        self.staff = User.objects.create_user(username="plain-staff", password="pass12345", is_staff=True)
        self.donor = User.objects.create_user(username="plain-donor", password="pass12345")

    def test_admin_can_access_user_list(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("accounts:list")).status_code, 200)

    def test_staff_cannot_access_user_list(self):
        """Staff != administrator: ordinary staff must not reach admin-only user management."""
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("accounts:list")).status_code, 403)

    def test_donor_cannot_access_user_list(self):
        self.client.force_login(self.donor)
        self.assertEqual(self.client.get(reverse("accounts:list")).status_code, 403)

    def test_anonymous_redirected_to_login(self):
        self.assertEqual(self.client.get(reverse("accounts:list")).status_code, 302)

    def test_staff_cannot_create_admin_account_via_crafted_post(self):
        """
        Part 3.D: 'ordinary staff cannot create administrator accounts'.
        Even though this endpoint is admin_required (staff gets 403 before
        the view body runs at all), this test nails down that the 403
        happens -- i.e. there is no way for a staff-level POST to reach
        the account-creation code path regardless of what fields it sends.
        """
        self.client.force_login(self.staff)
        response = self.client.post(reverse("accounts:create"), {
            "username": "sneaky", "password1": "x", "password2": "x", "role": "admin",
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username="sneaky").exists())


class AdminUserManagementBehaviorTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="root-admin2", password="pass12345", email="a@a.com")
        self.client.force_login(self.admin)

    def test_create_account_with_role_sets_flags_correctly(self):
        response = self.client.post(reverse("accounts:create"), {
            "username": "newstaff", "password1": "Str0ng-Pass!23", "password2": "Str0ng-Pass!23",
            "email": "s@example.com", "role": "staff",
        })
        user = User.objects.get(username="newstaff")
        self.assertRedirects(response, reverse("accounts:detail", kwargs={"pk": user.pk}))
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_cannot_demote_the_last_active_superuser(self):
        """Part 3.D: 'do not accidentally deactivate the last active superuser' (role version)."""
        response = self.client.post(
            reverse("accounts:detail", kwargs={"pk": self.admin.pk}),
            {"action": "change_role", "role": "staff"}, follow=True,
        )
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_superuser)
        self.assertContains(response, "last active administrator")

    def test_cannot_deactivate_the_last_active_superuser(self):
        response = self.client.post(
            reverse("accounts:detail", kwargs={"pk": self.admin.pk}),
            {"action": "toggle_active"}, follow=True,
        )
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertContains(response, "last active administrator")

    def test_can_deactivate_a_superuser_when_another_remains_active(self):
        other_admin = User.objects.create_superuser(username="root-admin3", password="pass12345", email="b@b.com")
        response = self.client.post(
            reverse("accounts:detail", kwargs={"pk": other_admin.pk}),
            {"action": "toggle_active"},
        )
        other_admin.refresh_from_db()
        self.assertFalse(other_admin.is_active)

    def test_role_change_is_audited(self):
        import auditlog.models as auditlog
        staff_user = User.objects.create_user(username="to-promote", password="pass12345")
        self.client.post(
            reverse("accounts:detail", kwargs={"pk": staff_user.pk}),
            {"action": "change_role", "role": "staff"},
        )
        self.assertTrue(
            auditlog.AuditLog.objects.filter(
                action=auditlog.AuditLog.Action.USER_ROLE_CHANGED, entity_id=str(staff_user.pk),
            ).exists()
        )
