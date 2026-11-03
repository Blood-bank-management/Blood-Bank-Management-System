"""
Project-wide domain constants and shared validation helpers.

Before this patch, the eight-blood-group choice list was defined three times
independently (donors.models.BLOOD_GROUP_CHOICES, requests.models.
BloodRequest.BloodGroup, and a bare list literal repeated in every
inventory.views function). That is a real risk: adding "O+ (apheresis)" or
fixing a typo in one copy and not the others would silently desynchronize
validation across apps. This module is the one place that list is defined;
every app imports from here instead of re-declaring it.
"""
from django.core.exceptions import ValidationError
from django.utils import timezone


BLOOD_GROUP_CHOICES = [
    ("A+", "A+"), ("A-", "A-"),
    ("B+", "B+"), ("B-", "B-"),
    ("AB+", "AB+"), ("AB-", "AB-"),
    ("O+", "O+"), ("O-", "O-"),
]

BLOOD_GROUPS = [code for code, _label in BLOOD_GROUP_CHOICES]

# Shelf life for a whole-blood donation. This is a documented project
# assumption, not an SRS-stated clinical rule (the bundled SRS does not
# specify a shelf-life figure): 42 days / 6 weeks is the commonly cited
# storage limit for CPDA-1 anticoagulated whole blood. Staff can always
# override the computed expiry date when recording a donation if their
# blood bank's actual policy differs; see docs/KNOWN_ISSUES.md.
WHOLE_BLOOD_SHELF_LIFE_DAYS = 42

# Minimum days that must elapse before a donor is eligible to donate again.
# Also a documented assumption (WHO commonly cites ~90 days for whole-blood
# donors), not an SRS-stated figure -- see docs/KNOWN_ISSUES.md.
MIN_DAYS_BETWEEN_DONATIONS = 90


def validate_positive_quantity(value):
    """Shared by Donation, BloodInventory and issue/adjustment forms."""
    if value is None or value <= 0:
        raise ValidationError("Quantity must be a positive number of units.")


def validate_not_future_date(value, *, field_name="Date"):
    """
    Collection dates, donation dates, etc. must not be in the future.
    Expiry dates are deliberately NOT validated with this helper -- expiry
    is always after collection, i.e. usually in the future relative to
    collection, which is exactly what makes it a different rule.
    """
    if value and value > timezone.localdate():
        raise ValidationError(f"{field_name} cannot be in the future.")
