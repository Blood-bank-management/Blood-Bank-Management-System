# Demo Guide

A concrete script for demonstrating the full
**donor registration → eligibility → donation → inventory update →
blood request → approval → issue → inventory deduction → distribution
log** workflow end to end, using the demo accounts `seed_demo_data`
actually creates (see `README.md` "Getting started" for setup).

Every credential below is real — it is whatever
`python manage.py seed_demo_data` printed when you ran it. If you
re-seed, the same usernames/passwords come back (the command is
idempotent — see `KNOWN_LIMITATIONS.md`).

## 0. One-time setup (do this before the demo, not during it)

```powershell
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

Demo credentials (all passwords are literally `DemoPass!2026`):

| Role | Username |
|---|---|
| Administrator | `admin_demo` |
| Staff | `staff_demo` |
| Donor | `donor_demo1`, `donor_demo2`, `donor_demo3` |

After seeding, the database already contains a starting inventory, two
recorded donations, one eligibility-history entry, and three requests
(pending/approved/fulfilled) — so the queue and lists aren't empty on
first load. The script below adds **new** records on top of that so
you can show the create path too, not just existing data.

## 1. Donor registration

1. Log out if logged in. Go to `/donors/register/`.
2. Register a brand-new donor — e.g. username `demo_live_donor`, blood
   group `A+`, any valid date of birth/address.
3. You land on `/home/` immediately, logged in, with the donor
   dashboard: your blood group, eligibility ("Eligible" by default),
   donation count (0), and no "next eligible date" yet (no donations).

## 2. Eligibility (staff side)

1. Log out, log in as `staff_demo`.
2. Go to `/donors/staff/donors/`, search for `demo_live_donor`, open
   their record.
3. Scroll to "Eligibility" — change status, add a reason, submit.
4. Point out the **history list** below it: this change is appended,
   not overwritten (previous changes, if any, are still shown).

## 3. Donation (staff records it, inventory updates automatically)

1. Still as `staff_demo`, go to `/donations/record/`.
2. Donor username: `demo_live_donor`. Blood group: `A+`. Quantity: `1`.
   Collection date: today. Collection reference: anything unique, e.g.
   `DEMO-LIVE-0001`. Outcome: Recorded.
3. Submit. You're redirected to the donation list, and the new
   donation appears.
4. **Show the inventory updated automatically**: go to
   `/inventory/batches/` — a new `A+` batch exists, collected today,
   with `quantity_remaining` equal to what you just recorded. No
   separate "add inventory" step was needed.
5. **Show the duplicate-submission guard**: try recording a donation
   again with the *same* collection reference (`DEMO-LIVE-0001`). It is
   rejected with an error, and nothing is double-counted — open
   `/inventory/batches/` again and confirm there's still only one new
   batch, not two.

## 4. Donor views their own history

1. Log out, log in as `demo_live_donor` (or whatever you registered).
2. Go to `/donations/my-history/` (or "My donations" in the nav). The
   donation you just recorded is listed, with the next-eligible-date
   now showing (90 days from today, per this project's documented
   assumption — see `KNOWN_LIMITATIONS.md`).
3. **Show the IDOR protection**: this URL has no id/pk in it at all —
   there's nothing to tamper with to see another donor's history.

## 5. Blood request submission (no account needed)

1. Log out entirely (stay anonymous).
2. Go to `/requests/`. Fill in a hospital-desk style request: requester
   name/e-mail, hospital name, blood group `A+`, quantity `1`, purpose.
3. Submit — you land on a tracking page at a unique URL. **Copy that
   URL** (or just keep the tab open) — this is the only way to check
   back on this request later; bookmark it.

## 6. Staff review and approval

1. Log in as `staff_demo`. Go to `/requests/staff/requests/`.
2. Find the pending request you just submitted (use the search/filter
   controls to narrow by status=Pending or by the hospital name you
   used).
3. Choose **Approve**, submit.
4. Go back to the tracking tab from step 5 (still logged out, or in a
   different browser/incognito window) — refresh it. Status now shows
   **Approved**, with no staff login needed to see that.

## 7. Issue and distribution (inventory deducted atomically)

1. Back as `staff_demo` in the request queue, find the now-approved
   request. An "Issue blood" form appears.
2. Enter an issue note, submit.
3. Request status flips to **Fulfilled**.
4. **Show the inventory deduction**: go to `/inventory/batches/` again
   — the `A+` batch's `quantity_remaining` has dropped by the issued
   quantity. Open the batch detail page to see the matching
   `InventoryTransaction` ledger row (type `ISSUE`, negative delta).
5. **Show the duplicate-issue guard**: go back to the request queue
   and try to issue against the same (now-fulfilled) request again —
   it's rejected ("This request has already been issued against" /
   the request no longer shows an issue form at all).

## 8. Distribution / audit trail

1. Go to `/audit-log/` (staff/admin only). Filter by entity type or
   action if the list is long.
2. Point out the trail this one walkthrough just created, in order:
   `ELIGIBILITY_CHANGED` → `DONATION_RECORDED` → `INVENTORY_INCREASED`
   → `REQUEST_SUBMITTED` → `REQUEST_APPROVED` → `BLOOD_ISSUED`. Every
   entry shows who did it, when, and the before/after values.

## 9. Administrator account management (bonus, if time allows)

1. Log in as `admin_demo`. Go to `/administration/users/`.
2. Create a new staff account with the role dropdown set to "Staff" —
   point out there's no raw `is_staff` checkbox, only the role choice.
3. Open `staff_demo`'s own account detail page and try to deactivate
   it — if `admin_demo` is currently the *only* active administrator,
   try demoting `admin_demo` itself to staff instead, from a second
   browser tab logged in as `admin_demo`: this is rejected with an
   explicit error ("cannot remove the last active administrator"),
   not a silent failure.

## 10. Theming (quick, anywhere)

At any point in the above, click the light/dark/system switcher in the
nav. Confirm it applies instantly, persists if you reload the page or
navigate to another page, and there's no flash of the wrong theme on
load.

## If something doesn't match this script

Re-run `python manage.py seed_demo_data` — it's safe to run again, it
won't duplicate anything, and it will recreate the three accounts if
your database was reset. If a step genuinely doesn't work, check
`TEST_EXECUTION_REPORT.md` first — it documents every automated check
this project's own author actually ran, which may already explain the
discrepancy.
