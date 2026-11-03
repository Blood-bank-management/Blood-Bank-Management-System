"""
All writes to BloodInventory stock go through these functions. Nothing else
in the project is allowed to decrement/increment `quantity_remaining`
directly -- that is what makes "donation increases stock exactly once" and
"issue decreases stock exactly once" (Part 11 final-verification checklist)
actual invariants rather than things that happen to be true today.

Every function here runs inside transaction.atomic() and writes a matching
InventoryTransaction row, so the business-data change and its ledger entry
always succeed or fail together (Part 3.B, Part 4).
"""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from bloodbank.constants import WHOLE_BLOOD_SHELF_LIFE_DAYS
from .models import BloodInventory, InventoryTransaction


def available_units(blood_group):
    """
    The one place "how much blood of this group is actually usable" is
    computed: sum of quantity_remaining across batches of this group that
    are neither expired nor depleted. Availability search, the inventory
    dashboard and the issue workflow all call this instead of each
    re-deriving their own filter, which is exactly the "duplicate inventory
    source of truth" problem this patch removes.
    """
    today = timezone.localdate()
    return (
        BloodInventory.objects.filter(
            blood_group=blood_group,
            expiry_date__gte=today,
            quantity_remaining__gt=0,
        ).aggregate(total=Sum("quantity_remaining"))["total"]
        or 0
    )


@transaction.atomic
def receive_batch(*, blood_group, quantity, collection_date, expiry_date=None,
                   source_donation=None, performed_by=None, notes=""):
    """
    Create a new batch and its matching RECEIVE ledger row atomically.
    Used by donations.services.record_donation (donation -> stock credit)
    and by staff manually adding legacy/manual stock.
    """
    if quantity is None or quantity <= 0:
        raise ValidationError("Quantity received must be a positive number of units.")

    if expiry_date is None:
        expiry_date = collection_date + timedelta(days=WHOLE_BLOOD_SHELF_LIFE_DAYS)

    batch = BloodInventory.objects.create(
        blood_group=blood_group,
        quantity=quantity,
        quantity_remaining=quantity,
        collection_date=collection_date,
        expiry_date=expiry_date,
        source_donation=source_donation,
        notes=notes,
    )
    InventoryTransaction.objects.create(
        batch=batch,
        transaction_type=InventoryTransaction.TransactionType.RECEIVE,
        quantity_delta=quantity,
        balance_after=quantity,
        performed_by=performed_by,
        reason=notes or "Stock received",
    )
    return batch


@transaction.atomic
def issue_units(*, blood_group, quantity, performed_by, related_issue=None, reason=""):
    """
    Decrement the oldest-expiring non-expired batches first (FIFO by
    expiry) until `quantity` units have been issued, or raise if the group
    does not have enough available stock. Locks the candidate batch rows
    with select_for_update so two concurrent issues against the same
    low-stock group cannot both succeed and drive the balance negative
    (Part 2.A "safe concurrent transactions", Part 11 "no negative stock").
    """
    if quantity is None or quantity <= 0:
        raise ValidationError("Quantity issued must be a positive number of units.")

    today = timezone.localdate()
    batches = list(
        BloodInventory.objects.select_for_update()
        .filter(blood_group=blood_group, expiry_date__gte=today, quantity_remaining__gt=0)
        .order_by("expiry_date", "id")
    )

    total_available = sum(b.quantity_remaining for b in batches)
    if total_available < quantity:
        raise ValidationError(
            f"Insufficient {blood_group} inventory: {total_available} unit(s) available, "
            f"{quantity} requested."
        )

    remaining_to_issue = quantity
    touched = []
    for batch in batches:
        if remaining_to_issue <= 0:
            break
        take = min(batch.quantity_remaining, remaining_to_issue)
        batch.quantity_remaining -= take
        batch.save(update_fields=("quantity_remaining",))
        InventoryTransaction.objects.create(
            batch=batch,
            transaction_type=InventoryTransaction.TransactionType.ISSUE,
            quantity_delta=-take,
            balance_after=batch.quantity_remaining,
            related_issue=related_issue,
            performed_by=performed_by,
            reason=reason or "Stock issued",
        )
        touched.append((batch, take))
        remaining_to_issue -= take

    return touched


@transaction.atomic
def adjust_batch(*, batch, delta, performed_by, reason):
    """Manual correction to a single batch (e.g. spoilage, count correction)."""
    if delta == 0:
        raise ValidationError("Adjustment quantity cannot be zero.")
    new_balance = batch.quantity_remaining + delta
    if new_balance < 0:
        raise ValidationError("Adjustment would drive this batch's balance below zero.")
    if not reason:
        raise ValidationError("A reason is required for a manual inventory adjustment.")

    batch.quantity_remaining = new_balance
    batch.save(update_fields=("quantity_remaining",))
    InventoryTransaction.objects.create(
        batch=batch,
        transaction_type=InventoryTransaction.TransactionType.ADJUSTMENT,
        quantity_delta=delta,
        balance_after=new_balance,
        performed_by=performed_by,
        reason=reason,
    )
    return batch
