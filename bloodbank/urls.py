
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

    # Donation Management (Part 3.A): recording, donor-own history,
    # staff/donor-scoped history views and search.
    path("", include("donations.urls")),

    # Staff/admin audit trail (Part 4).
    path("", include("auditlog.urls")),

    # Administrator-only user management (Part 3.D).
    path("", include("accounts.urls")),

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
