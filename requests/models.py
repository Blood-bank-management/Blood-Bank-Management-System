import uuid

from django.core.validators import MinValueValidator
from django.db import models


class BloodRequest(models.Model):
    class BloodGroup(models.TextChoices):
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