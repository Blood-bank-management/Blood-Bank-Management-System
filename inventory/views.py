from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from authentication.decorators import staff_required
from bloodbank.constants import BLOOD_GROUPS
from .forms import InventoryAdjustmentForm
from .models import BloodInventory, InventoryTransaction
from .services import adjust_batch, available_units


def home(request):
    return redirect("inventory:availability_search")


@login_required
def availability_search(request):
    """Unchanged access control from before this patch: login required, no role check."""
    blood_group = request.GET.get("blood_group", "").strip()

    result = None
    message = None

    if not blood_group:
        message = "Please select a blood group."
    elif blood_group not in BLOOD_GROUPS:
        message = "Unsupported blood group."
    else:
        result = available_units(blood_group)
        if result == 0:
            message = "No blood available for this blood group."

    return render(
        request,
        "inventory/availability_search.html",
        {
            "blood_group": blood_group,
            "result": result,
            "message": message,
            "blood_groups": BLOOD_GROUPS,
        },
    )


@staff_required
def inventory_summary(request):
    """Staff inventory dashboard: per-group availability, batch counts, and expiring-soon warnings."""
    today = timezone.localdate()
    soon = today + timezone.timedelta(days=7)

    inventory = []
    for group in BLOOD_GROUPS:
        batches = BloodInventory.objects.filter(
            blood_group=group, expiry_date__gte=today, quantity_remaining__gt=0,
        )
        inventory.append({
            "blood_group": group,
            "quantity": sum(b.quantity_remaining for b in batches),
            "batch_count": batches.count(),
            "expiring_soon": batches.filter(expiry_date__lte=soon).count(),
        })

    recent_transactions = (
        InventoryTransaction.objects.select_related("batch", "performed_by").order_by("-created_at")[:15]
    )

    return render(
        request,
        "inventory/inventory_summary.html",
        {"inventory": inventory, "recent_transactions": recent_transactions},
    )


@staff_required
def batch_list(request):
    """Full batch-level detail (Part 2.A 'include batch details'), with search/pagination."""
    blood_group = request.GET.get("blood_group", "").strip()
    batches = BloodInventory.objects.select_related("source_donation").order_by("expiry_date")
    if blood_group:
        batches = batches.filter(blood_group=blood_group)

    paginator = Paginator(batches, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "inventory/batch_list.html",
        {"page_obj": page_obj, "blood_group": blood_group, "blood_groups": BLOOD_GROUPS},
    )


@staff_required
def batch_detail(request, pk):
    batch = get_object_or_404(BloodInventory, pk=pk)

    if request.method == "POST":
        form = InventoryAdjustmentForm(request.POST)
        if form.is_valid():
            try:
                adjust_batch(
                    batch=batch,
                    delta=form.cleaned_data["delta"],
                    performed_by=request.user,
                    reason=form.cleaned_data["reason"],
                )
                messages.success(request, "Batch adjusted.")
                return redirect("inventory:batch_detail", pk=pk)
            except ValidationError as exc:
                messages.error(request, "; ".join(exc.messages))
    else:
        form = InventoryAdjustmentForm()

    transactions = batch.transactions.select_related("performed_by").order_by("-created_at")
    return render(
        request,
        "inventory/batch_detail.html",
        {"batch": batch, "form": form, "transactions": transactions},
    )


@staff_required
def expired_units(request):
    expired = BloodInventory.objects.filter(expiry_date__lt=timezone.localdate())
    return render(request, "inventory/expired_units.html", {"expired_units": expired})
