"""Manual batch adjustment (coverage gap 4.4)."""
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import InventoryTransaction
from .services import adjust_batch, receive_batch

User = get_user_model()


class BatchAdjustmentTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("adj_staff", password="S3cure-Pass!word-42", is_staff=True)
        self.batch = receive_batch(
            blood_group="O+", quantity=5, collection_date=date.today(), performed_by=self.staff
        )
        self.url = reverse("inventory:batch_detail", args=[self.batch.pk])

    def test_successful_adjustment_updates_balance_and_ledger(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url, {"delta": -1, "reason": "Spoiled unit"})
        self.assertRedirects(response, self.url)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.quantity_remaining, 4)
        txn = InventoryTransaction.objects.get(
            batch=self.batch, transaction_type=InventoryTransaction.TransactionType.ADJUSTMENT
        )
        self.assertEqual(txn.quantity_delta, -1)
        self.assertEqual(txn.balance_after, 4)
        self.assertEqual(txn.reason, "Spoiled unit")
