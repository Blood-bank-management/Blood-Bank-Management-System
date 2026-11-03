from django.core.paginator import Paginator
from django.shortcuts import render

from authentication.decorators import staff_required
from .models import AuditLog


@staff_required
def audit_log_list(request):
    """
    Staff/admin audit trail (Part 4). Staff-level, not admin-only: Jira asks
    for "an administrator/staff audit-log view", and operational staff
    reviewing donation/inventory/request history is a normal, legitimate
    need, distinct from the admin-only *user*-management views in
    accounts/views.py.
    """
    action = request.GET.get("action", "").strip()
    entity_type = request.GET.get("entity_type", "").strip()

    entries = AuditLog.objects.select_related("actor")
    if action:
        entries = entries.filter(action=action)
    if entity_type:
        entries = entries.filter(entity_type=entity_type)

    paginator = Paginator(entries, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "auditlog/audit_log_list.html",
        {
            "page_obj": page_obj,
            "action": action,
            "entity_type": entity_type,
            "action_choices": AuditLog.Action.choices,
        },
    )
