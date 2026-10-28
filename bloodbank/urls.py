
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Inventory management
    path("", include("inventory.urls")),

    # Blood requests and distribution
    path("requests/", include("requests.urls")),

    # Donor self-registration, donor self-service profile, and staff donor
    # management (BBMS-F-003, BBMS-F-004, BBMS-F-005, BBMS-F-006).
    path("donors/", include("donors.urls")),

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
