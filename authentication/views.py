from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import UsernameOrEmailAuthenticationForm


class LoginView(auth_views.LoginView):
    """Django's built-in session login, using the username-or-email form."""

    template_name = "authentication/login.html"
    authentication_form = UsernameOrEmailAuthenticationForm
    redirect_authenticated_user = True


@login_required
def home(request):
    """Minimal protected landing page (BBMS-SR-001)."""
    return render(request, "authentication/home.html")
