from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "authentication"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    # Built-in LogoutView: POST-only, CSRF-protected, flushes the session and
    # redirects to settings.LOGOUT_REDIRECT_URL.
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("home/", views.home, name="home"),
]
