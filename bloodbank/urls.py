
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Inventory management
    path("", include("inventory.urls")),

    # Blood requests and distribution
    path("requests/", include("requests.urls")),

    # Redirect the root URL to the authentication login page
    path(
        "",
        RedirectView.as_view(
            pattern_name="authentication:login",
            permanent=False,
        ),
        name="index",
    ),

    # Login, logout, and authenticated home page
    path("", include("authentication.urls")),
]
