import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("donors", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EligibilityHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "previous_status",
                    models.CharField(
                        choices=[("eligible", "Eligible"), ("temporarily_ineligible", "Temporarily ineligible")],
                        max_length=24,
                    ),
                ),
                (
                    "new_status",
                    models.CharField(
                        choices=[("eligible", "Eligible"), ("temporarily_ineligible", "Temporarily ineligible")],
                        max_length=24,
                    ),
                ),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "changed_by",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+", to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "donor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="eligibility_history",
                        to="donors.donorprofile",
                    ),
                ),
            ],
            options={"ordering": ("-changed_at",), "verbose_name_plural": "eligibility history"},
        ),
    ]
