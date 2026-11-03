from django import forms


class InventoryAdjustmentForm(forms.Form):
    """Manual correction to a single batch's balance. Requires a reason (Part 2.A)."""

    delta = forms.IntegerField(
        label="Adjustment (+/- units)",
        help_text="Positive to add units back, negative to remove (e.g. spoilage).",
    )
    reason = forms.CharField(
        max_length=255,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text="Required -- why is this batch being adjusted?",
    )

    def clean_delta(self):
        delta = self.cleaned_data["delta"]
        if delta == 0:
            raise forms.ValidationError("Adjustment cannot be zero.")
        return delta
