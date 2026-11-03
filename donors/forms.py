from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UsernameField
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import BLOOD_GROUP_CHOICES, DonorProfile

User = get_user_model()


class DonorRegistrationForm(forms.Form):
    """
    Public self-registration form (BBMS-F-003).

    Deliberately NOT a ModelForm against auth.User with is_staff/is_superuser
    exposed: those fields simply do not appear on this form, so there is no
    value a requester can submit (not even by tampering with hidden fields)
    that grants anything above the Donor role. save() always creates the
    account with is_staff=False, is_superuser=False -- the minimum-privilege
    role is the only outcome this form can produce.
    """

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    username = UsernameField(max_length=150)
    email = forms.EmailField(max_length=254)
    phone_number = forms.CharField(max_length=20)
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="YYYY-MM-DD.",
    )
    blood_group = forms.ChoiceField(choices=BLOOD_GROUP_CHOICES)
    address = forms.CharField(max_length=500, widget=forms.Textarea(attrs={"rows": 3}))
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput, strip=False)
    password2 = forms.CharField(
        label="Confirm password", widget=forms.PasswordInput, strip=False
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("That username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this e-mail address already exists.")
        return email

    def clean_date_of_birth(self):
        dob = self.cleaned_data["date_of_birth"]
        if dob >= timezone.localdate():
            raise ValidationError("Date of birth must be in the past.")
        return dob

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields did not match.")
        return password2

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password1")
        if password:
            # Reuses the project's configured AUTH_PASSWORD_VALIDATORS
            # (BBMS-SR-004 groundwork) rather than inventing separate rules.
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned_data

    def save(self):
        """Create the User (minimum privilege) and its DonorProfile together."""
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password1"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            is_staff=False,
            is_superuser=False,
        )
        profile = DonorProfile.objects.create(
            user=user,
            phone_number=data["phone_number"],
            date_of_birth=data["date_of_birth"],
            blood_group=data["blood_group"],
            address=data["address"],
        )
        return user, profile


class DonorProfileUpdateForm(forms.ModelForm):
    """Donor self-service update of their own contact details (BBMS-F-004).

    Eligibility fields are intentionally absent from this form's `fields`
    tuple -- there is no way to submit a change to them through this view,
    which is how "a donor cannot modify their own eligibility" is enforced,
    not just a view-level check.
    """

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField(max_length=254)

    class Meta:
        model = DonorProfile
        fields = ("phone_number", "date_of_birth", "blood_group", "address")
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user is not None and not self.is_bound:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError("Another account already uses this e-mail address.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if self.user is not None:
            self.user.first_name = self.cleaned_data["first_name"]
            self.user.last_name = self.cleaned_data["last_name"]
            self.user.email = self.cleaned_data["email"]
            if commit:
                self.user.save(update_fields=("first_name", "last_name", "email"))
        return profile


class EligibilityUpdateForm(forms.Form):
    """Staff-only change of a donor's eligibility status (BBMS-F-006)."""

    eligibility_status = forms.ChoiceField(choices=DonorProfile.Eligibility.choices)
    note = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={"placeholder": "Reason (optional)"}),
    )
