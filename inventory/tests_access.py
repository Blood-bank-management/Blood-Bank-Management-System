"""Part 3.F: allowed/denied access for the new staff-only inventory views."""
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .services import receive_batch

User = get_user_model()


class InventoryStaffViewAccessTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="inv-view-staff", password="pass12345", is_staff=True)
        self.donor = User.objects.create_user(username="inv-view-donor", password="pass12345")
        self.batch = receive_batch(blood_group="O+", quantity=3, collection_date=date.today(), performed_by=self.staff)

    def test_staff_can_view_batch_list_and_detail(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("inventory:batch_list")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("inventory:batch_detail", kwargs={"pk": self.batch.pk})).status_code, 200,
        )

    def test_donor_cannot_view_batch_list_or_adjust(self):
        self.client.force_login(self.donor)
        self.assertEqual(self.client.get(reverse("inventory:batch_list")).status_code, 403)
        response = self.client.post(
            reverse("inventory:batch_detail", kwargs={"pk": self.batch.pk}),
            {"delta": "-1", "reason": "sneaky"},
        )
        self.assertEqual(response.status_code, 403)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.quantity_remaining, 3)

    def test_anonymous_redirected_from_inventory_summary(self):
        self.assertEqual(self.client.get(reverse("inventory:inventory_summary")).status_code, 302)
