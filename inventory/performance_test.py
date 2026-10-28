
import time
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AuthenticatedPagePerformanceTests(TestCase):
    """
    BBMS-53 performance smoke test.

    inventory_summary is now staff-only (Sprint 2 RBAC fix: BBMS-F-011 names
    "Blood Bank Staff" as the page's source/stakeholder, so a plain donor
    account should never have reached it). The test user here is created
    with is_staff=True to match, and the login page is measured with a
    logged-out client since it is never behind authentication.
    """

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="perfuser",
            password="perfpass123",
            is_staff=True,
        )

    def test_common_pages_response_time(self):
        limit_seconds = 3.0
        requests_per_page = 20

        self._measure(
            "Login", reverse("authentication:login"),
            self.client, requests_per_page, limit_seconds,
        )

        self.client.force_login(self.staff_user)
        staff_pages = {
            "Availability": reverse("inventory:availability_search"),
            "Inventory summary": reverse("inventory:inventory_summary"),
        }
        for name, url in staff_pages.items():
            self._measure(name, url, self.client, requests_per_page, limit_seconds)

    def _measure(self, name, url, client, requests_per_page, limit_seconds):
        times = []

        for _ in range(requests_per_page):
            start = time.perf_counter()
            response = client.get(url)
            elapsed = time.perf_counter() - start

            self.assertEqual(response.status_code, 200)
            times.append(elapsed)

        times.sort()
        p90 = times[17]

        print(f"{name}: p90={p90:.4f}s (target <= {limit_seconds}s)")

        self.assertLessEqual(
            p90, limit_seconds, f"{name} exceeded the 3-second p90 target"
        )
