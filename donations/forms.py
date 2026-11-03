from django import forms
from django.utils import timezone

from bloodbank.constants import BLOOD_GROUP_CHOICES
from donors.models import DonorProfile

from .models import Donation


class DonationRecordForm(forms.Form):
    """
    Staff-facing donation recording form (Part 3.A.1). Deliberately a plain
    Form, not a ModelForm bound to Donation, because `donor` is looked up by
    username/ID with real validation (must be an existing donor, not just
    any integer) and `recorded_by`/status transitions are server-controlled,
    not form input.
    """

    donor_username = forms.CharField(label="Donor username")
    blood_group = forms.ChoiceField(choices=BLOOD_GROUP_CHOICES)
    quantity = forms.IntegerField(min_value=1, label="Quantity (units)")
    collection_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    collection_reference = forms.CharField(
        max_length=64,
        help_text="A unique reference for this collection (bag/barcode number).",
    )
    outcome = forms.ChoiceField(
        choices=Donation.Status.choices,
        initial=Donation.Status.RECORDED,
        label="Outcome",
    )
    rejection_reason = forms.CharField(
        max_length=255, required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
    notes = forms.CharField(max_length=255, required=False)

    def clean_donor_username(self):
        username = self.cleaned_data["donor_username"].strip()
        try:
            return DonorProfile.objects.select_related("user").get(user__username=username)
        except DonorProfile.DoesNotExist:
            raise forms.ValidationError("No donor with this username was found.")

    def clean_collection_date(self):
        collection_date = self.cleaned_data["collection_date"]
        if collection_date > timezone.localdate():
            raise forms.ValidationError("Collection date cannot be in the future.")
        return collection_date

    def clean_collection_reference(self):
        reference = self.cleaned_data["collection_reference"].strip()
        if not reference:
            raise forms.ValidationError("A collection reference is required.")
        if Donation.objects.filter(collection_reference=reference).exists():
            raise forms.ValidationError(
                "This collection reference has already been recorded."
            )
        return reference

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("outcome") == Donation.Status.REJECTED and not cleaned.get("rejection_reason"):
            self.add_error("rejection_reason", "A reason is required when the outcome is Rejected.")
        return cleaned
