import uuid

from django.core.validators import MinValueValidator
from django.db import models

from bloodbank.constants import BLOOD_GROUP_CHOICES


class BloodRequest(models.Model):
    class BloodGroup(models.TextChoices):
        """
        Named members kept for readability in code/tests (e.g.
        BloodGroup.O_POSITIVE). The (value, label) pairs themselves must
        stay identical to bloodbank.constants.BLOOD_GROUP_CHOICES -- the
        test suite's test_blood_group_choices_match_shared_constant guards
        against the two silently diverging again.
        """
        A_POSITIVE = 'A+', 'A+'
        A_NEGATIVE = 'A-', 'A-'
        B_POSITIVE = 'B+', 'B+'
        B_NEGATIVE = 'B-', 'B-'
        AB_POSITIVE = 'AB+', 'AB+'
        AB_NEGATIVE = 'AB-', 'AB-'
        O_POSITIVE = 'O+', 'O+'
        O_NEGATIVE = 'O-', 'O-'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        FULFILLED = 'fulfilled', 'Fulfilled'

    tracking_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    requester_name = models.CharField(max_length=120)
    requester_email = models.EmailField()
    hospital_name = models.CharField(max_length=160)
    blood_group = models.CharField(max_length=3, choices=BloodGroup.choices)
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text='Number of blood units required.',
    )
    purpose = models.TextField(max_length=500)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
    )
    review_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        'auth.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_blood_requests',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'blood request'
        verbose_name_plural = 'blood requests'

    def __str__(self):
        return f'{self.tracking_id} - {self.blood_group} ({self.quantity} units)'


# The per-blood-group aggregate BloodInventory model that used to live here
# was removed in this patch (see inventory/models.py's BloodInventory and
# docs/KNOWN_ISSUES.md #1). inventory.BloodInventory (batch-level) is now
# the one stock table in the project; its data migration
# (requests/migrations/0003_remove_duplicate_inventory.py) converts any
# existing aggregate rows into batches before dropping this table, so no
# stock numbers are lost.


class BloodIssue(models.Model):
    class Status(models.TextChoices):
        ISSUED = 'issued', 'Issued'
        REVERSED = 'reversed', 'Reversed'

    request = models.OneToOneField(
        BloodRequest,
        on_delete=models.PROTECT,
        related_name='issue_transaction',
    )
    blood_group = models.CharField(max_length=3, choices=BloodRequest.BloodGroup.choices)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ISSUED)
    issued_by = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='blood_issues')
    issue_note = models.TextField(blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-issued_at',)

    def __str__(self):
        return f'Issue for {self.request.tracking_id}: {self.quantity} units'