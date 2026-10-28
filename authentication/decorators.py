"""
Server-side RBAC helpers (BBMS-SR-001, BBMS-SR-002), shared by every app.

Role model used across the project (see README.md "Role-permission matrix"):

  Anonymous         -- not logged in.
  Donor             -- a logged-in user with is_staff=False, is_superuser=False.
                       This is the floor that donor self-registration grants;
                       it is not stored anywhere as a separate label.
  Blood Bank Staff  -- is_staff=True.
  Administrator     -- is_superuser=True (also satisfies is_staff checks,
                       since Django gives superusers every permission).

These decorators are the enforcement point, independent of whatever the UI
shows or hides. Hiding a "Donors" link from a donor's nav bar is not a
security control; every staff-only view in inventory, requests and donors
calls staff_required explicitly so the check happens on every request,
regardless of which link (if any) was used to reach it.
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def staff_required(view_func):
    """
    Allow authenticated staff/admin users only.

    - Anonymous requests redirect to login (consistent with every other
      protected page in the project, BBMS-SR-001).
    - Authenticated non-staff requests get HTTP 403, not a redirect: the
      user is who they say they are, they are simply not allowed to see
      this (BBMS-SR-002). A redirect-to-login loop would be misleading.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied("This page is restricted to blood bank staff.")
        return view_func(request, *args, **kwargs)
    return wrapper
