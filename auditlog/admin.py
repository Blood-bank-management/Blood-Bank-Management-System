from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "entity_type", "entity_id", "actor", "created_at")
    list_filter = ("action", "entity_type")
    search_fields = ("entity_id", "reason")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        # Audit entries are written only by application code via
        # auditlog.models.record(), never hand-typed -- see Part 4
        # ("Audit history must not be casually editable or deletable").
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
