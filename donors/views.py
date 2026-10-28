from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import staff_required
from .forms import DonorProfileUpdateForm, DonorRegistrationForm, EligibilityUpdateForm
from .models import DonorProfile


def register(request):
    """Public donor self-registration (BBMS-F-003).

    Open to anyone, logged in or not -- it is the one donors.* view with no
    access check, because being allowed to register is the whole point.
    Every account it creates lands with the minimum-privilege Donor role
    (see DonorRegistrationForm.save): there is no path from this form to
    is_staff or is_superuser.
    """
    if request.user.is_authenticated:
        return redirect("authentication:home")

    if request.method == "POST":
        form = DonorRegistrationForm(request.POST)
        if form.is_valid():
            user, _profile = form.save()
            login(request, user)
            messages.success(
                request,
                f"Welcome, {user.first_name or user.get_username()}! "
                "Your donor account has been created.",
            )
            return redirect("authentication:home")
    else:
        form = DonorRegistrationForm()

    return render(request, "donors/register.html", {"form": form})


@login_required
def profile(request):
    """A donor viewing/updating their own profile (BBMS-F-004).

    This view never takes an id/pk from the URL or request body -- it always
    operates on request.user's own DonorProfile. That is the IDOR defence
    for self-service profile access: there is no identifier for an attacker
    to swap out, by construction, rather than an ownership check that could
    be forgotten in a future edit.

    Staff/admin accounts created outside the registration flow (e.g. via
    createsuperuser or the seed command) have no DonorProfile; they are
    sent to the staff donor list instead of hitting a 404 here.
    """
    donor_profile = getattr(request.user, "donor_profile", None)
    if donor_profile is None:
        if request.user.is_staff:
            return redirect("donors:list")
        messages.info(
            request,
            "Your account does not have a donor profile. Contact blood bank staff.",
        )
        return redirect("authentication:home")

    if request.method == "POST":
        form = DonorProfileUpdateForm(request.POST, instance=donor_profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("donors:profile")
    else:
        form = DonorProfileUpdateForm(instance=donor_profile, user=request.user)

    return render(request, "donors/profile.html", {"form": form, "donor_profile": donor_profile})


@staff_required
def donor_list(request):
    """Staff-only list of registered donors (BBMS-F-005)."""
    query = request.GET.get("q", "").strip()
    donors = DonorProfile.objects.select_related("user").order_by("user__username")
    if query:
        donors = donors.filter(
            Q(user__username__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__email__icontains=query)
            | Q(blood_group__icontains=query)
        )
    paginator = Paginator(donors, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "donors/donor_list.html", {"page_obj": page_obj, "query": query})


@staff_required
def donor_detail(request, pk):
    """
    Staff-only single donor record, including eligibility management
    (BBMS-F-005, BBMS-F-006).

    `pk` is the donor's primary key, taken straight from the URL -- this is
    an ID-accepting endpoint. The authorization here is role-based
    (@staff_required), not ownership-based: any staff/admin account may view
    any donor, which is exactly what BBMS-F-005 asks for, and any
    non-staff caller is rejected before pk is even looked up. Nothing about
    this URL's safety depends on pk being hard to guess.
    """
    donor_profile = get_object_or_404(DonorProfile, pk=pk)

    if request.method == "POST":
        form = EligibilityUpdateForm(request.POST)
        if form.is_valid():
            donor_profile.set_eligibility(
                form.cleaned_data["eligibility_status"],
                changed_by=request.user,
                note=form.cleaned_data["note"],
            )
            messages.success(
                request,
                f"{donor_profile.user.get_username()}'s eligibility status was updated.",
            )
            return redirect("donors:detail", pk=pk)
    else:
        form = EligibilityUpdateForm(initial={
            "eligibility_status": donor_profile.eligibility_status,
        })

    return render(
        request,
        "donors/donor_detail.html",
        {"donor_profile": donor_profile, "form": form},
    )
