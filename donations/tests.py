from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from donors.models import DonorProfile
from inventory.models import BloodInventory
from .models import Donation
from .services import DuplicateDonationError, record_donation

User = get_user_model()


def _make_donor(username="donor1"):
    user = User.objects.create_user(username=username, password="pass12345")
    return DonorProfile.objects.create(
        user=user, phone_number="+1 555-0100", date_of_birth=date(1995, 1, 1),
        blood_group="O+", address="1 Main St",
    )


class DonationServiceTests(TestCase):
    """Unit tests: donation model/service validation (Part 5.A)."""

    def setUp(self):
        self.donor = _make_donor()
        self.staff = User.objects.create_user(username="staff1", password="pass12345", is_staff=True)

    def test_record_donation_creates_donation_and_credits_inventory(self):
        """Integration: donation creation -> inventory increase (Part 5.B)."""
        donation = record_donation(
            donor=self.donor, blood_group="O+", quantity=2,
            collection_date=date.today(), collection_reference="REF-001",
            recorded_by=self.staff,
        )
        self.assertTrue(donation.is_successful)
        batch = BloodInventory.objects.get(source_donation=donation)
        self.assertEqual(batch.quantity_remaining, 2)
        self.assertEqual(batch.blood_group, "O+")

    def test_rejected_donation_does_not_credit_inventory(self):
        """Part 3.A.2: rejected donations never become available stock."""
        record_donation(
            donor=self.donor, blood_group="O+", quantity=2,
            collection_date=date.today(), collection_reference="REF-002",
            recorded_by=self.staff, status=Donation.Status.REJECTED,
            rejection_reason="Low hemoglobin",
        )
        self.assertEqual(BloodInventory.objects.count(), 0)

    def test_duplicate_collection_reference_is_rejected(self):
        """Part 3.A.2: prevent duplicate inventory credit on form resubmission."""
        record_donation(
            donor=self.donor, blood_group="O+", quantity=2,
            collection_date=date.today(), collection_reference="REF-003",
            recorded_by=self.staff,
        )
        with self.assertRaises(DuplicateDonationError):
            record_donation(
                donor=self.donor, blood_group="O+", quantity=2,
                collection_date=date.today(), collection_reference="REF-003",
                recorded_by=self.staff,
            )
        # Only one batch was ever credited -- not two.
        self.assertEqual(BloodInventory.objects.count(), 1)

    def test_donation_quantity_must_be_positive(self):
        donation = Donation(
            donor=self.donor, blood_group="O+", quantity=0,
            collection_date=date.today(), collection_reference="REF-004",
            recorded_by=self.staff,
        )
        with self.assertRaises(ValidationError):
            donation.full_clean()

    def test_donation_collection_date_cannot_be_future(self):
        donation = Donation(
            donor=self.donor, blood_group="O+", quantity=1,
            collection_date=date.today() + timedelta(days=1),
            collection_reference="REF-005", recorded_by=self.staff,
        )
        with self.assertRaises(ValidationError):
            donation.full_clean()


class DonationViewAccessTests(TestCase):
    """Part 3.F: allowed and denied access for donation views."""

    def setUp(self):
        self.donor_profile = _make_donor("donor2")
        self.other_donor_profile = _make_donor("donor3")
        self.staff = User.objects.create_user(username="staff2", password="pass12345", is_staff=True)

    def test_donor_cannot_record_donation(self):
        self.client.force_login(self.donor_profile.user)
        response = self.client.get(reverse("donations:record"))
        self.assertEqual(response.status_code, 403)

    def test_staff_can_record_donation(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("donations:record"))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_cannot_see_donation_list(self):
        response = self.client.get(reverse("donations:list"))
        self.assertEqual(response.status_code, 302)  # redirected to login

    def test_donor_sees_only_their_own_history_not_a_url_pk(self):
        """
        Part 3.A.3 / 3.F IDOR: donations:my_history takes no pk -- there is
        no URL parameter a donor could change to view someone else's
        history. Confirm the view only ever returns the caller's own
        records even when another donor has donations recorded.
        """
        record_donation(
            donor=self.other_donor_profile, blood_group="A+", quantity=1,
            collection_date=date.today(), collection_reference="REF-OTHER",
            recorded_by=self.staff,
        )
        record_donation(
            donor=self.donor_profile, blood_group="O+", quantity=1,
            collection_date=date.today(), collection_reference="REF-MINE",
            recorded_by=self.staff,
        )
        self.client.force_login(self.donor_profile.user)
        response = self.client.get(reverse("donations:my_history"))
        self.assertContains(response, "REF-MINE")
        self.assertNotContains(response, "REF-OTHER")

    def test_donor_history_url_has_no_id_parameter_to_tamper_with(self):
        from django.urls import resolve
        match = resolve(reverse("donations:my_history"))
        self.assertEqual(match.kwargs, {})
