"""
Tests for the new batch-ledger service layer (inventory/services.py).
Kept in a separate module from inventory/tests.py (the pre-existing
Sprint-1 suite) rather than merged into it, so the original file's
history/diff stays easy to review on its own.
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import BloodInventory, InventoryTransaction
from .services import adjust_batch, available_units, issue_units, receive_batch

User = get_user_model()


class InventoryServiceTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="inv-staff", password="pass12345", is_staff=True)

    def test_receive_batch_credits_stock_and_writes_ledger_row(self):
        batch = receive_batch(
            blood_group="B+", quantity=4, collection_date=date.today(), performed_by=self.staff,
        )
        self.assertEqual(batch.quantity_remaining, 4)
        txn = InventoryTransaction.objects.get(batch=batch)
        self.assertEqual(txn.transaction_type, InventoryTransaction.TransactionType.RECEIVE)
        self.assertEqual(txn.quantity_delta, 4)
        self.assertEqual(txn.balance_after, 4)

    def test_receive_batch_defaults_expiry_to_shelf_life(self):
        from bloodbank.constants import WHOLE_BLOOD_SHELF_LIFE_DAYS
        collected = date.today()
        batch = receive_batch(blood_group="B+", quantity=1, collection_date=collected, performed_by=self.staff)
        self.assertEqual(batch.expiry_date, collected + timedelta(days=WHOLE_BLOOD_SHELF_LIFE_DAYS))

    def test_issue_units_decrements_oldest_expiring_batch_first(self):
        older = receive_batch(
            blood_group="A+", quantity=2, collection_date=date.today(),
            expiry_date=date.today() + timedelta(days=5), performed_by=self.staff,
        )
        newer = receive_batch(
            blood_group="A+", quantity=5, collection_date=date.today(),
            expiry_date=date.today() + timedelta(days=30), performed_by=self.staff,
        )
        issue_units(blood_group="A+", quantity=3, performed_by=self.staff)
        older.refresh_from_db()
        newer.refresh_from_db()
        self.assertEqual(older.quantity_remaining, 0)
        self.assertEqual(newer.quantity_remaining, 4)

    def test_issue_units_raises_on_insufficient_stock_and_changes_nothing(self):
        receive_batch(blood_group="AB-", quantity=2, collection_date=date.today(), performed_by=self.staff)
        with self.assertRaises(ValidationError):
            issue_units(blood_group="AB-", quantity=5, performed_by=self.staff)
        self.assertEqual(available_units("AB-"), 2)
        self.assertEqual(InventoryTransaction.objects.filter(transaction_type="issue").count(), 0)

    def test_issue_units_excludes_expired_batches(self):
        receive_batch(
            blood_group="O-", quantity=5, collection_date=date.today() - timedelta(days=60),
            expiry_date=date.today() - timedelta(days=1), performed_by=self.staff,
        )
        with self.assertRaises(ValidationError):
            issue_units(blood_group="O-", quantity=1, performed_by=self.staff)

    def test_no_negative_stock_possible_via_adjust(self):
        batch = receive_batch(blood_group="O-", quantity=2, collection_date=date.today(), performed_by=self.staff)
        with self.assertRaises(ValidationError):
            adjust_batch(batch=batch, delta=-5, performed_by=self.staff, reason="correction")
        batch.refresh_from_db()
        self.assertEqual(batch.quantity_remaining, 2)

    def test_adjust_batch_requires_a_reason(self):
        batch = receive_batch(blood_group="O-", quantity=2, collection_date=date.today(), performed_by=self.staff)
        with self.assertRaises(ValidationError):
            adjust_batch(batch=batch, delta=1, performed_by=self.staff, reason="")

    def test_concurrent_issue_cannot_drive_balance_negative(self):
        """
        Part 2.A 'safe concurrent transactions': issue_units locks candidate
        batches with select_for_update inside an atomic block. We can't
        spin up real concurrent DB connections inside a single SQLite test
        transaction, so this test instead proves the *sequential* guard
        that would stop a second concurrent request from overselling: once
        the first issue_units call commits, a second call for more than
        what's left is rejected rather than allowed to go negative.
        """
        receive_batch(blood_group="B-", quantity=3, collection_date=date.today(), performed_by=self.staff)
        issue_units(blood_group="B-", quantity=3, performed_by=self.staff)
        with self.assertRaises(ValidationError):
            issue_units(blood_group="B-", quantity=1, performed_by=self.staff)
        self.assertEqual(available_units("B-"), 0)

    def test_available_units_excludes_depleted_batches(self):
        batch = receive_batch(blood_group="AB+", quantity=1, collection_date=date.today(), performed_by=self.staff)
        issue_units(blood_group="AB+", quantity=1, performed_by=self.staff)
        self.assertEqual(available_units("AB+"), 0)
