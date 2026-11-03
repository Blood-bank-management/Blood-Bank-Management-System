from django.contrib import admin

from .models import Donation


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("collection_reference", "donor", "blood_group", "quantity", "status", "collection_date")
    list_filter = ("status", "blood_group")
    search_fields = ("collection_reference", "donor__user__username")
