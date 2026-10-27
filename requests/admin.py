from django.contrib import admin

from .models import BloodInventory, BloodIssue, BloodRequest


@admin.register(BloodInventory)
class BloodInventoryAdmin(admin.ModelAdmin):
    list_display = ('blood_group', 'available_units', 'updated_at')
    list_filter = ('blood_group',)


@admin.register(BloodIssue)
class BloodIssueAdmin(admin.ModelAdmin):
    list_display = ('request', 'blood_group', 'quantity', 'status', 'issued_by', 'issued_at')
    list_filter = ('status', 'blood_group')
    search_fields = ('request__tracking_id', 'request__hospital_name')
    readonly_fields = ('issued_at',)


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('tracking_id', 'hospital_name', 'blood_group', 'quantity', 'status', 'created_at')
    list_filter = ('status', 'blood_group')
    search_fields = ('tracking_id', 'requester_name', 'requester_email', 'hospital_name')
    readonly_fields = ('tracking_id', 'created_at', 'updated_at', 'reviewed_at')