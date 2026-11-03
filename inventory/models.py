from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from bloodbank.constants import BLOOD_GROUP_CHOICES, validate_positive_quantity


class BloodInventory(models.Model):
    """
    The single inventory source of truth (Part 2.A / Part 3.B).

    Before this patch there were two independent models: this one
    (batch-level, with expiry) and requests.BloodInventory (a per-blood-group
    aggregate counter). The availability search used this model; the issue
    workflow decremented the other one, so the two numbers could disagree
    with no code path that kept them in sync. This model is now the only
    stock table in the project; requests.BloodInventory is removed by the
    migration that ships with this patch (0002_remove_duplicate_aggregate.py
    in the requests app), after migrating its data into batches here.

    `quantity` is the amount originally received into this batch and never
    changes after creation -- it is the audit trail's "how much did this
    batch start with". `quantity_remaining` is the live balance and is the
    only field availability/issue logic reads; it only ever changes through
    InventoryTransaction-recording service functions in inventory.services,
    never by direct `.save()` from a view, so every change to stock has a
    matching ledger row.
    """

    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    quantity = models.PositiveIntegerField(
        validators=[validate_positive_quantity],
        help_text="Units originally received into this batch. Does not change after creation.",
    )
    quantity_remaining = models.PositiveIntegerField(
        default=0,
        help_text="Live available balance for this batch. Changed only via inventory.services.",
    )
    collection_date = models.DateField()
    expiry_date = models.DateField()
    source_donation = models.OneToOneField(
        "donations.Donation",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_batch",
        help_text="The donation this batch was credited from, if any. "
                   "Null for batches created directly by staff (e.g. migrated "
                   "legacy stock) with no matching Donation record.",
    )
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("expiry_date",)
        verbose_name_plural = "blood inventory batches"
        indexes = [
            models.Index(fields=["blood_group", "expiry_date"]),
        ]

    def clean(self):
        if self.expiry_date and self.collection_date and self.expiry_date < self.collection_date:
            raise ValidationError("Expiry date cannot be before collection date.")

    def save(self, *args, **kwargs):
        # Backward-compatible default: a batch created without explicitly
        # setting quantity_remaining (e.g. direct BloodInventory.objects.
        # create(quantity=5, ...) in existing tests or an admin/data
        # migration) starts fully stocked, same as before this field
        # existed. inventory.services always sets quantity_remaining
        # explicitly, so this only ever applies to that legacy call shape.
        if self._state.adding and not self.quantity_remaining and self.quantity:
            self.quantity_remaining = self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.blood_group} batch #{self.pk}: {self.quantity_remaining}/{self.quantity} units"

    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expiry_date < timezone.localdate()

    @property
    def is_depleted(self):
        return self.quantity_remaining <= 0


class InventoryTransactionQuerySet(models.QuerySet):
    def for_blood_group(self, blood_group):
        return self.filter(batch__blood_group=blood_group)


class InventoryTransaction(models.Model):
    """
    Append-only ledger of every stock change (Part 2.A / Part 3.B / Part 4).
    Every credit, issue and manual adjustment to a BloodInventory batch
    writes exactly one row here, inside the same transaction.atomic() block
    as the balance change -- see inventory.services. This is what makes
    "maintain a complete inventory transaction history" true rather than
    aspirational.
    """

    class TransactionType(models.TextChoices):
        RECEIVE = "receive", "Stock received"
        ISSUE = "issue", "Stock issued"
        ADJUSTMENT = "adjustment", "Manual adjustment"

    batch = models.ForeignKey(
        BloodInventory, on_delete=models.CASCADE, related_name="transactions",
    )
    transaction_type = models.CharField(max_length=12, choices=TransactionType.choices)
    quantity_delta = models.IntegerField(
        help_text="Positive for receive/upward adjustment, negative for issue/downward adjustment.",
    )
    balance_after = models.PositiveIntegerField()
    related_issue = models.ForeignKey(
        "requests.BloodIssue",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_transactions",
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_transactions",
    )
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = InventoryTransactionQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.quantity_delta:+d} on batch #{self.batch_id}"
