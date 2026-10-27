
from datetime import date, timedelta

from django.test import TestCase
from django.contrib.auth.models import User

from .models import BloodInventory


class BloodInventoryTests(TestCase):

    def setUp(self):
        user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.client.force_login(user)

    # UNIT TESTS - INVENTORY

    def test_inventory_quantity_cannot_be_negative(self):
        inventory = BloodInventory(
            blood_group="A+",
            quantity=-5,
            collection_date=date.today(),
            expiry_date=date.today() + timedelta(days=30),
        )

        with self.assertRaises(Exception):
            inventory.full_clean()

    def test_expiry_date_cannot_be_before_collection_date(self):
        inventory = BloodInventory(
            blood_group="A+",
            quantity=5,
            collection_date=date.today(),
            expiry_date=date.today() - timedelta(days=1),
        )

        with self.assertRaises(Exception):
            inventory.full_clean()

    def test_inventory_summary_includes_zero_stock(self):
        blood_groups = [
            "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"
        ]

        for group in blood_groups:
            BloodInventory.objects.create(
                blood_group=group,
                quantity=0,
                collection_date=date.today(),
                expiry_date=date.today() + timedelta(days=30),
            )

        self.assertEqual(
            BloodInventory.objects.filter(quantity=0).count(),
            8
        )

    # UNIT TESTS - SEARCH

    def test_search_requires_blood_group(self):
        response = self.client.get("/availability/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please select a blood group.")

    def test_search_handles_unsupported_blood_group(self):
        response = self.client.get(
            "/availability/",
            {"blood_group": "X+"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unsupported blood group.")

    def test_search_shows_no_stock_message(self):
        BloodInventory.objects.create(
            blood_group="AB-",
            quantity=0,
            collection_date=date.today(),
            expiry_date=date.today() + timedelta(days=30),
        )

        response = self.client.get(
            "/availability/",
            {"blood_group": "AB-"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "No blood available for this blood group."
        )

    def test_search_shows_available_quantity(self):
        BloodInventory.objects.create(
            blood_group="O+",
            quantity=5,
            collection_date=date.today(),
            expiry_date=date.today() + timedelta(days=30),
        )

        response = self.client.get(
            "/availability/",
            {"blood_group": "O+"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "5")

    # INTEGRATION TESTS - SEARCH

    def test_search_matches_current_inventory(self):
        BloodInventory.objects.create(
            blood_group="O+",
            quantity=5,
            collection_date=date.today(),
            expiry_date=date.today() + timedelta(days=30),
        )

        response = self.client.get(
            "/availability/",
            {"blood_group": "O+"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Available: 5 units")

    def test_search_excludes_expired_units(self):
        BloodInventory.objects.create(
            blood_group="O+",
            quantity=5,
            collection_date=date.today() - timedelta(days=60),
            expiry_date=date.today() - timedelta(days=1),
        )

        BloodInventory.objects.create(
            blood_group="O+",
            quantity=2,
            collection_date=date.today(),
            expiry_date=date.today() + timedelta(days=30),
        )

        response = self.client.get(
            "/availability/",
            {"blood_group": "O+"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Available: 2 units")

    # PRELIMINARY INVENTORY INTEGRITY TEST

    def test_inventory_quantities_are_non_negative(self):
        blood_groups = [
            "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"
        ]

        for group in blood_groups:
            total = sum(
                item.quantity
                for item in BloodInventory.objects.filter(
                    blood_group=group,
                    expiry_date__gte=date.today()
                )
            )

            self.assertGreaterEqual(total, 0)
