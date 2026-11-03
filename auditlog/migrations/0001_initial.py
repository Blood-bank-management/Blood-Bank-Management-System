import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("donation_recorded", "Donation recorded"),
                            ("donation_modified", "Donation modified"),
                            ("donation_cancelled", "Donation cancelled"),
                            ("inventory_increased", "Inventory increased"),
                            ("inventory_decreased", "Inventory decreased"),
                            ("inventory_adjusted", "Inventory adjusted"),
                            ("request_submitted", "Request submitted"),
                            ("request_approved", "Request approved"),
                            ("request_rejected", "Request rejected"),
                            ("request_status_changed", "Request status changed"),
                            ("blood_issued", "Blood issued"),
                            ("eligibility_changed", "Donor eligibility changed"),
                            ("user_created", "User created"),
                            ("user_role_changed", "User role changed"),
                            ("user_activation_changed", "User activated/deactivated"),
                        ],
                        max_length=32,
                    ),
                ),
                ("entity_type", models.CharField(max_length=64)),
                ("entity_id", models.CharField(max_length=64)),
                ("previous_value", models.TextField(blank=True)),
                ("new_value", models.TextField(blank=True)),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_entries",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["entity_type", "entity_id"], name="auditlog_entity_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["action"], name="auditlog_action_idx"),
        ),
    ]
