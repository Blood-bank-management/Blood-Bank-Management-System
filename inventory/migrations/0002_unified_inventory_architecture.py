import django.db.models.deletion
import django.utils.timezone
import bloodbank.constants
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0001_initial"),
        ("donations", "0001_initial"),
        ("requests", "0002_bloodinventory_bloodissue"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="bloodinventory",
            name="blood_group",
            field=models.CharField(
                choices=[
                    ("A+", "A+"), ("A-", "A-"), ("B+", "B+"), ("B-", "B-"),
                    ("AB+", "AB+"), ("AB-", "AB-"), ("O+", "O+"), ("O-", "O-"),
                ],
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="bloodinventory",
            name="quantity",
            field=models.PositiveIntegerField(
                help_text="Units originally received into this batch. Does not change after creation.",
                validators=[bloodbank.constants.validate_positive_quantity],
            ),
        ),
        migrations.AddField(
            model_name="bloodinventory",
            name="quantity_remaining",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Live available balance for this batch. Changed only via inventory.services.",
            ),
        ),
        migrations.AddField(
            model_name="bloodinventory",
            name="notes",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="bloodinventory",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="bloodinventory",
            name="source_donation",
            field=models.OneToOneField(
                blank=True,
                help_text="The donation this batch was credited from, if any. "
                           "Null for batches created directly by staff (e.g. migrated "
                           "legacy stock) with no matching Donation record.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="inventory_batch",
                to="donations.donation",
            ),
        ),
        migrations.AlterModelOptions(
            name="bloodinventory",
            options={"ordering": ("expiry_date",), "verbose_name_plural": "blood inventory batches"},
        ),
        migrations.AddIndex(
            model_name="bloodinventory",
            index=models.Index(fields=["blood_group", "expiry_date"], name="inv_bg_expiry_idx"),
        ),
        migrations.CreateModel(
            name="InventoryTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "transaction_type",
                    models.CharField(
                        choices=[
                            ("receive", "Stock received"),
                            ("issue", "Stock issued"),
                            ("adjustment", "Manual adjustment"),
                        ],
                        max_length=12,
                    ),
                ),
                ("quantity_delta", models.IntegerField(help_text="Positive for receive/upward adjustment, negative for issue/downward adjustment.")),
                ("balance_after", models.PositiveIntegerField()),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transactions",
                        to="inventory.bloodinventory",
                    ),
                ),
                (
                    "related_issue",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name="inventory_transactions", to="requests.bloodissue",
                    ),
                ),
                (
                    "performed_by",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name="inventory_transactions", to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
