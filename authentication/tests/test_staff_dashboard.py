"""Staff dashboard on /home/ (coverage gap 4.2: _staff_dashboard_context)."""
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from bloodbank.constants import BLOOD_GROUPS
from inventory.services import receive_batch

User = get_user_model()
HOME = reverse("authentication:home")


class StaffDashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user(
            username="dash_staff", password="S3cure-Pass!word-42", is_staff=True
        )

    def test_staff_user_gets_staff_dashboard(self):
        self.client.force_login(self.staff)
        response = self.client.get(HOME)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_staff_dashboard"])
        groups = [row["blood_group"] for row in response.context["blood_group_distribution"]]
        self.assertEqual(groups, list(BLOOD_GROUPS))

    def test_staff_dashboard_totals_reflect_live_stock(self):
        receive_batch(blood_group="A+", quantity=3, collection_date=date.today(), performed_by=self.staff)
        self.client.force_login(self.staff)
        response = self.client.get(HOME)
        self.assertEqual(response.context["total_available_units"], 3)
        a_pos = [r for r in response.context["blood_group_distribution"] if r["blood_group"] == "A+"][0]
        self.assertEqual(a_pos["units"], 3)
