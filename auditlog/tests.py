from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import AuditLog, record

User = get_user_model()


class AuditLogTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="audit-staff", password="pass12345", is_staff=True)
        self.donor = User.objects.create_user(username="audit-donor", password="pass12345")

    def test_record_creates_entry_with_expected_fields(self):
        entry = record(
            AuditLog.Action.INVENTORY_INCREASED,
            entity_type="bloodinventory", entity_id=42, actor=self.staff,
            new_value="+5u O+", reason="test",
        )
        self.assertEqual(entry.entity_id, "42")
        self.assertEqual(entry.action, AuditLog.Action.INVENTORY_INCREASED)

    def test_staff_can_view_audit_log(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("auditlog:list"))
        self.assertEqual(response.status_code, 200)

    def test_donor_cannot_view_audit_log(self):
        self.client.force_login(self.donor)
        response = self.client.get(reverse("auditlog:list"))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_view_audit_log(self):
        response = self.client.get(reverse("auditlog:list"))
        self.assertEqual(response.status_code, 302)

    def test_filter_by_action(self):
        record(AuditLog.Action.USER_CREATED, entity_type="user", entity_id=1, actor=self.staff)
        record(AuditLog.Action.BLOOD_ISSUED, entity_type="bloodrequest", entity_id="abc", actor=self.staff)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("auditlog:list"), {"action": AuditLog.Action.USER_CREATED})
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
