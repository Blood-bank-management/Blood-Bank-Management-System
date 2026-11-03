from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from authentication.decorators import staff_required
from bloodbank.constants import BLOOD_GROUPS
from donors.models import DonorProfile

from .forms import DonationRecordForm
from .models import Donation
from .services import DuplicateDonationError, record_donation


@staff_required
def record(request):
    """Staff records a donation (Part 3.A.1/2)."""
    if request.method == "POST":
        form = DonationRecordForm(request.POST)
        if form.is_valid():
            try:
                donation = record_donation(
                    donor=form.cleaned_data["donor_username"],
                    blood_group=form.cleaned_data["blood_group"],
                    quantity=form.cleaned_data["quantity"],
                    collection_date=form.cleaned_data["collection_date"],
                    collection_reference=form.cleaned_data["collection_reference"],
                    recorded_by=request.user,
                    notes=form.cleaned_data["notes"],
                    status=form.cleaned_data["outcome"],
                    rejection_reason=form.cleaned_data["rejection_reason"],
                )
            except DuplicateDonationError as exc:
                form.add_error("collection_reference", str(exc))
            else:
                if donation.is_successful:
                    messages.success(
                        request,
                        f"Donation recorded: {donation.quantity} unit(s) of "
                        f"{donation.blood_group} credited to inventory.",
                    )
                else:
                    messages.warning(request, "Donation recorded as rejected -- no stock was credited.")
                return redirect("donations:list")
    else:
        form = DonationRecordForm()

    return render(request, "donations/record.html", {"form": form})


@staff_required
def donation_list(request):
    """Staff search/filter over all donation records (Part 3.A.4)."""
    donor_username = request.GET.get("donor", "").strip()
    blood_group = request.GET.get("blood_group", "").strip()
    status = request.GET.get("status", "").strip()

    donations = Donation.objects.select_related("donor__user", "recorded_by")
    if donor_username:
        donations = donations.filter(donor__user__username__icontains=donor_username)
    if blood_group and blood_group in BLOOD_GROUPS:
        donations = donations.filter(blood_group=blood_group)
    if status in dict(Donation.Status.choices):
        donations = donations.filter(status=status)

    paginator = Paginator(donations, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "donations/donation_list.html",
        {
            "page_obj": page_obj,
            "donor_username": donor_username,
            "blood_group": blood_group,
            "status": status,
            "blood_groups": BLOOD_GROUPS,
            "status_choices": Donation.Status.choices,
        },
    )


@login_required
def my_donation_history(request):
    """
    Donor's own donation history (Part 3.A.3). No pk/id is taken from the
    URL -- same IDOR defence pattern as donors.views.profile: this view
    only ever looks at request.user's own DonorProfile, so there is no
    identifier for another donor's history to be reached through.
    """
    donor_profile = getattr(request.user, "donor_profile", None)
    if donor_profile is None:
        messages.info(request, "Your account does not have a donor profile.")
        return redirect("authentication:home")

    donations = Donation.objects.filter(donor=donor_profile).order_by("-collection_date")
    paginator = Paginator(donations, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "donations/my_history.html", {"page_obj": page_obj})


@staff_required
def donor_donation_history(request, pk):
    """Staff viewing a specific donor's donation history, for operational purposes (Part 3.A.3)."""
    donor_profile = get_object_or_404(DonorProfile, pk=pk)
    donations = Donation.objects.filter(donor=donor_profile).order_by("-collection_date")
    return render(
        request,
        "donations/donor_history.html",
        {"donor_profile": donor_profile, "donations": donations},
    )
