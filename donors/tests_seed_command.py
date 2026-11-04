"""seed_demo_data runs and is idempotent (coverage gap 4.1, regression guard for DEFECT-04)."""
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from auditlog.models import AuditLog
from donations.models import Donation
from inventory.models import BloodInventory, InventoryTransaction
from requests.models import BloodIssue, BloodRequest

User = get_user_model()
MODELS = [User, BloodInventory, InventoryTransaction, Donation, BloodRequest, BloodIssue, AuditLog]


def counts():
    return [m.objects.count() for m in MODELS]


class SeedDemoDataTests(TestCase):
    def test_seed_creates_expected_rows(self):
        call_command("seed_demo_data", stdout=StringIO())
        self.assertEqual(counts(), [5, 7, 8, 2, 3, 1, 8])

    def test_seed_is_idempotent(self):
        call_command("seed_demo_data", stdout=StringIO())
        first = counts()
        call_command("seed_demo_data", stdout=StringIO())
        self.assertEqual(counts(), first)
