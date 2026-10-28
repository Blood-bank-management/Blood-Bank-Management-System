from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import DonorProfile

User = get_user_model()

VALID_DOB = date.today() - timedelta(days=365 * 25)

REGISTRATION_DATA = {
    "first_name": "Asha",
    "last_name": "Rao",
    "username": "asha_rao",
    "email": "asha.rao@example.com",
    "phone_number": "+91 98765 43210",
    "date_of_birth": VALID_DOB.isoformat(),
    "blood_group": "O+",
    "address": "12 MG Road, Bengaluru",
    "password1": "S3cure-Pass!word-42",
    "password2": "S3cure-Pass!word-42",
}


# ---------------------------------------------------------------------------
# BBMS-F-003: donor self-registration
# ---------------------------------------------------------------------------
class DonorRegistrationTests(TestCase):
    def test_donor_ut_01_valid_registration_creates_user_and_profile(self):
        response = self.client.post(reverse("donors:register"), REGISTRATION_DATA)

        user = User.objects.get(username="asha_rao")
        self.assertRedirects(response, reverse("authentication:home"))
        self.assertTrue(hasattr(user, "donor_profile"))
        self.assertEqual(user.donor_profile.blood_group, "O+")

    def test_donor_ut_02_registration_grants_minimum_privilege_role(self):
        """A self-registered account is never staff or superuser (BBMS-SR-002)."""
        self.client.post(reverse("donors:register"), REGISTRATION_DATA)
        user = User.objects.get(username="asha_rao")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_donor_ut_03_registration_logs_the_user_in(self):
        response = self.client.post(reverse("donors:register"), REGISTRATION_DATA)
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            User.objects.get(username="asha_rao").pk,
        )

    def test_donor_ut_04_duplicate_username_rejected(self):
        User.objects.create_user(username="asha_rao", password="whatever-1")
        response = self.client.post(reverse("donors:register"), REGISTRATION_DATA)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already taken")
        self.assertEqual(DonorProfile.objects.count(), 0)

    def test_donor_ut_05_duplicate_email_rejected(self):
        User.objects.create_user(
            username="someone-else", email="asha.rao@example.com", password="whatever-1"
        )
        response = self.client.post(reverse("donors:register"), REGISTRATION_DATA)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        self.assertEqual(User.objects.filter(username="asha_rao").count(), 0)

    def test_donor_ut_06_missing_required_fields_rejected(self):
        response = self.client.post(reverse("donors:register"), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.assertEqual(User.objects.count(), 0)

    def test_donor_ut_07_mismatched_passwords_rejected(self):
        data = {**REGISTRATION_DATA, "password2": "something-different-99"}
        response = self.client.post(reverse("donors:register"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "did not match")
        self.assertEqual(User.objects.count(), 0)

    def test_donor_ut_08_weak_password_rejected_by_shared_validators(self):
        """Reuses AUTH_PASSWORD_VALIDATORS (BBMS-SR-004 groundwork)."""
        data = {**REGISTRATION_DATA, "password1": "1234", "password2": "1234"}
        response = self.client.post(reverse("donors:register"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)

    def test_donor_ut_09_future_date_of_birth_rejected(self):
        future = (date.today() + timedelta(days=10)).isoformat()
        data = {**REGISTRATION_DATA, "date_of_birth": future}
        response = self.client.post(reverse("donors:register"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "must be in the past")
        self.assertEqual(User.objects.count(), 0)

    def test_donor_ut_10_password_is_hashed(self):
        self.client.post(reverse("donors:register"), REGISTRATION_DATA)
        user = User.objects.get(username="asha_rao")
        self.assertNotEqual(user.password, REGISTRATION_DATA["password1"])
        self.assertTrue(user.check_password(REGISTRATION_DATA["password1"]))

    def test_donor_ut_11_already_authenticated_user_is_redirected(self):
        user = User.objects.create_user(username="existing", password="whatever-1")
        self.client.force_login(user)
        response = self.client.get(reverse("donors:register"))
        self.assertRedirects(response, reverse("authentication:home"))


# ---------------------------------------------------------------------------
# BBMS-F-004: donor self-service profile
# ---------------------------------------------------------------------------
class DonorProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="donor_bob", email="bob@example.com", password="S3cure-Pass!word-42",
        )
        self.profile = DonorProfile.objects.create(
            user=self.user,
            phone_number="9876543210",
            date_of_birth=VALID_DOB,
            blood_group="B+",
            address="Old address",
        )
        self.other_user = User.objects.create_user(username="donor_carol", password="whatever-1")
        self.other_profile = DonorProfile.objects.create(
            user=self.other_user, phone_number="1112223333",
            date_of_birth=VALID_DOB, blood_group="A-", address="Carol's address",
        )

    def test_donor_ut_12_anonymous_cannot_view_profile(self):
        response = self.client.get(reverse("donors:profile"))
        self.assertRedirects(
            response, f"{reverse('authentication:login')}?next={reverse('donors:profile')}"
        )

    def test_donor_ut_13_donor_can_view_own_profile(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("donors:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Old address")

    def test_donor_ut_14_donor_can_update_own_profile(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("donors:profile"), {
            "first_name": "Bob", "last_name": "Singh", "email": "bob.new@example.com",
            "phone_number": "9999999999", "date_of_birth": VALID_DOB.isoformat(),
            "blood_group": "B+", "address": "New address",
        })
        self.assertRedirects(response, reverse("donors:profile"))
        self.profile.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.profile.address, "New address")
        self.assertEqual(self.user.email, "bob.new@example.com")

    def test_donor_ut_15_profile_form_has_no_eligibility_field(self):
        """A donor cannot change their own eligibility -- the field is not on the form."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("donors:profile"))
        self.assertNotContains(response, 'name="eligibility_status"')

    def test_donor_ut_16_posting_an_eligibility_value_to_profile_is_ignored(self):
        """Even if a client crafts the field name by hand, profile() cannot act on it."""
        self.client.force_login(self.user)
        self.client.post(reverse("donors:profile"), {
            "first_name": "Bob", "last_name": "X", "email": "bob@example.com",
            "phone_number": "9876543210", "date_of_birth": VALID_DOB.isoformat(),
            "blood_group": "B+", "address": "Old address",
            "eligibility_status": DonorProfile.Eligibility.TEMPORARILY_INELIGIBLE,
        })
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.eligibility_status, DonorProfile.Eligibility.ELIGIBLE)

    def test_donor_ut_17_profile_view_has_no_id_parameter_to_tamper_with(self):
        """
        IDOR check: donors:profile always resolves to one URL with no id/pk,
        so there is nothing in the request that could be swapped to reach
        another donor's data through this view.
        """
        self.assertNotIn("pk", reverse("donors:profile"))
        self.client.force_login(self.user)
        response = self.client.get(reverse("donors:profile"))
        self.assertNotContains(response, "Carol's address")


# ---------------------------------------------------------------------------
# BBMS-F-005 / BBMS-F-006: staff donor list, detail and eligibility
# ---------------------------------------------------------------------------
class StaffDonorManagementTests(TestCase):
    def setUp(self):
        self.donor_user = User.objects.create_user(username="donor_dave", password="whatever-1")
        self.donor_profile = DonorProfile.objects.create(
            user=self.donor_user, phone_number="1234567890",
            date_of_birth=VALID_DOB, blood_group="AB+", address="Dave's address",
        )
        self.staff_user = User.objects.create_user(
            username="staff_emma", password="whatever-1", is_staff=True,
        )
        self.other_donor_user = User.objects.create_user(username="donor_frank", password="whatever-1")

    # --- RBAC: donor_list ---
    def test_donor_ut_18_anonymous_cannot_list_donors(self):
        response = self.client.get(reverse("donors:list"))
        self.assertRedirects(
            response, f"{reverse('authentication:login')}?next={reverse('donors:list')}"
        )

    def test_donor_ut_19_donor_role_forbidden_from_donor_list(self):
        """BBMS-SR-002: a donor account cannot reach a staff-only page."""
        self.client.force_login(self.donor_user)
        response = self.client.get(reverse("donors:list"))
        self.assertEqual(response.status_code, 403)

    def test_donor_ut_20_staff_can_list_donors(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("donors:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "donor_dave")

    def test_donor_ut_21_donor_list_search_filters_by_field(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("donors:list"), {"q": "AB+"})
        self.assertContains(response, "donor_dave")

    # --- RBAC + IDOR: donor_detail ---
    def test_donor_ut_22_anonymous_cannot_view_donor_detail(self):
        url = reverse("donors:detail", kwargs={"pk": self.donor_profile.pk})
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('authentication:login')}?next={url}")

    def test_donor_ut_23_donor_role_forbidden_from_any_donor_detail_including_their_own(self):
        """
        IDOR / RBAC: donor_detail is a staff tool. A donor account is
        rejected by role before pk is even looked at -- including when pk
        happens to be their own profile. The access check does not depend
        on which pk was guessed.
        """
        own_url = reverse("donors:detail", kwargs={"pk": self.donor_profile.pk})
        self.client.force_login(self.donor_user)
        self.assertEqual(self.client.get(own_url).status_code, 403)

        other_profile = DonorProfile.objects.create(
            user=self.other_donor_user, phone_number="5555555555",
            date_of_birth=VALID_DOB, blood_group="O-", address="Frank's address",
        )
        other_url = reverse("donors:detail", kwargs={"pk": other_profile.pk})
        self.assertEqual(self.client.get(other_url).status_code, 403)

    def test_donor_ut_24_nonexistent_donor_pk_returns_404_not_500(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("donors:detail", kwargs={"pk": 999999}))
        self.assertEqual(response.status_code, 404)

    def test_donor_ut_25_staff_can_view_any_donor_detail(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("donors:detail", kwargs={"pk": self.donor_profile.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dave&#x27;s address")

    # --- BBMS-F-006: eligibility ---
    def test_donor_ut_26_staff_can_update_eligibility_with_audit_fields(self):
        self.client.force_login(self.staff_user)
        url = reverse("donors:detail", kwargs={"pk": self.donor_profile.pk})
        response = self.client.post(url, {
            "eligibility_status": DonorProfile.Eligibility.TEMPORARILY_INELIGIBLE,
            "note": "Recent donation, 90-day deferral.",
        })
        self.assertRedirects(response, url)
        self.donor_profile.refresh_from_db()
        self.assertEqual(
            self.donor_profile.eligibility_status,
            DonorProfile.Eligibility.TEMPORARILY_INELIGIBLE,
        )
        self.assertEqual(self.donor_profile.eligibility_updated_by, self.staff_user)
        self.assertIsNotNone(self.donor_profile.eligibility_updated_at)

    def test_donor_ut_27_donor_cannot_post_eligibility_change(self):
        self.client.force_login(self.donor_user)
        url = reverse("donors:detail", kwargs={"pk": self.donor_profile.pk})
        response = self.client.post(url, {
            "eligibility_status": DonorProfile.Eligibility.TEMPORARILY_INELIGIBLE,
            "note": "Self-escalation attempt.",
        })
        self.assertEqual(response.status_code, 403)
        self.donor_profile.refresh_from_db()
        self.assertEqual(self.donor_profile.eligibility_status, DonorProfile.Eligibility.ELIGIBLE)
        self.assertIsNone(self.donor_profile.eligibility_updated_by)

    def test_donor_ut_28_eligibility_update_requires_csrf_token(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.staff_user)
        url = reverse("donors:detail", kwargs={"pk": self.donor_profile.pk})
        response = client.post(url, {
            "eligibility_status": DonorProfile.Eligibility.TEMPORARILY_INELIGIBLE,
        })
        self.assertEqual(response.status_code, 403)


# ---------------------------------------------------------------------------
# Integration: full donor lifecycle across authentication + donors + inventory
# ---------------------------------------------------------------------------
class DonorIntegrationWorkflowTests(TestCase):
    def test_register_login_profile_staff_review_eligibility_workflow(self):
        # 1. Register.
        response = self.client.post(reverse("donors:register"), REGISTRATION_DATA)
        self.assertRedirects(response, reverse("authentication:home"))
        donor_user = User.objects.get(username="asha_rao")

        # 2. Registration logs the donor in automatically; home page greets them.
        home = self.client.get(reverse("authentication:home"))
        self.assertContains(home, "asha_rao")
        self.assertContains(home, "Donor")  # role badge

        # 3. Donor can see and edit their own profile, but not eligibility.
        profile_page = self.client.get(reverse("donors:profile"))
        self.assertContains(profile_page, "12 MG Road")
        self.assertNotContains(profile_page, 'name="eligibility_status"')

        # 4. Donor cannot reach the staff donor list or their own staff-view detail page.
        self.assertEqual(self.client.get(reverse("donors:list")).status_code, 403)
        detail_url = reverse("donors:detail", kwargs={"pk": donor_user.donor_profile.pk})
        self.assertEqual(self.client.get(detail_url).status_code, 403)

        # 5. Log out; protected pages become inaccessible again.
        self.client.post(reverse("authentication:logout"))
        self.assertEqual(self.client.get(reverse("donors:profile")).status_code, 302)

        # 6. Staff logs in, finds the new donor in the list, opens their record.
        staff_user = User.objects.create_user(username="staff_lead", password="whatever-1", is_staff=True)
        self.client.force_login(staff_user)
        listing = self.client.get(reverse("donors:list"))
        self.assertContains(listing, "asha_rao")

        detail = self.client.get(detail_url)
        self.assertContains(detail, "12 MG Road")

        # 7. Staff marks the donor temporarily ineligible after a recent donation.
        response = self.client.post(detail_url, {
            "eligibility_status": DonorProfile.Eligibility.TEMPORARILY_INELIGIBLE,
            "note": "Donated 2 weeks ago; eligible again after 90 days.",
        })
        self.assertRedirects(response, detail_url)

        # 8. The donor sees their own updated status on their own profile page.
        self.client.logout()
        self.client.force_login(donor_user)
        profile_page = self.client.get(reverse("donors:profile"))
        self.assertContains(profile_page, "Temporarily ineligible")

        # 9. The donor still cannot clear the flag themselves.
        response = self.client.post(detail_url, {
            "eligibility_status": DonorProfile.Eligibility.ELIGIBLE,
        })
        self.assertEqual(response.status_code, 403)
        donor_user.donor_profile.refresh_from_db()
        self.assertEqual(
            donor_user.donor_profile.eligibility_status,
            DonorProfile.Eligibility.TEMPORARILY_INELIGIBLE,
        )
