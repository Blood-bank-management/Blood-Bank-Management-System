from django.contrib import admin

from .models import DonorProfile


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "blood_group", "eligibility_status", "eligibility_updated_at")
    list_filter = ("blood_group", "eligibility_status")
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email")
    readonly_fields = ("eligibility_updated_by", "eligibility_updated_at", "created_at", "updated_at")
    autocomplete_fields = ("user",)
