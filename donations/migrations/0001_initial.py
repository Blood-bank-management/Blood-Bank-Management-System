import django.db.models.deletion
import bloodbank.constants
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("donors", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Donation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "blood_group",
                    models.CharField(
                        choices=[
                            ("A+", "A+"), ("A-", "A-"), ("B+", "B+"), ("B-", "B-"),
                            ("AB+", "AB+"), ("AB-", "AB-"), ("O+", "O+"), ("O-", "O-"),
                        ],
                        max_length=3,
                    ),
                ),
                ("quantity", models.PositiveIntegerField(validators=[bloodbank.constants.validate_positive_quantity])),
                ("collection_date", models.DateField()),
                ("collection_reference", models.CharField(max_length=64, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("recorded", "Recorded"), ("rejected", "Rejected (did not meet collection criteria)")],
                        default="recorded",
                        max_length=10,
                    ),
                ),
                ("rejection_reason", models.CharField(blank=True, max_length=255)),
                ("notes", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "donor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="donations",
                        to="donors.donorprofile",
                    ),
                ),
                (
                    "recorded_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="donations_recorded",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-collection_date", "-created_at"),
            },
        ),
        migrations.AddIndex(
            model_name="donation",
            index=models.Index(fields=["donor", "-collection_date"], name="donation_donor_date_idx"),
        ),
        migrations.AddIndex(
            model_name="donation",
            index=models.Index(fields=["blood_group"], name="donation_bg_idx"),
        ),
        migrations.AddIndex(
            model_name="donation",
            index=models.Index(fields=["status"], name="donation_status_idx"),
        ),
    ]
