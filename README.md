# Blood Bank Management System

Django project for the BBMS mini-project (Team 1). This README covers the
shared dev/testing environment set up in Sprint 2: install, migrate, seed
data, run tests, and the role-permission matrix enforced by the code.

## 1. Setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in a real `DJANGO_SECRET_KEY` before
running anything beyond your own machine (see `.env.example` for how to
generate one and how to export it, since this project does not depend on a
.env-loading library). For solo local development the settings module falls
back to the original Sprint 1 dev key, so you can skip this step just to get
started.

```bash
python manage.py migrate
python manage.py seed_demo_data   # optional: demo users + sample data, see below
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`.

## 2. Demo credentials (seed_demo_data)

`python manage.py seed_demo_data` is idempotent — safe to run again, it will
not duplicate data. It creates:

| Role          | Username      | Password        |
|---------------|---------------|------------------|
| Administrator | `admin_demo`  | `DemoPass!2026`  |
| Blood bank staff | `staff_demo` | `DemoPass!2026` |
| Donor         | `donor_demo1`, `donor_demo2`, `donor_demo3` | `DemoPass!2026` |

These are fake, local-only credentials for a development database. Never
reuse this password anywhere real, and never point `seed_demo_data` at a
shared/production database.

## 3. Running tests

```bash
python manage.py test                        # default discovery (test*.py)
python manage.py test inventory.performance_test -v 2   # perf smoke test, run separately: see note below
```

Current status (Sprint 2, this commit): **71/71** tests pass under default
discovery, plus the separately-run performance smoke test.

**Note:** `inventory/performance_test.py` is not named `test_*.py`, so
Django's default test runner does not discover it automatically — this was
true in Sprint 1 too, and is why a real bug in it (`reverse("login")`,
fixed in Sprint 2) went unnoticed. It is not renamed in this change set to
avoid touching a file outside Donor Management's scope without the
teammate who owns it; run it explicitly as shown above, or rename it to
`test_performance.py` if the team agrees.

## 4. Role-permission matrix

Roles are derived directly from Django's built-in `User` flags — there is
no separate "role" field to drift out of sync:

| Role | Definition |
|---|---|
| Anonymous | Not logged in. |
| Donor | Logged in, `is_staff=False`, `is_superuser=False`. Granted automatically and only by `donors:register` self-registration. |
| Blood Bank Staff | `is_staff=True`. |
| Administrator | `is_superuser=True` (also satisfies every Staff check). |

| Action | Anonymous | Donor | Staff | Admin |
|---|---|---|---|---|
| View login page | Yes | Yes (redirected if already in) | Yes | Yes |
| Register as donor | Yes | — (redirected home) | — | — |
| Search blood availability | No (login required) | Yes | Yes | Yes |
| Submit a blood request | Yes | Yes | Yes | Yes |
| Track a blood request by tracking ID | Yes | Yes | Yes | Yes |
| View/update own donor profile | No | Yes (own only — no id parameter exists) | n/a (no profile unless also registered as donor) | n/a |
| View donor list | No | **No (403)** | Yes | Yes |
| View a donor's detail record | No | **No (403), even their own** | Yes | Yes |
| Change a donor's eligibility status | No | **No (403)** | Yes | Yes |
| View blood request queue, approve/reject | No | **No (403)** | Yes | Yes |
| Issue blood against an approved request | No | **No (403)** | Yes | Yes |
| View inventory summary / expired units | No | **No (403)** | Yes | Yes |
| Django admin site | No | No | No (unless superuser) | Yes |

Enforcement point: `authentication/decorators.py:staff_required`, used by
every staff-only view in `inventory`, `requests`-adjacent staff flows, and
`donors`. It is **not** implemented by hiding nav links — the nav bar hides
links a role can't use for clarity, but every view re-checks the role on
every request regardless of how the URL was reached. See
`donors/tests.py` (`StaffDonorManagementTests`) for RBAC/IDOR tests that
hit the URLs directly, not just the rendered pages.

## 5. Known limitations (read before assuming something is "done")

- **Two independent inventory models.** `inventory.BloodInventory`
  (per-batch: blood group + quantity + collection/expiry date) and
  `requests.BloodInventory` (per-blood-group aggregate: available_units)
  are separate tables built by different Sprint 1 modules. `availability_search`
  reads the first; `issue_blood`'s atomic deduction writes the second. They
  are not kept in sync with each other. This is a real cross-module
  integration gap, flagged here rather than silently patched, because a
  fix touches the Blood Donation Management and Blood Issue/Distribution
  modules owned by other teammates. Recommended Sprint 3 fix: pick one
  model (`requests.BloodInventory`'s aggregate shape fits the issue/request
  workflow already built on it) and migrate `inventory` app's views to read
  from it, retiring the per-batch model or demoting it to a donation-batch
  ledger that rolls up into the aggregate.
- **Donor eligibility is staff-set, not auto-computed.** BBMS-F-006's
  acceptance criterion ties eligibility to donation history
  (BBMS-F-007/008/009), but the Blood Donation Management module does not
  exist in this repository yet. `DonorProfile.eligibility_status` is a
  manual staff decision with an audit trail (who/when/why), not an
  automatic 90-day-deferral calculation. Revisit once donation recording
  lands.
- **Donation Management (BBMS-F-007/008/009) and Administrative user
  management (BBMS-F-020/021) are not implemented** in this repository —
  out of Donor Management's Sprint 2 scope; see the Sprint 2 completion
  report for the full requirement-by-requirement status.
- **HTTPS (BBMS-SR-003)** is a deployment-environment concern, not
  something `DEBUG=True`'s local dev server enforces; not addressed here.
- Passing the local test suite is not a production-readiness claim — see
  the Sprint 2 security and test reports for what was and wasn't verified.
