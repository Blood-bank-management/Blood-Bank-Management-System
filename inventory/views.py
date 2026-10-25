
from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import BloodInventory


@login_required
def availability_search(request):
    blood_group = request.GET.get("blood_group", "").strip()

    valid_groups = [
        "A+", "A-", "B+", "B-",
        "AB+", "AB-", "O+", "O-"
    ]

    result = None
    message = None

    if not blood_group:
        message = "Please select a blood group."

    elif blood_group not in valid_groups:
        message = "Unsupported blood group."

    else:
        result = sum(
            item.quantity
            for item in BloodInventory.objects.filter(
                blood_group=blood_group,
                expiry_date__gte=date.today()
            )
        )

        if result == 0:
            message = "No blood available for this blood group."

    return render(
        request,
        "inventory/availability_search.html",
        {
            "blood_group": blood_group,
            "result": result,
            "message": message,
        },
    )


@login_required
def inventory_summary(request):
    valid_groups = [
        "A+", "A-", "B+", "B-",
        "AB+", "AB-", "O+", "O-"
    ]

    inventory = []

    for group in valid_groups:
        total = sum(
            item.quantity
            for item in BloodInventory.objects.filter(
                blood_group=group,
                expiry_date__gte=date.today()
            )
        )

        inventory.append({
            "blood_group": group,
            "quantity": total,
        })

    return render(
        request,
        "inventory/inventory_summary.html",
        {"inventory": inventory},
    )
