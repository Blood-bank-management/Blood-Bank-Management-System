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
3. On success you land on `/home/`, a short dashboard showing your
   username and role, with quick links relevant to that role.
4. **Log out** from the "Log out" control in the top navigation bar on
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

**Pending.** There is no Donation Management module in this repository
yet — you cannot record a donation or view a donation history anywhere
in the application.

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
2. Current status and (if ever changed) who changed it and when are
   shown.
3. Choose a new status ("Eligible" / "Temporarily ineligible"), add an
   optional reason, and submit.
4. The change is recorded with your account and a timestamp
   (`DonorProfile.eligibility_updated_by` / `_updated_at`). The donor
   cannot make this change themselves, from any page.

**Note:** this status is set manually by staff judgment — it is not
calculated automatically from a donation history, because no donation
data exists in this system yet.

### Viewing inventory

1. "Inventory" in the nav bar → `/inventory-summary/`: total non-expired
   units per blood group.
2. From there, "View expired units" → `/expired-units/`: every batch
   whose expiry date has passed.

### Reviewing blood requests

1. "Request queue" in the nav bar → `/requests/staff/requests/`.
2. Every submitted request is listed with its current status.
3. For a **pending** request: choose Approve or Reject (a reason is
   required when rejecting) and submit.
4. For an **approved** request: an "Issue blood" form appears. Submitting
   it deducts the requested quantity from inventory (refused if
   insufficient stock is on record), logs the issue, and marks the
   request **Fulfilled**. This step cannot be repeated for the same
   request — the inventory deduction and status change happen together
   as one atomic operation.

### Administrator account management

**Pending.** There is no in-application screen for creating, updating or
deactivating user accounts. Use Django's own tools instead:
`python manage.py createsuperuser`, or the Django admin site at
`/admin/` (reachable only by a superuser).

## Administrator workflow

An administrator is a staff account with `is_superuser=True`. Everything
in the Staff workflow above is available, plus:

- Access to `/admin/`, Django's built-in admin site, where `DonorProfile`,
  `BloodInventory` (both apps' versions — see
  [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md)), `BloodRequest` and `BloodIssue`
  records can all be viewed and edited directly.
- Creating other staff/admin accounts, via `createsuperuser` or the admin
  site's own User management screens — there is no dedicated
  "administrator" UI beyond Django's built-in one.
