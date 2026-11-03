from django.urls import path

from . import views

app_name = "auditlog"

urlpatterns = [
    path("staff/audit-log/", views.audit_log_list, name="list"),
]
