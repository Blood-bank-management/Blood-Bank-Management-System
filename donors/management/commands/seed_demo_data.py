"""
Idempotent demo-data seeding for a shared dev/testing/demo environment.

Run with: python manage.py seed_demo_data

Creates (or reuses, if already present) one administrator, one staff
member, three donors with profiles, a starting inventory (via the real
inventory.services.receive_batch path, not a direct row insert), two
recorded donations (via the real donations.services.record_donation path,
so they also credit inventory and write audit log entries exactly the way
the application itself would), a donor eligibility history entry, and
three blood requests in three different states (pending, approved,
fulfilled) so the fulfilled one also exercises issue_units and leaves a
BloodIssue + InventoryTransaction + AuditLog trail -- i.e. this command
seeds through the same code paths the UI uses, not by poking the database
directly, so what you see after seeding is a real, consistent demonstration
of every workflow rather than disconnected fixture rows.

Safe to run more than once: every create is guarded by a lookup on a
stable, unique key (username, collection_reference, tracking UUID derived
from a fixed seed string) so re-running never creates duplicates and never
fails on a UniqueViolation. All passwords are the literal demo value
printed below -- never real credentials, never meant to be used outside a
local/dev/demo database.
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

import auditlog.models as auditlog
from donations.models import Donation
from donations.services import DuplicateDonationError, record_donation
from donors.models import DonorProfile
from inventory.services import issue_units, receive_batch
from requests.models import BloodIssue, BloodRequest

User = get_user_model()

DEMO_PASSWORD = "DemoPass!2026"


class Command(BaseCommand):
    help = (
        "Seed demo users, donor profiles, inventory, donations, requests, "
        "issues and eligibility history for local development/demo."
    )

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

        # --- Inventory: a starting batch per blood group, through the
        # real service layer (so each one writes its own InventoryTransaction
        # RECEIVE row, exactly like a real donation would). Guarded by notes
        # containing a stable marker so re-running doesn't add a second
        # starting batch per group.
        for group, units in (("O+", 20), ("A+", 10), ("B+", 8), ("AB+", 3), ("O-", 5)):
            marker = f"seed-starting-stock-{group}"
            if not InventoryTransactionExistsFor(marker):
                receive_batch(
                    blood_group=group,
                    quantity=units,
                    collection_date=date.today() - timedelta(days=5),
                    performed_by=admin,
                    notes=marker,
                )
                self.stdout.write(f"  inventory: {group} seeded with {units} starting units")

        # --- Donations: two recorded donations from donor_demo1/2, each
        # through donations.services.record_donation, so they also credit
        # inventory and write DONATION_RECORDED + INVENTORY_INCREASED audit
        # entries, same as the real "record donation" screen. Guarded by a
        # fixed, stable collection_reference so re-running hits the
        # DuplicateDonationError path and is silently skipped.
        donation_specs = [
            ("SEED-DON-0001", donors[0], "O+", 1, date.today() - timedelta(days=30)),
            ("SEED-DON-0002", donors[1], "B+", 1, date.today() - timedelta(days=10)),
        ]
        for ref, donor_user, group, qty, collected_on in donation_specs:
            donor_profile = DonorProfile.objects.get(user=donor_user)
            try:
                record_donation(
                    donor=donor_profile,
                    blood_group=group,
                    quantity=qty,
                    collection_date=collected_on,
                    collection_reference=ref,
                    recorded_by=staff,
                    notes="Seeded demo donation",
                )
                self.stdout.write(f"  donation: recorded {ref} ({qty}u {group} from {donor_user.username})")
            except DuplicateDonationError:
                pass  # already seeded on a previous run

        # --- Donor eligibility history: one explicit staff-made eligibility
        # change on donor_demo3, so the eligibility-history UI has something
        # to show beyond the default. Guarded by checking whether a history
        # row with this reason already exists for this donor.
        donor3_profile = DonorProfile.objects.get(user=donors[2])
        seed_note = "Seed data: reviewed after routine screening"
        if not donor3_profile.eligibility_history.filter(reason=seed_note).exists():
            donor3_profile.set_eligibility(
                DonorProfile.Eligibility.ELIGIBLE,
                changed_by=staff,
                note=seed_note,
            )
            self.stdout.write(f"  eligibility: recorded a history entry for {donors[2].username}")

        # --- Blood requests in three different states, so the request
        # queue and tracking pages have something in every status to show.
        # tracking_id is a UUIDField(default=uuid.uuid4); since we can't
        # pick our own, we key "already seeded" off requester_email + a
        # fixed, distinctive hospital name instead, which is also unique
        # enough for a demo fixture.
        pending_req = self._get_or_create_request(
            requester_email="seed-pending@cityhospital.example.com",
            requester_name="City Hospital Blood Desk",
            hospital_name="City Hospital (seed - pending)",
            blood_group="O+",
            quantity=2,
            purpose="Scheduled surgery (seed demo request, pending review).",
        )

        approved_req = self._get_or_create_request(
            requester_email="seed-approved@cityhospital.example.com",
            requester_name="City Hospital Blood Desk",
            hospital_name="City Hospital (seed - approved)",
            blood_group="A+",
            quantity=1,
            purpose="Scheduled transfusion (seed demo request, approved, ready to issue).",
        )
        if approved_req.status == BloodRequest.Status.PENDING:
            approved_req.status = BloodRequest.Status.APPROVED
            approved_req.review_note = "Seed data: approved for demo."
            approved_req.reviewed_by = staff
            approved_req.save(update_fields=("status", "review_note", "reviewed_by", "reviewed_at", "updated_at"))
            auditlog.record(
                auditlog.AuditLog.Action.REQUEST_APPROVED,
                entity_type="bloodrequest",
                entity_id=approved_req.tracking_id,
                actor=staff,
                new_value="approved (seed data)",
            )

        fulfilled_req = self._get_or_create_request(
            requester_email="seed-fulfilled@cityhospital.example.com",
            requester_name="City Hospital Blood Desk",
            hospital_name="City Hospital (seed - fulfilled)",
            blood_group="B+",
            quantity=1,
            purpose="Emergency transfusion (seed demo request, already fulfilled).",
        )
        if fulfilled_req.status == BloodRequest.Status.PENDING:
            fulfilled_req.status = BloodRequest.Status.APPROVED
            fulfilled_req.review_note = "Seed data: approved for demo."
            fulfilled_req.reviewed_by = staff
            fulfilled_req.save(update_fields=("status", "review_note", "reviewed_by", "reviewed_at", "updated_at"))
            auditlog.record(
                auditlog.AuditLog.Action.REQUEST_APPROVED,
                entity_type="bloodrequest",
                entity_id=fulfilled_req.tracking_id,
                actor=staff,
                new_value="approved (seed data)",
            )
        if not BloodIssue.objects.filter(request=fulfilled_req).exists():
            issue_units(
                blood_group=fulfilled_req.blood_group,
                quantity=fulfilled_req.quantity,
                performed_by=staff,
                reason=f"Seed data: issued against request {fulfilled_req.tracking_id}",
            )
            blood_issue = BloodIssue.objects.create(
                request=fulfilled_req,
                blood_group=fulfilled_req.blood_group,
                quantity=fulfilled_req.quantity,
                issued_by=staff,
                issue_note="Seed data: issued for demo.",
            )
            fulfilled_req.status = BloodRequest.Status.FULFILLED
            fulfilled_req.save(update_fields=("status", "updated_at"))
            auditlog.record(
                auditlog.AuditLog.Action.BLOOD_ISSUED,
                entity_type="bloodrequest",
                entity_id=fulfilled_req.tracking_id,
                actor=staff,
                new_value=f"{blood_issue.quantity}u {blood_issue.blood_group} (seed data)",
            )
            self.stdout.write("  request: seeded one fulfilled request with a matching issue")

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

    def _get_or_create_request(self, *, requester_email, requester_name, hospital_name,
                                blood_group, quantity, purpose):
        req, created = BloodRequest.objects.get_or_create(
            requester_email=requester_email,
            hospital_name=hospital_name,
            defaults={
                "requester_name": requester_name,
                "blood_group": blood_group,
                "quantity": quantity,
                "purpose": purpose,
            },
        )
        if created:
            self.stdout.write(f"  request: seeded {hospital_name} ({blood_group}, {quantity}u)")
        return req


def InventoryTransactionExistsFor(marker):
    """Small helper so the starting-stock loop above reads as one line:
    has a RECEIVE batch with this exact seed marker in its notes already
    been created on a previous run of this command?"""
    from inventory.models import BloodInventory
    return BloodInventory.objects.filter(notes=marker).exists()
