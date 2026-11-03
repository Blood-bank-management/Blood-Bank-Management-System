from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Append-only history of the sensitive actions enumerated in the Jira
    audit-logging requirement: donation recorded/modified, inventory
    increased/decreased/adjusted, request submitted/approved/rejected/status
    changed, blood issued, donor eligibility changed, user
    created/role-changed/activated/deactivated.

    Deliberately NOT a generic Django ContentType-based audit framework --
    this is a small project and a plain (action, entity_type, entity_id)
    triplet plus free-text before/after values is enough to satisfy the
    requirement without adding a dependency. `entity_type`/`entity_id` let a
    caller point at *any* model (Donation, BloodInventory, BloodRequest,
    DonorProfile, auth.User, ...) without this app importing any of them,
    which is what keeps auditlog import-cycle-free relative to every app
    that writes to it.
    """

    class Action(models.TextChoices):
        DONATION_RECORDED = "donation_recorded", "Donation recorded"
        DONATION_MODIFIED = "donation_modified", "Donation modified"
        DONATION_CANCELLED = "donation_cancelled", "Donation cancelled"
        INVENTORY_INCREASED = "inventory_increased", "Inventory increased"
        INVENTORY_DECREASED = "inventory_decreased", "Inventory decreased"
        INVENTORY_ADJUSTED = "inventory_adjusted", "Inventory adjusted"
        REQUEST_SUBMITTED = "request_submitted", "Request submitted"
        REQUEST_APPROVED = "request_approved", "Request approved"
        REQUEST_REJECTED = "request_rejected", "Request rejected"
        REQUEST_STATUS_CHANGED = "request_status_changed", "Request status changed"
        BLOOD_ISSUED = "blood_issued", "Blood issued"
        ELIGIBILITY_CHANGED = "eligibility_changed", "Donor eligibility changed"
        USER_CREATED = "user_created", "User created"
        USER_ROLE_CHANGED = "user_role_changed", "User role changed"
        USER_ACTIVATION_CHANGED = "user_activation_changed", "User activated/deactivated"

    action = models.CharField(max_length=32, choices=Action.choices)
    entity_type = models.CharField(
        max_length=64,
        help_text="e.g. 'donation', 'bloodinventory', 'bloodrequest', 'user'.",
    )
    entity_id = models.CharField(max_length=64)
    previous_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
        help_text="Who performed the action. Null only for system/migration-generated entries.",
    )
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["action"]),
        ]

    def __str__(self):
        return f"{self.get_action_display()} on {self.entity_type}#{self.entity_id} at {self.created_at:%Y-%m-%d %H:%M}"


def record(action, *, entity_type, entity_id, actor=None, previous_value="", new_value="", reason=""):
    """
    Single entry point every app uses to write an audit entry, so there is
    exactly one place that decides what a row looks like. Callers are
    expected to call this inside the same `transaction.atomic()` block as
    the business-logic write it documents, per the Jira requirement that
    the audit entry and the operation it records must succeed together.
    """
    return AuditLog.objects.create(
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        actor=actor,
        previous_value=str(previous_value) if previous_value else "",
        new_value=str(new_value) if new_value else "",
        reason=reason,
    )
