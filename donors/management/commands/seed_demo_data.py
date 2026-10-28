"""
Idempotent demo-data seeding for a shared dev/testing environment.

Run with: python manage.py seed_demo_data

Creates (or reuses, if already present) one administrator, one staff
member, three donors with profiles, a small starting inventory and one
sample blood request, so a teammate who just cloned the repo has something
to click through immediately after migrating. All passwords are the
literal demo values printed below -- never real credentials, and never
meant to be used outside a local/dev database.
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from donors.models import DonorProfile
from requests.models import BloodInventory as RequestsBloodInventory
from requests.models import BloodRequest

User = get_user_model()

DEMO_PASSWORD = "DemoPass!2026"


class Command(BaseCommand):
    help = "Seed demo users, donor profiles, inventory and a sample request for local development."

    @transaction.atomic
    def handle(self, *args, **options):
        admin = self._get_or_create_user(
            "admin_demo", "admin@example.com", is_staff=True, is_superuser=True,
        )
        staff = self._get_or_create_user(
            "staff_demo", "staff@example.com", is_staff=True,
        )
        donors = [
            self._get_or_create_donor("donor_demo1", "Asha", "Patel", "O+"),
            self._get_or_create_donor("donor_demo2", "Ravi", "Kumar", "B+"),
            self._get_or_create_donor("donor_demo3", "Meera", "Shah", "A-"),
        ]

        for group, units in (("O+", 20), ("A+", 10), ("B+", 8), ("AB+", 3), ("O-", 5)):
            inv, created = RequestsBloodInventory.objects.get_or_create(
                blood_group=group, defaults={"available_units": units},
            )
            if created:
                self.stdout.write(f"  inventory: {group} seeded with {units} units")

        BloodRequest.objects.get_or_create(
            requester_name="City Hospital Blood Desk",
            requester_email="desk@cityhospital.example.com",
            hospital_name="City Hospital",
            blood_group="O+",
            quantity=2,
            defaults={"purpose": "Scheduled surgery (demo request)."},
        )

        self.stdout.write(self.style.SUCCESS("\nDemo data ready. Log in with:"))
        self.stdout.write(f"  Administrator : admin_demo / {DEMO_PASSWORD}")
        self.stdout.write(f"  Staff         : staff_demo / {DEMO_PASSWORD}")
        for donor in donors:
            self.stdout.write(f"  Donor         : {donor.username} / {DEMO_PASSWORD}")

    def _get_or_create_user(self, username, email, **flags):
        user, created = User.objects.get_or_create(
            username=username, defaults={"email": email, **flags},
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(f"  user: created {username}")
        return user

    def _get_or_create_donor(self, username, first_name, last_name, blood_group):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": f"{username}@example.com",
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(f"  user: created {username}")

        DonorProfile.objects.get_or_create(
            user=user,
            defaults={
                "phone_number": "9000000000",
                "date_of_birth": date.today() - timedelta(days=365 * 28),
                "blood_group": blood_group,
                "address": "123 Demo Street",
            },
        )
        return user
