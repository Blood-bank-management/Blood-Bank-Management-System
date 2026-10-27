
import time
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse


class AuthenticatedPagePerformanceTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            username="perfuser",
            password="perfpass123"
        )
        self.client.force_login(user)

    def test_common_pages_response_time(self):
        pages = {
            "Login": reverse("login"),
            "Availability": reverse("availability_search"),
            "Inventory summary": reverse("inventory_summary"),
        }

        limit_seconds = 3.0
        requests_per_page = 20

        for name, url in pages.items():
            times = []

            for _ in range(requests_per_page):
                start = time.perf_counter()
                response = self.client.get(url)
                elapsed = time.perf_counter() - start

                self.assertEqual(response.status_code, 200)
                times.append(elapsed)

            times.sort()
            p90 = times[17]

            print(
                f"{name}: p90={p90:.4f}s "
                f"(target <= {limit_seconds}s)"
            )

            self.assertLessEqual(
                p90,
                limit_seconds,
                f"{name} exceeded the 3-second p90 target"
            )
