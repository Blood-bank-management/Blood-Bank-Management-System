"""
donation -> inventory integration (Part 2.A/3.A: "a successful donation must
update the appropriate inventory batch/stock... donation and inventory
updates succeed or fail together... prevent duplicate inventory credits if
a donation form is resubmitted").
"""
from django.db import IntegrityError, transaction

import auditlog.models as auditlog
from inventory.services import receive_batch

from .models import Donation


class DuplicateDonationError(Exception):
    """Raised when collection_reference already exists -- i.e. this exact
    donation was already recorded, most likely a resubmitted form."""


@transaction.atomic
def record_donation(*, donor, blood_group, quantity, collection_date,
                     collection_reference, recorded_by, notes="", status=Donation.Status.RECORDED,
                     rejection_reason=""):
    """
    The only way to create a Donation that can ever credit stock. A
    REJECTED donation is recorded (so staff keep a record of why collection
    didn't go ahead) but never creates an inventory batch -- "do not allow
    expired or rejected donations to become available stock" (Part 3.A.2).

    Resubmission protection: collection_reference has a unique database
    constraint (donations.Donation.collection_reference), so a second
    request with the same reference raises IntegrityError here, which is
    translated into DuplicateDonationError for the view to show as a form
    error rather than silently creating a second credited batch.
    """
    try:
        donation = Donation.objects.create(
            donor=donor,
            blood_group=blood_group,
            quantity=quantity,
            collection_date=collection_date,
            collection_reference=collection_reference,
            status=status,
            rejection_reason=rejection_reason,
            recorded_by=recorded_by,
            notes=notes,
        )
    except IntegrityError as exc:
        raise DuplicateDonationError(
            f"A donation with collection reference '{collection_reference}' "
            "has already been recorded."
        ) from exc

    auditlog.record(
        auditlog.AuditLog.Action.DONATION_RECORDED,
        entity_type="donation",
        entity_id=donation.pk,
        actor=recorded_by,
        new_value=f"{status}: {quantity}u {blood_group} from donor #{donor.pk}",
    )

    if status == Donation.Status.RECORDED:
        batch = receive_batch(
            blood_group=blood_group,
            quantity=quantity,
            collection_date=collection_date,
            source_donation=donation,
            performed_by=recorded_by,
            notes=f"Donation {collection_reference}",
        )
        auditlog.record(
            auditlog.AuditLog.Action.INVENTORY_INCREASED,
            entity_type="bloodinventory",
            entity_id=batch.pk,
            actor=recorded_by,
            new_value=f"+{quantity}u {blood_group} (donation {collection_reference})",
        )

    return donation
