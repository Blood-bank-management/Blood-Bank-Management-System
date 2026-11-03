# User Guide

This guide covers what actually works in the current codebase, organized
by role. Anything not yet built is marked **Pending** rather than
described as if it existed — see
[`REQUIREMENTS_TRACEABILITY.md`](REQUIREMENTS_TRACEABILITY.md) for the
complete requirement-by-requirement status.

## Logging in and out

1. Go to `/login/`.
2. Enter your **username or e-mail address** and your password (the login
   form accepts either — `authentication/forms.py`).
3. On success you land on `/home/`, a dashboard that differs by role:
   staff/admin see available units by blood group, pending/approved
   request counts, recent donations and issues, batches expiring within
   7 days, and recent audit activity; donors see their own blood group,
   eligibility status, donation count, and the next date they'd be
   eligible to donate again. Every figure comes from a live database
   query — none of it is hardcoded.
4. A light/dark/system theme switcher is available in the nav on every
   page; your choice is remembered in your browser (no account needed)
   and there's no flash of the wrong theme on page load.
5. **Log out** from the "Log out" control in the top navigation bar on
   any page — it is a POST request with a CSRF token (`authentication/
   urls.py`, `auth_views.LogoutView`), not a plain link, so it can't be
   triggered by just visiting a URL.

If you try to open any page that requires login while logged out, you
are redirected to `/login/?next=<the page you wanted>` and sent there
automatically after a successful login.

## Donor workflow

### Registering as a donor

1. From the login page, or directly at `/donors/register/`.
2. Fill in: first name, last name, username, e-mail, phone number, date
   of birth, blood group, address, and a password (entered twice).
3. The form validates: no duplicate username or e-mail, date of birth
   must be in the past, the two password fields must match, and the
   password itself must pass Django's standard password checks (not too
   short, not too similar to your username, not a commonly used
   password, not entirely numeric).
4. On success you are logged in immediately and taken to `/home/`. Your
   account is created with donor-level access only — registration never
   grants staff or administrator rights (`donors/forms.py:
   DonorRegistrationForm.save`).

### Managing your profile

1. Go to `/donors/profile/` (or "My profile" in the nav bar).
2. You will see your current eligibility status (set by staff — see
   below) and a form to update your first name, last name, e-mail,
   phone number, date of birth, blood group and address.
3. Submit to save. You cannot change your own eligibility status from
   this page — there is no field for it.

### Checking blood availability

1. Go to `/availability/` (or "Availability" in the nav bar). Requires
   being logged in.
2. Choose a blood group and submit. You'll see the total non-expired
   units currently on record for that group, or a message if none are
   available.

### Submitting and tracking a blood request

1. Go to `/requests/` (or "Request blood" in the nav bar). **No login is
   required** — this form is open to anyone (a hospital desk submitting
   on a patient's behalf may not have an account).
2. Fill in requester name, e-mail, hospital/facility name, blood group,
   quantity, and purpose. Submit.
3. You're redirected to a tracking page at a unique URL (your
   `tracking_id`) showing status (**Pending review** initially), and the
   request details. Bookmark or save that link — it's how you check back
   on status later; there is no donor-account-linked list of "my
   requests" (see [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) for why that link
   alone grants access to the tracking page).

### Donation history

1. Go to `/donations/my-history/` (or "My donations" in the nav bar).
2. You'll see every donation recorded against your profile — date,
   blood group, quantity, and status (recorded or rejected, with a
   reason if rejected) — and your next eligible-to-donate date, based
   on this project's documented 90-day assumption since your most
   recent recorded donation (`bloodbank.constants
   .MIN_DAYS_BETWEEN_DONATIONS` — not a medical claim, just the
   interval this project uses; see
   [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) for how it's documented).
3. This page takes no donor ID from the URL — it always shows your own
   history, so there is nothing to tamper with to see someone else's.
4. Your eligibility status itself (Eligible / Temporarily ineligible)
   is still set by staff judgment, not auto-derived from this history —
   see "Managing donor eligibility" below and
   [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) §8.1.

## Staff workflow

Everything below requires a staff account (`is_staff=True` — either
created via `createsuperuser`, the Django admin, or the `seed_demo_data`
demo accounts). A donor account that tries to reach any of these pages
gets an HTTP 403, not a login prompt.

### Viewing the donor directory

1. Go to `/donors/staff/donors/` (or "Donors" in the nav bar).
2. The list shows every registered donor: username, name, blood group,
   and current eligibility status.
3. Use the search box to filter by username, name, e-mail or blood
   group.
4. Click "View" on any row to open that donor's full record.

### Managing donor eligibility

1. From a donor's detail page (`/donors/staff/donors/<id>/`), scroll to
   the "Eligibility" section.
2. Current status, who changed it and when, and the **full history**
   of past changes (not just the most recent one) are shown.
3. Choose a new status ("Eligible" / "Temporarily ineligible"), add an
   optional reason, and submit.
4. The change is recorded with your account and a timestamp, a new
   history row is added (the previous status is never overwritten),
   and an audit log entry is written — all as one atomic operation.
   The donor cannot make this change themselves, from any page.

**Note:** this status is still set manually by staff judgment, not
auto-calculated from donation history. The donor's "next eligible
date" (see "Donation history" above) is shown to the donor and to
staff as a reference point, but nothing currently flips the
eligibility status automatically when that date arrives — see
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) §8.1.

### Recording a donation

1. Go to `/donations/record/` (or "Record donation" in the nav bar).
2. Enter the donor's username, blood group, quantity, collection date
   (cannot be in the future), and a **collection reference** — a
   unique identifier for this physical donation (e.g. a lab/paper form
   number). Choose an outcome: Recorded, or Rejected (with a required
   reason — e.g. a failed screening).
3. Submit. If you accidentally resubmit the same collection reference
   (e.g. a double-click, or a duplicate paper form), the system
   rejects it and nothing is double-counted — you'll see an error
   instead of a second donation silently being created.
4. If the outcome is Recorded, inventory for that blood group is
   credited automatically in the same step — there is no separate
   "now update inventory" action to forget.

### Viewing the donation list

1. Go to `/donations/` (or "Donations" in the nav bar).
2. Every recorded donation is listed, with search/filter by donor,
   blood group, and status, and pagination for large lists.
3. From a donor's own detail page, staff can also open that specific
   donor's donation history directly.

### Viewing inventory

1. "Inventory" in the nav bar → `/inventory/batches/`: every batch
   (blood group, original quantity, remaining quantity, collection and
   expiry dates), searchable and paginated. Open a batch to see its
   full transaction history (every receive/issue/adjustment against
   it) and to make a manual adjustment — a reason is required for
   every adjustment, and the balance can never go negative.
4. `/inventory-summary/`: a higher-level view — batch counts per blood
   group, how many are expiring within 7 days, and the most recent
   inventory transactions across the whole system.
5. From there, "View expired units" → `/expired-units/`: every batch
   whose expiry date has passed (automatically excluded from
   availability search and from being issued against).

### Reviewing blood requests

1. "Request queue" in the nav bar → `/requests/staff/requests/`.
2. Every submitted request is listed with its current status; use the
   search/filter controls to narrow by status, blood group, or
   hospital name, with pagination for large queues.
3. For a **pending** request: choose Approve or Reject (a reason is
   required when rejecting) and submit.
4. For an **approved** request: an "Issue blood" form appears. Submitting
   it deducts the requested quantity from inventory, taken from the
   batches closest to expiry first (refused if insufficient stock is on
   record), logs the issue, and marks the request **Fulfilled**. This
   step cannot be repeated for the same request — a second attempt is
   explicitly rejected, and the inventory deduction and status change
   happen together as one atomic operation.

### Viewing the audit log

1. Go to `/audit-log/` (or "Audit log" in the nav bar).
2. Every tracked action across the system — donations, inventory
   changes, request status changes, blood issued, eligibility changes,
   and account/role changes — is listed with who did it, when, and the
   before/after values, filterable by action type or entity, with
   pagination. Entries cannot be edited or deleted from this screen or
   from the Django admin site (registered read-only).

### Administrator account management

1. Go to `/administration/users/` (or "Users" in the nav bar — visible
   only to administrators). This is an in-application screen; it is no
   longer necessary to use `createsuperuser` or the Django admin site
   for day-to-day account management (though both still work).
2. Search/filter the account list by username, name, or role, with
   pagination.
3. "Create account" lets you set a username, password, and a **role**
   (Donor / Staff / Administrator) from a fixed dropdown — there is no
   way to set `is_staff`/`is_superuser` directly, by design.
4. From an account's detail page you can update its name/e-mail, change
   its role, or activate/deactivate it. Two safeguards apply
   automatically: you cannot demote or deactivate the **last** active
   administrator account (the system always keeps at least one), and a
   non-administrator account can never be granted admin rights through
   this screen or by tampering with the form submission — the role is
   always read from the validated dropdown value, never from a raw
   field name.
5. Every create, role change, and activate/deactivate action is written
   to the audit log automatically.

## Administrator workflow

An administrator is a staff account with `is_superuser=True`. Everything
in the Staff workflow above is available, plus:

- The in-application account management screen described above
  (`/administration/users/`) — the primary way to manage accounts now.
- Access to `/admin/`, Django's built-in admin site, where `DonorProfile`,
  `BloodInventory`, `Donation`, `BloodRequest`, `BloodIssue` and
  `AuditLog` (read-only) records can all be viewed, and most of them
  edited, directly.
