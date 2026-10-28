from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _


class UsernameOrEmailAuthenticationForm(AuthenticationForm):
    """
    Login form that accepts either a username or an e-mail address (BBMS-F-001).

    The identifier is resolved to a username before Django's own
    AuthenticationForm.clean() runs, so authentication, the inactive-user check
    and password verification are all done by Django's built-in machinery.
    """

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": _(
            "Please enter a correct username/email and password. "
            "Note that both fields may be case-sensitive."
        ),
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        field = self.fields["username"]
        field.label = _("Username or email")
        field.max_length = 254  # long enough for any e-mail address
        field.widget.attrs["maxlength"] = 254

    def clean(self):
        identifier = self.cleaned_data.get("username")
        if identifier:
            self.cleaned_data["username"] = self._resolve_username(identifier)
        return super().clean()

    @staticmethod
    def _resolve_username(identifier):
        """
        Return the username to authenticate with.

        1. An exact username match always wins.
        2. Otherwise, if the identifier looks like an e-mail address and matches
           exactly one account (case-insensitively), use that account's username.
        3. Otherwise return the identifier unchanged (authentication will fail).
           An e-mail shared by several accounts is deliberately treated as
           ambiguous and rejected, because auth.User.email is not unique.
        """
        User = get_user_model()
        username_field = User.USERNAME_FIELD

        if User._default_manager.filter(**{username_field: identifier}).exists():
            return identifier

        if "@" in identifier:
            usernames = list(
                User._default_manager.filter(email__iexact=identifier)
                .values_list(username_field, flat=True)[:2]
            )
            if len(usernames) == 1:
                return usernames[0]

        return identifier
