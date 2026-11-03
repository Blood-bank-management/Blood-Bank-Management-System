from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from .forms import UsernameOrEmailAuthenticationForm


class LoginView(auth_views.LoginView):
    """Django's built-in session login, using the username-or-email form."""

    template_name = "authentication/login.html"
    authentication_form = UsernameOrEmailAuthenticationForm
    redirect_authenticated_user = True


@login_required
def home(request):
    """
    Role-aware dashboard (Part 7.D). Staff/admin see operational metrics
    drawn from real queries against the current database; donors see a
    personal summary. Nothing here is hardcoded mock data -- an empty
    database renders zeros/empty states, not placeholder numbers.
    """
    if request.user.is_staff:
        context = _staff_dashboard_context()
        template = "authentication/home.html"
    else:
        context = _donor_dashboard_context(request.user)
        template = "authentication/home.html"
    return render(request, template, context)


def _staff_dashboard_context():
    from auditlog.models import AuditLog
    from bloodbank.constants import BLOOD_GROUPS
    from donations.models import Donation
    from inventory.models import BloodInventory
    from inventory.services import available_units
    from requests.models import BloodIssue, BloodRequest

    today = timezone.localdate()
    soon = today + timezone.timedelta(days=7)

    blood_group_distribution = [
        {"blood_group": g, "units": available_units(g)} for g in BLOOD_GROUPS
    ]
    total_available_units = sum(row["units"] for row in blood_group_distribution)
    max_units = max((row["units"] for row in blood_group_distribution), default=0) or 1

    return {
        "is_staff_dashboard": True,
        "total_available_units": total_available_units,
        "blood_group_distribution": blood_group_distribution,
        "max_units": max_units,
        "pending_requests": BloodRequest.objects.filter(status=BloodRequest.Status.PENDING).count(),
        "approved_requests": BloodRequest.objects.filter(status=BloodRequest.Status.APPROVED).count(),
        "recent_donations": Donation.objects.select_related("donor__user").order_by("-created_at")[:5],
        "recent_issues": BloodIssue.objects.select_related("request", "issued_by").order_by("-issued_at")[:5],
        "expiring_batches": BloodInventory.objects.filter(
            expiry_date__gte=today, expiry_date__lte=soon, quantity_remaining__gt=0,
        ).order_by("expiry_date")[:5],
        "recent_audit_entries": AuditLog.objects.select_related("actor").order_by("-created_at")[:5],
    }


def _donor_dashboard_context(user):
    from donations.models import Donation, next_eligible_date

    donor_profile = getattr(user, "donor_profile", None)
    if donor_profile is None:
        return {"is_staff_dashboard": False, "donor_profile": None}

    return {
        "is_staff_dashboard": False,
        "donor_profile": donor_profile,
        "recent_donations": Donation.objects.filter(donor=donor_profile).order_by("-collection_date")[:5],
        "donation_count": Donation.objects.filter(donor=donor_profile, status=Donation.Status.RECORDED).count(),
        "next_eligible_date": next_eligible_date(donor_profile),
    }
