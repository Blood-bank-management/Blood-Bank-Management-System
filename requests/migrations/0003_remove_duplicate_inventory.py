from django.db import migrations


def migrate_aggregate_stock_into_batches(apps, schema_editor):
    """
    Part 2.A: before this migration, stock lived in two places --
    requests.BloodInventory (a per-blood-group aggregate counter) and
    inventory.BloodInventory (batch-level, with expiry). This migration
    converts any existing aggregate rows into a single batch per blood
    group in the now-sole inventory.BloodInventory table, so no existing
    deployment's stock count is silently lost when the aggregate table is
    dropped by the next operation in this migration.

    Rows with available_units == 0 are not migrated (there is nothing to
    represent), matching the original aggregate counter's visible effect.
    Each migrated batch is given a 42-day shelf life from today, since the
    aggregate model never tracked a collection date at all -- see
    docs/KNOWN_ISSUES.md for this being a documented limitation of the
    data being migrated, not something this migration invents new
    certainty about.
    """
    from datetime import timedelta

    from django.utils import timezone

    LegacyBloodInventory = apps.get_model("requests", "BloodInventory")
    NewBloodInventory = apps.get_model("inventory", "BloodInventory")

    today = timezone.localdate()
    shelf_life_days = 42  # bloodbank.constants.WHOLE_BLOOD_SHELF_LIFE_DAYS, inlined: migrations must not import app code that can change independently of this historical snapshot.

    for legacy_row in LegacyBloodInventory.objects.all():
        if legacy_row.available_units <= 0:
            continue
        NewBloodInventory.objects.create(
            blood_group=legacy_row.blood_group,
            quantity=legacy_row.available_units,
            quantity_remaining=legacy_row.available_units,
            collection_date=today,
            expiry_date=today + timedelta(days=shelf_life_days),
            notes="Migrated from legacy requests.BloodInventory aggregate count "
                  "(see docs/KNOWN_ISSUES.md #1).",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("requests", "0002_bloodinventory_bloodissue"),
        ("inventory", "0002_unified_inventory_architecture"),
    ]

    operations = [
        migrations.RunPython(
            migrate_aggregate_stock_into_batches,
            reverse_code=migrations.RunPython.noop,
            elidable=False,
        ),
        migrations.DeleteModel(
            name="BloodInventory",
        ),
    ]
