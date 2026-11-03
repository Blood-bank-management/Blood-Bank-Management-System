from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from auditlog.models import AuditLog
from donors.models import DonorProfile, EligibilityHistory
from donations.models import Donation
from inventory.models import BloodInventory, InventoryTransaction

from .models import BloodIssue, BloodRequest


User = get_user_model()


class BloodBankEndToEndWorkflowTests(TestCase):
    """Verify the primary donor-to-distribution workflow through HTTP views."""

    def test_donor_to_blood_issue_workflow(self):
        registration_data = {
            "first_name": "Asha",
            "last_name": "Rao",
            "username": "e2e_donor",
            "email": "e2e.donor@example.com",
            "phone_number": "+91 98765 43210",
            "date_of_birth": (date.today() - timedelta(days=365 * 25)).isoformat(),
            "blood_group": "O+",
            "address": "12 MG Road, Bengaluru",
            "password1": "S3cure-Pass!word-42",
            "password2": "S3cure-Pass!word-42",
        }
        response = self.client.post(
            reverse("donors:register"),
            registration_data,
        )
        self.assertRedirects(response, reverse("authentication:home"))
        donor = DonorProfile.objects.get(user__username="e2e_donor")

        self.assertContains(self.client.get(reverse("donors:profile")), "e2e_donor")
        self.client.post(reverse("authentication:logout"))

        staff = User.objects.create_user(
            username="e2e_staff",
            password="S3cure-Staff!word-42",
            is_staff=True,
        )
        self.client.force_login(staff)

        detail_url = reverse("donors:detail", kwargs={"pk": donor.pk})
        response = self.client.post(
            detail_url,
            {
                "eligibility_status": DonorProfile.Eligibility.TEMPORARILY_INELIGIBLE,
                "note": "Recorded recent donation.",
            },
        )
        self.assertRedirects(response, detail_url)
        donor.refresh_from_db()
        self.assertEqual(
            donor.eligibility_status,
            DonorProfile.Eligibility.TEMPORARILY_INELIGIBLE,
        )
        self.assertEqual(EligibilityHistory.objects.filter(donor=donor).count(), 1)

        response = self.client.post(
            reverse("donations:record"),
            {
                "donor_username": donor.user.username,
                "blood_group": "O+",
                "quantity": 5,
                "collection_date": date.today().isoformat(),
                "collection_reference": "E2E-DON-0001",
                "outcome": Donation.Status.RECORDED,
                "rejection_reason": "",
                "notes": "End-to-end test donation.",
            },
        )
        self.assertRedirects(response, reverse("donations:list"))
        donation = Donation.objects.get(collection_reference="E2E-DON-0001")
        batch = BloodInventory.objects.get(source_donation=donation)
        self.assertEqual(batch.quantity_remaining, 5)

        self.client.logout()
        response = self.client.post(
            reverse("requests:create"),
            {
                "requester_name": "City Hospital",
                "requester_email": "hospital@example.com",
                "hospital_name": "City Hospital",
                "blood_group": "O+",
                "quantity": 2,
                "purpose": "Scheduled surgery",
            },
        )
        blood_request = BloodRequest.objects.get()
        self.assertRedirects(
            response,
            reverse(
                "requests:detail",
                kwargs={"tracking_id": blood_request.tracking_id},
            ),
        )
        self.assertContains(self.client.get(response.url), "Pending review")

        self.client.force_login(staff)
        response = self.client.post(
            reverse(
                "requests:review",
                kwargs={"tracking_id": blood_request.tracking_id},
            ),
            {"action": BloodRequest.Status.APPROVED, "review_note": "Stock confirmed."},
        )
        self.assertRedirects(response, reverse("requests:queue"))
        blood_request.refresh_from_db()
        self.assertEqual(blood_request.status, BloodRequest.Status.APPROVED)

        response = self.client.post(
            reverse(
                "requests:issue",
                kwargs={"tracking_id": blood_request.tracking_id},
            ),
            {"issue_note": "Released to City Hospital."},
        )
        self.assertRedirects(response, reverse("requests:queue"))
        blood_request.refresh_from_db()
        batch.refresh_from_db()
        self.assertEqual(blood_request.status, BloodRequest.Status.FULFILLED)
        self.assertEqual(batch.quantity_remaining, 3)
        self.assertEqual(BloodIssue.objects.get(request=blood_request).quantity, 2)

        self.assertContains(
            self.client.get(reverse("inventory:availability_search"), {"blood_group": "O+"}),
            "3",
        )
        self.assertEqual(
            InventoryTransaction.objects.filter(batch=batch).count(),
            2,
        )
        self.assertEqual(
            set(
                AuditLog.objects.values_list("action", flat=True)
            ),
            {
                AuditLog.Action.ELIGIBILITY_CHANGED,
                AuditLog.Action.DONATION_RECORDED,
                AuditLog.Action.INVENTORY_INCREASED,
                AuditLog.Action.REQUEST_SUBMITTED,
                AuditLog.Action.REQUEST_APPROVED,
                AuditLog.Action.BLOOD_ISSUED,
            },
        )
