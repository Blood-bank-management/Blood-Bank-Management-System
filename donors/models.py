from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


BLOOD_GROUP_CHOICES = [
    ("A+", "A+"), ("A-", "A-"),
    ("B+", "B+"), ("B-", "B-"),
    ("AB+", "AB+"), ("AB-", "AB-"),
    ("O+", "O+"), ("O-", "O-"),
]

PHONE_VALIDATOR = RegexValidator(
    regex=r"^\+?[0-9 ()-]{7,17}$",
    message="Enter a valid phone number (7-17 digits, optionally with +, spaces, "
            "hyphens or parentheses).",
)


class DonorProfile(models.Model):
    """
    Extended donor information for an auth.User account (BBMS-F-003, BBMS-F-004).

    One profile per user. A profile is created automatically at registration
    time by donors.views.register; it is never created implicitly elsewhere,
    so "a DonorProfile exists" and "this account registered as a donor" are
    the same fact.
    """

    class Eligibility(models.TextChoices):
        ELIGIBLE = "eligible", "Eligible"
        TEMPORARILY_INELIGIBLE = "temporarily_ineligible", "Temporarily ineligible"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="donor_profile",
        primary_key=True,
    )
    phone_number = models.CharField(max_length=20, validators=[PHONE_VALIDATOR])
    date_of_birth = models.DateField()
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    address = models.TextField(max_length=500)

    # BBMS-F-006: staff-set eligibility. The SRS acceptance criterion links this
    # to donation history (BBMS-F-007/008/009), but the Blood Donation Management
    # module (a teammate's Sprint 2 responsibility) does not exist in this
    # repository yet, so there is nothing to compute eligibility from
    # automatically. Until that module lands, staff set this field directly from
    # whatever donation record they are looking at outside the system. This is a
    # documented limitation, not a silent gap -- see the Sprint 2 reports.
    eligibility_status = models.CharField(
        max_length=24,
        choices=Eligibility.choices,
        default=Eligibility.ELIGIBLE,
    )
    eligibility_note = models.CharField(max_length=255, blank=True)
    eligibility_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Staff member who last changed this donor's eligibility status.",
    )
    eligibility_updated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("user__username",)
        verbose_name = "donor profile"
        verbose_name_plural = "donor profiles"

    def __str__(self):
        return f"Donor profile: {self.user.get_username()}"

    def set_eligibility(self, status, *, changed_by, note=""):
        """
        Update eligibility and stamp who changed it and when (BBMS-SR-005
        audit groundwork). Callers are responsible for checking that
        `changed_by` is authorized (donors.decorators.staff_required) --
        this method does not re-check authorization itself, by design, so it
        stays usable from the admin site and management commands too.
        """
        self.eligibility_status = status
        self.eligibility_note = note
        self.eligibility_updated_by = changed_by
        self.eligibility_updated_at = timezone.now()
        self.save(update_fields=(
            "eligibility_status", "eligibility_note",
            "eligibility_updated_by", "eligibility_updated_at", "updated_at",
        ))
