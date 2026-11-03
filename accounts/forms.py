from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms


class AdminUserCreateForm(UserCreationForm):
    """
    Administrator-only account creation (Part 3.D). Uses Django's own
    UserCreationForm (password hashing, password-match validation, the
    project's AUTH_PASSWORD_VALIDATORS) rather than a hand-rolled
    equivalent -- Part 3.D explicitly asks for this ("do not duplicate
    Django's user authentication system").

    Role is a separate, explicit field rather than letting a caller submit
    is_staff/is_superuser directly, so "create account" and "grant admin"
    are always two distinct, auditable actions -- and so this form's
    `role` choices can be restricted at the view layer for a staff-level
    creator without touching the model fields it ultimately sets.
    """

    ROLE_DONOR = "donor"
    ROLE_STAFF = "staff"
    ROLE_ADMIN = "admin"
    ROLE_CHOICES = [
        (ROLE_DONOR, "Donor (no staff access)"),
        (ROLE_STAFF, "Blood bank staff"),
        (ROLE_ADMIN, "Administrator"),
    ]

    email = forms.EmailField(required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial=ROLE_DONOR)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")
        role = self.cleaned_data["role"]
        user.is_staff = role in (self.ROLE_STAFF, self.ROLE_ADMIN)
        user.is_superuser = role == self.ROLE_ADMIN
        if commit:
            user.save()
        return user


class AdminUserUpdateForm(forms.ModelForm):
    """Editing an existing account's basic details (not password, not role -- role has its own form/view)."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")


class RoleChangeForm(forms.Form):
    role = forms.ChoiceField(choices=AdminUserCreateForm.ROLE_CHOICES)


class UserSearchForm(forms.Form):
    q = forms.CharField(required=False, label="Search")
    role = forms.ChoiceField(
        required=False,
        choices=[("", "All roles")] + AdminUserCreateForm.ROLE_CHOICES,
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All"), ("active", "Active"), ("inactive", "Inactive")],
    )
