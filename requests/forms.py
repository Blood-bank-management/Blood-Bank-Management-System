from django import forms

from .models import BloodRequest


class BloodRequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = (
            'requester_name',
            'requester_email',
            'hospital_name',
            'blood_group',
            'quantity',
            'purpose',
        )
        widgets = {
            'purpose': forms.Textarea(attrs={'rows': 4}),
            'quantity': forms.NumberInput(attrs={'min': 1}),
        }


class ReviewForm(forms.Form):
    action = forms.ChoiceField(
        choices=(
            (BloodRequest.Status.APPROVED, 'Approve request'),
            (BloodRequest.Status.REJECTED, 'Reject request'),
        ),
        widget=forms.RadioSelect,
    )
    review_note = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={'rows': 3}),
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('action') == BloodRequest.Status.REJECTED and not cleaned_data.get('review_note'):
            self.add_error('review_note', 'Add a reason when rejecting a request.')
        return cleaned_data