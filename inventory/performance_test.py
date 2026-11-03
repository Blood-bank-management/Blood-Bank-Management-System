
import time
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from donors.models import DonorProfile
from requests.models import BloodRequest


class AuthenticatedPagePerformanceTests(TestCase):
    """
    BBMS-53 / Part 5.E performance smoke test, run against Django's
    in-process test client -- this measures view/template/ORM overhead on
    whatever machine runs the test, NOT production latency under real
    network, WSGI-server and concurrent-load conditions. Treat the numbers
    below as a regression signal (did this change make a page much
    slower), not as a production SLA measurement -- Part 5.E explicitly
    warns against claiming production performance from this client, and
    this docstring is that warning made concrete rather than an
    afterthought.

    inventory_summary/batch_list/donor_list/donation list/request queue/
    administrative user list are all staff-or-admin-only, so the staff/
    admin test user created in setUp is used for all of them; the login
    page and availability search are measured as the SRS originally
    specified (login logged-out, availability as any authenticated user).
    """

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="perfuser", password="perfpass123", is_staff=True,
        )
        self.admin_user = User.objects.create_superuser(
            username="perfadmin", password="perfpass123", email="perf@example.com",
        )
        donor_user = User.objects.create_user(username="perfdonor", password="perfpass123")
        self.donor_profile = DonorProfile.objects.create(
            user=donor_user, phone_number="+1 555-0199",
            date_of_birth=date(1990, 1, 1), blood_group="O+", address="1 Perf St",
        )
        self.tracked_request = BloodRequest.objects.create(
            requester_name="Perf Tester", requester_email="perf@example.com",
            hospital_name="Perf Hospital", blood_group="O+", quantity=1,
            purpose="performance test fixture",
        )
        # A modest, realistic-ish dataset so list/search pages aren't
        # being measured against an empty table.
        for i in range(30):
            DonorProfile.objects.create(
                user=User.objects.create_user(username=f"perf-donor-{i}", password="x"),
                phone_number="+1 555-0100", date_of_birth=date(1992, 1, 1),
                blood_group="A+", address=f"{i} Sample Rd",
            )

    def test_common_pages_response_time(self):
        limit_seconds = 3.0
        requests_per_page = 20

        self._measure(
            "Login", reverse("authentication:login"),
            self.client, requests_per_page, limit_seconds,
        )
        self._measure(
            "Request tracking", reverse("requests:detail", kwargs={"tracking_id": self.tracked_request.tracking_id}),
            self.client, requests_per_page, limit_seconds,
        )

        self.client.force_login(self.staff_user)
        staff_pages = {
            "Availability": reverse("inventory:availability_search"),
            "Inventory dashboard": reverse("inventory:inventory_summary"),
            "Donor list": reverse("donors:list"),
            "Donation list": reverse("donations:list"),
            "Request queue": reverse("requests:queue"),
        }
        for name, url in staff_pages.items():
            self._measure(name, url, self.client, requests_per_page, limit_seconds)
        self.client.logout()

        self.client.force_login(self.admin_user)
        self._measure(
            "Administrative user list", reverse("accounts:list"),
            self.client, requests_per_page, limit_seconds,
        )

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
