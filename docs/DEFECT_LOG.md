# Defect log

Real defects found while building and testing this patch series, in the
order they were found. Nothing here is hypothetical -- each entry is a
defect this session's own test runs actually caught, with the retest
that confirms the fix. Per Part 5.G, no defect is listed as fixed without
having actually been re-tested after the fix.

---

## DEFECT-01: Administrative user-management URLs unreachable (404)

**Severity:** High -- the entire new admin user-management module
(Part 3.D) was completely unreachable; every view returned 404.

**Found during:** first full test run of `accounts/tests.py`
(`python manage.py test accounts`) -- 8 of 10 tests failed, several with
`AssertionError: 404 != 200`.

**Root cause:** `accounts/urls.py` originally mounted its views under
`admin/users/...`. `bloodbank/urls.py` already mounts Django's own admin
site at `path("admin/", admin.site.urls)`, and that entry comes first in
`urlpatterns`. Django's URL resolver matches `admin/` as a prefix and
hands everything under it to `admin.site.urls`, which has no
`users/` route of its own -- so every request to `/admin/users/...`
404'd inside the admin app's own URLconf before it ever reached
`accounts.views`.

**Reproduction:** `GET /admin/users/` while logged in as a superuser ->
HTTP 404 (confirmed via the Django test client, not just inspection).

**Fix:** moved the accounts app's URL prefix to `administration/users/...`
(`accounts/urls.py`), which does not collide with any existing mount
point, and documented the reason in a comment in that file so it isn't
reintroduced.

**Retest:** `python manage.py test accounts` -- 10/10 passed after the
fix (commit `8cca93d`, see `docs/COMMIT_PLAN.md`).

---

## DEFECT-02: Hand-written migrations drifted from model definitions

**Severity:** Low -- no runtime bug; `python manage.py makemigrations
--check --dry-run` (a required Part 11 verification step) reported
pending changes, which would have made that check fail if shipped as-is.

**Found during:** running `makemigrations --check --dry-run` as part of
Part 11 final verification, immediately after hand-writing the new
migrations for `inventory`, `donations` and `auditlog` (these were
written by hand rather than via `makemigrations` so a data migration
could be inserted at the correct point in `requests`' migration history;
see `docs/COMMIT_PLAN.md`).

**Root cause:** the hand-written migrations used slightly different
index names and, in one field, a different validator reference than
what `makemigrations`' autodetector would generate from the actual model
definitions (cosmetic drift, not a functional difference).

**Fix:** ran `makemigrations --noinput` to generate the small follow-up
migrations (`inventory/migrations/0003_...`, `donations/migrations/
0002_...`, `auditlog/migrations/0002_...`) that reconcile migration state
with the models exactly.

**Retest:** `python manage.py makemigrations --check --dry-run` ->
`No changes detected`, exit code 0.

---

## DEFECT-03: Last-active-superuser guard tests asserted on the wrong response

**Severity:** Low -- test-authoring defect, not an application defect.
The application behavior (blocking the action) was already correct; the
test was checking the wrong HTTP response for the confirmation message.

**Found during:** first run of `accounts/tests.py::
AdminUserManagementBehaviorTests::test_cannot_demote_the_last_active_superuser`
and `test_cannot_deactivate_the_last_active_superuser`.

**Root cause:** `accounts.views.user_detail` correctly blocks the action
and redirects (302) with a `django.contrib.messages` error; the message
text only appears in the *next* rendered page, not in the redirect
response body itself. The tests asserted `assertContains` directly on
the 302 response.

**Fix:** added `follow=True` to the test client calls so the message is
checked on the page the redirect leads to.

**Retest:** both tests pass; full suite re-run afterward (114/114,
see `docs/TEST_EXECUTION_REPORT.md`).

---

## DEFECT-04 (High) — `seed_demo_data` imported the removed aggregate inventory model

**Found during:** the final delivery/demo-readiness pass, while
verifying the demo seed command actually runs (it had not been
exercised since the inventory-unification fix was made earlier in this
series).

**Root cause:** `donors/management/commands/seed_demo_data.py` still
had `from requests.models import BloodInventory as
RequestsBloodInventory` and wrote stock through that model directly.
That model was removed by this same patch series (see §1 of
`docs/KNOWN_ISSUES.md`) when the two independent inventory models were
unified into one. Nothing in `python manage.py check`,
`makemigrations --check`, or the 114-test suite imports Django
management commands unless they're actually invoked, so this import
error was never triggered by any check this report had already run --
only by actually running `python manage.py seed_demo_data` itself,
which nothing in the automated test suite does.

**Impact (if shipped unfixed):** anyone following the README's own
"Getting started" steps and running `python manage.py seed_demo_data`
would have hit `ImportError: cannot import name 'BloodInventory' from
'requests.models'` and gotten no demo data, no working login
credentials, and no visible proof the application works at all --
despite every other check in this document reporting success. This is
exactly the kind of gap a report of "114/114 tests pass" can hide if
nothing specifically exercises the seed command.

**Fix:** rewrote the command to seed through the real service layer
instead of writing rows directly: `inventory.services.receive_batch`
for starting stock, `donations.services.record_donation` for two demo
donations (which also credits inventory and writes audit entries, the
same as the real "record donation" screen would), `inventory.services.
issue_units` plus a `BloodIssue` row for one fulfilled demo request,
and `DonorProfile.set_eligibility` for one eligibility-history entry.
This also means the seed data now exercises every module, not just
accounts and a flat inventory count.

**Retest:** ran `python manage.py seed_demo_data` twice against the
same fresh database. First run created 5 users, 7 inventory batches, 8
inventory transactions, 2 donations, 3 requests, 1 issue, and 8 audit
log entries. Second run produced zero new rows of any kind (confirmed
by re-counting every table) -- the command is genuinely idempotent,
not idempotent-looking. Full suite re-run afterward: 114/114, see
`docs/TEST_EXECUTION_REPORT.md` §7.

---

## No other defects found

Every other module (donations, the unified inventory architecture,
eligibility history, audit logging, the request-workflow changes, the
UI/theming pass) passed its own tests on first full run after being
written. That is reported here plainly rather than omitted, because a
defect log that only ever shows problems-then-fixes for some modules and
silence for others should say explicitly when the silence means "clean"
rather than "untested" -- see `docs/TEST_EXECUTION_REPORT.md` for the
actual commands and pass counts per module.
