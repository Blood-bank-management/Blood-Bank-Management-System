"""Audit log is read-only in the Django admin, even for a superuser (gap 4.5)."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import AuditLog, record

User = get_user_model()


class AuditLogAdminReadOnlyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser("audit_root", "audit@example.com", "S3cure-Pass!word-42")
        cls.entry = record(AuditLog.Action.INVENTORY_ADJUSTED, entity_type="batch", entity_id=1, reason="test")

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_superuser_can_view_audit_log_list(self):
        response = self.client.get(reverse("admin:auditlog_auditlog_changelist"))
        self.assertEqual(response.status_code, 200)

    def test_superuser_cannot_add_entry(self):
        response = self.client.get(reverse("admin:auditlog_auditlog_add"))
        self.assertEqual(response.status_code, 403)

    def test_superuser_cannot_edit_entry(self):
        url = reverse("admin:auditlog_auditlog_change", args=[self.entry.pk])
        response = self.client.post(url, {"reason": "tampered"})
        self.assertEqual(response.status_code, 403)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.reason, "test")

    def test_superuser_cannot_delete_entry(self):
        url = reverse("admin:auditlog_auditlog_delete", args=[self.entry.pk])
        response = self.client.post(url, {"post": "yes"})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(AuditLog.objects.filter(pk=self.entry.pk).exists())
