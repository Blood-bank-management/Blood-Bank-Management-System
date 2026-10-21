from django.contrib import admin

from .models import BloodRequest


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('tracking_id', 'hospital_name', 'blood_group', 'quantity', 'status', 'created_at')
    list_filter = ('status', 'blood_group')
    search_fields = ('tracking_id', 'requester_name', 'requester_email', 'hospital_name')
    readonly_fields = ('tracking_id', 'created_at', 'updated_at', 'reviewed_at')