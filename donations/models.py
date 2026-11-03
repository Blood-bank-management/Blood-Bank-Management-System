from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from bloodbank.constants import (
    BLOOD_GROUP_CHOICES,
    MIN_DAYS_BETWEEN_DONATIONS,
    validate_not_future_date,
    validate_positive_quantity,
)


class Donation(models.Model):
    """
    Donation Management module (Part 3.A). A Donation is the record of a
    donor giving blood; a *successful* (RECORDED) donation is what credits
    an inventory.BloodInventory batch -- see donations.services.
    record_donation, which is the only code path allowed to create a
    Donation that credits stock, run inside one atomic transaction.
    """

    class Status(models.TextChoices):
        RECORDED = "recorded", "Recorded"
        REJECTED = "rejected", "Rejected (did not meet collection criteria)"

    donor = models.ForeignKey(
        "donors.DonorProfile",
        on_delete=models.PROTECT,
        related_name="donations",
    )
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    quantity = models.PositiveIntegerField(validators=[validate_positive_quantity])
    collection_date = models.DateField()
    collection_reference = models.CharField(
        max_length=64,
        unique=True,
        help_text="A unique reference for this collection (e.g. a bag/barcode number). "
                   "Enforced unique so resubmitting the same recording form a second time "
                   "is rejected as a duplicate instead of silently double-crediting stock.",
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RECORDED)
    rejection_reason = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="donations_recorded",
        help_text="Staff member who entered this donation record.",
    )
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-collection_date", "-created_at")
        indexes = [
            models.Index(fields=["donor", "-collection_date"]),
            models.Index(fields=["blood_group"]),
            models.Index(fields=["status"]),
        ]

    def clean(self):
        validate_not_future_date(self.collection_date, field_name="Collection date")

    def __str__(self):
        return f"Donation {self.collection_reference} ({self.donor_id}, {self.quantity}u {self.blood_group})"

    @property
    def is_successful(self):
        return self.status == self.Status.RECORDED


def next_eligible_date(donor_profile):
    """
    donations/BBMS-F-006 helper: the earliest date this donor may donate
    again, based on their most recent RECORDED donation plus
    MIN_DAYS_BETWEEN_DONATIONS (a documented project assumption -- see
    bloodbank/constants.py and docs/KNOWN_ISSUES.md -- not an invented
    medical rule applied silently).
    """
    from datetime import timedelta

    last = (
        Donation.objects.filter(donor=donor_profile, status=Donation.Status.RECORDED)
        .order_by("-collection_date")
        .first()
    )
    if last is None:
        return None
    return last.collection_date + timedelta(days=MIN_DAYS_BETWEEN_DONATIONS)
