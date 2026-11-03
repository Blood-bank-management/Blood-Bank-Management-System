# Blood Bank Management System

A Django web application for managing blood donors, blood inventory, and
blood requests — a college mini-project (Team 1) built by four students
over two sprints. This README is the entry point; deeper documentation
lives in [`docs/`](docs/) (linked throughout).

## Table of contents

- [Problem statement](#problem-statement)
- [Objectives](#objectives)
- [Main features](#main-features)
- [Technology stack](#technology-stack)
- [Architecture](#architecture)
- [Application modules](#application-modules)
- [Getting started](#getting-started)
- [Demo accounts](#demo-accounts)
- [Running tests](#running-tests)
- [Project directory structure](#project-directory-structure)
- [User roles and permissions](#user-roles-and-permissions)
- [Functionality status](#functionality-status)
- [Known limitations](#known-limitations)
- [Future enhancements](#future-enhancements)
- [Team](#team)
- [Contributing](#contributing)
- [Documentation index](#documentation-index)

## Problem statement

Blood banks have traditionally tracked donors, donations, inventory and
requests on paper or in disconnected spreadsheets, making it slow and
error-prone to answer a simple question like "do we have enough O- for
this request right now?" (from the project's own SRS, §1.1 Purpose:
*"The purpose of this system is to support blood banks in collecting data
about donors, donations, blood types, blood supplies levels, and blood
orders using one application."*)

## Objectives

Per the project's SRS (§1.2 Scope), the system's objectives are to
provide, in one application: donor registration and management, donation
recording, blood type/group management, blood inventory management,
blood availability search, blood request submission, and blood issuing
and distribution. The SRS explicitly scopes out hospital patient
management, health diagnosis, and courier/logistics tracking — this is a
blood bank's internal system, not a hospital information system.

## Main features

Features marked **(implemented)** exist and are tested in this
repository today; see [Functionality status](#functionality-status) for
the complete, current picture.

- User authentication: login with username **or** email, logout, session
  protection on every non-public page **(implemented)**
- Donor self-registration with minimum-privilege account creation
  **(implemented)**
- Donor self-service profile (view/update own contact details)
  **(implemented)**
- Staff donor directory with search, and per-donor eligibility management
  with an audit trail **(implemented)**
- Blood inventory summary and expired-unit tracking, staff-only
  **(implemented)**
- Public blood availability search by blood group **(implemented)**
- Blood request submission and tracking-by-ID, for requesters with or
  without an account **(implemented)**
- Staff review queue: approve/reject pending requests **(implemented)**
- Blood issue/distribution against an approved request, with an atomic
  inventory deduction and an audit log entry **(implemented)**
- Donation recording with duplicate-submission protection and an
  automatic, atomic inventory credit **(implemented)**
- Donor's own donation history (no URL id parameter — IDOR-safe by
  construction) and a staff-facing donation list with search/filter
  **(implemented)**
- Donor eligibility change history, with an audit trail **(implemented)**
- Administrator user management: create accounts, change roles,
  activate/deactivate, all from the app, with safeguards against
  self-escalation and against ever leaving zero active administrators
  **(implemented)**
- A single, append-only audit log covering 14 action types across
  donations, inventory, requests, eligibility and account management
  **(implemented)**
- Light/dark/system theme switcher, persisted per browser, with no
  flash of the wrong theme on load **(implemented)**
- Role-aware staff/admin dashboard (available units, blood-group
  distribution, pending requests, expiring stock, recent activity) and
  donor dashboard (own eligibility, donation history, next-eligible
  date), both built from live database queries, no mock data
  **(implemented)**

## Technology stack

| Layer | Technology |
|---|---|
| Backend framework | Django 6.1.1 (Python) |
| Database | SQLite (`db.sqlite3`, Django's default dev database) |
| Authentication | Django's built-in session authentication (`django.contrib.auth`) |
| Templates | Django Template Language, one shared base template (`templates/base.html`) |
| Dev/test tooling | Django's built-in test runner (`manage.py test`) |

This is the actual stack in `requirements.txt` and `bloodbank/settings.py`
— four dependencies (`asgiref`, `Django`, `sqlparse`, `tzdata`), no REST
framework, no frontend build tooling, no JavaScript framework, despite the
SRS header listing "Python (Django) / JavaScript (Node.js)" as the
intended technology. No Node.js code exists in this repository.

## Architecture

Four Django apps, each owning one area of the domain, sharing one
database and one template design system. See
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full breakdown
(models, views, URL routing, the authentication/authorization flow, and
Mermaid diagrams of the app and request/response structure).

## Application modules

| App | Responsibility | Key models |
|---|---|---|
| `authentication` | Login, logout, the role-aware dashboard | — (uses Django's built-in `User`) |
| `donors` | Donor self-registration, self-service profile, staff donor directory, eligibility management + history | `DonorProfile`, `EligibilityHistory` |
| `donations` | Recording a donation (staff), duplicate-submission protection, donor/staff donation history | `Donation` |
| `inventory` | The single inventory source of truth: batch-level stock, availability search, staff batch dashboard, transaction ledger | `BloodInventory` (per-batch), `InventoryTransaction` |
| `requests` | Blood request submission/tracking, staff review, blood issue and distribution | `BloodRequest`, `BloodIssue` |
| `auditlog` | The append-only audit trail every other app writes to | `AuditLog` |
| `accounts` | Administrator-only user management (create/role/activate), built on Django's own `User` model | — (no new models; operates on `User`) |

`inventory` is now the **only** app that stores blood stock.
`requests` previously defined its own, separate aggregate
`BloodInventory` model that could drift out of sync with `inventory`'s;
that model has been removed, with a data migration
(`requests/migrations/0003_remove_duplicate_inventory.py`) that
converts any pre-existing aggregate rows into `inventory` batches
first. See [`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md) §1 for the
full history of that fix.

## Getting started

### Prerequisites

- Python 3.10+ (tested in this environment with Python 3.13)
- `pip`
- Git

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/Blood-bank-management/blood-bank-management-system.git
cd blood-bank-management-system
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables (optional for local dev)

Copy `.env.example` to `.env` and fill in a real `DJANGO_SECRET_KEY`
before running this anywhere beyond your own machine. This project does
not use a `.env`-loading library, so export the variables as real
environment variables before running `manage.py`:

**macOS / Linux (bash/zsh):**
```bash
export $(grep -v '^#' .env | xargs)
```

**Windows (PowerShell):**
```powershell
Get-Content .env | Where-Object { $_ -notmatch '^#' -and $_.Trim() } | ForEach-Object {
    $name, $value = $_ -split '=', 2
    [System.Environment]::SetEnvironmentVariable($name, $value)
}
```

For solo local development you can skip this step entirely — the
settings module falls back to the original development `SECRET_KEY` and
`DEBUG=True`.

### 4. Apply database migrations

```bash
python manage.py migrate
```

This creates `db.sqlite3` in the project root (already in `.gitignore` —
never commit it).

### 5. Load demo data (optional)

```bash
python manage.py seed_demo_data
```

Idempotent — safe to run more than once. See
[Demo accounts](#demo-accounts) for what it creates.

### 6. Create an administrator account (if you skipped step 5)

```bash
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

### 8. Open the application

```
http://127.0.0.1:8000/
```

## Demo accounts

`python manage.py seed_demo_data` (defined in
`donors/management/commands/seed_demo_data.py`) creates exactly these
accounts — nothing else is pre-configured anywhere in the codebase:

| Role | Username | Password |
|---|---|---|
| Administrator | `admin_demo` | `DemoPass!2026` |
| Blood bank staff | `staff_demo` | `DemoPass!2026` |
| Donor | `donor_demo1`, `donor_demo2`, `donor_demo3` | `DemoPass!2026` |

It also seeds, through the application's own service layer (not raw
database rows): starting inventory across five blood groups, two
recorded donations (which themselves credit inventory, same as the
real "record donation" screen), one donor eligibility-history entry,
and three blood requests in three different states (pending, approved,
and fulfilled — the fulfilled one with a matching issue and inventory
deduction already applied). This gives every list/dashboard something
real to show immediately after a fresh clone, and it's the dataset
[`DEMO_GUIDE.md`](DEMO_GUIDE.md)'s walkthrough is written against.

The command is idempotent — running it again creates nothing new; see
`docs/TEST_EXECUTION_REPORT.md` §7 for the verification. These are
fake, local-only development credentials — never reuse this password
anywhere real, and never run this command against a shared or
production database.

## Running tests

```bash
python manage.py test
```

Executed in this environment on the current `main` branch: **114/114
tests pass.** Django's default test discovery only picks up files
matching `test*.py`, which `inventory/performance_test.py` does not — run
it explicitly:

```bash
python manage.py test inventory.performance_test -v 2
```

That file now benchmarks all 8 pages named in the project's
performance task (login, donor list, donation list, availability
search, inventory dashboard, request queue, request tracking,
administrator user list) — each p90 under the 3-second target against
Django's test client (see
[`docs/TEST_EXECUTION_REPORT.md`](docs/TEST_EXECUTION_REPORT.md) for
the caveat on test-client timings vs. real production latency).

Full breakdown of what each test module covers is in
[`docs/TESTING.md`](docs/TESTING.md).

```bash
python manage.py check                        # Django system checks
python manage.py makemigrations --check --dry-run   # no un-made migrations
```

Both pass cleanly on the current `main` branch.

## Project directory structure

```
blood-bank-management-system/
├── authentication/              # Login, logout, role-aware dashboard
│   ├── templates/authentication/
│   ├── tests/
│   ├── decorators.py            # staff_required, admin_required (shared RBAC decorators)
│   ├── forms.py                 # username-or-email login form
│   ├── urls.py
│   └── views.py                 # _staff_dashboard_context / _donor_dashboard_context
├── donors/                      # Donor self-registration, profile, staff management
│   ├── management/commands/seed_demo_data.py
│   ├── migrations/
│   ├── templates/donors/
│   ├── admin.py
│   ├── decorators.py            # re-exports authentication.decorators.staff_required
│   ├── forms.py
│   ├── models.py                # DonorProfile, EligibilityHistory
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── donations/                   # Record a donation; donor/staff donation history
│   ├── migrations/
│   ├── templates/donations/
│   ├── admin.py
│   ├── forms.py                 # DonationRecordForm
│   ├── models.py                # Donation, next_eligible_date()
│   ├── services.py               # record_donation() — the one atomic entry point
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── inventory/                   # The single inventory source of truth
│   ├── migrations/
│   ├── templates/inventory/
│   ├── forms.py                 # InventoryAdjustmentForm
│   ├── models.py                # BloodInventory (per-batch), InventoryTransaction
│   ├── services.py               # receive_batch() / issue_units() / adjust_batch()
│   ├── performance_test.py      # BBMS-53 perf test, 8 pages (run separately)
│   ├── tests.py / tests_services.py / tests_access.py
│   ├── urls.py
│   └── views.py
├── requests/                    # Blood requests, staff review, issue/distribution
│   ├── migrations/
│   ├── templates/requests/
│   ├── models.py                # BloodRequest, BloodIssue
│   ├── tests.py
│   ├── urls.py
│   └── views.py                 # issue_blood() now calls inventory.services.issue_units()
├── auditlog/                    # Append-only audit trail
│   ├── migrations/
│   ├── templates/auditlog/
│   ├── admin.py                  # registered read-only (no add/change/delete)
│   ├── models.py                 # AuditLog, record()
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── accounts/                     # Administrator-only user management
│   ├── migrations/
│   ├── templates/accounts/
│   ├── forms.py                  # AdminUserCreateForm, RoleChangeForm, UserSearchForm
│   ├── tests.py
│   ├── urls.py                   # mounted at administration/users/ (see KNOWN_ISSUES DEFECT-01)
│   └── views.py
├── bloodbank/                    # Project settings, root URLconf, shared constants
│   ├── constants.py              # BLOOD_GROUP_CHOICES, shelf-life/eligibility-interval constants
│   ├── settings.py
│   └── urls.py
├── templates/base.html          # Shared design system every app's templates extend
│                                 # (light/dark/system theming, nav, metric/bar-chart CSS)
├── documents/                   # BBMS-13 database design PDF
├── Team 1_Blood Bank Management System.pdf   # The team's SRS
├── docs/                        # Deeper documentation (this README links each file)
├── .env.example
├── manage.py
└── requirements.txt
```

## User roles and permissions

Roles are derived directly from Django's built-in `User` flags — there is
no separate "role" field to drift out of sync with reality:

| Role | Definition |
|---|---|
| Anonymous | Not logged in |
| Donor | Logged in, `is_staff=False`, `is_superuser=False` — granted automatically and only by self-registration |
| Blood bank staff | `is_staff=True` |
| Administrator | `is_superuser=True` (also satisfies every staff check) |

| Action | Anonymous | Donor | Staff | Admin |
|---|:---:|:---:|:---:|:---:|
| View login page | Yes | Yes¹ | Yes | Yes |
| Register as donor | Yes | —¹ | — | — |
| Search blood availability | No | Yes | Yes | Yes |
| Submit a blood request | Yes | Yes | Yes | Yes |
| Track a blood request by ID | Yes | Yes | Yes | Yes |
| View/update own donor profile | No | Yes² | n/a³ | n/a³ |
| View donor list | No | **No (403)** | Yes | Yes |
| View a donor's detail record | No | **No (403), even their own** | Yes | Yes |
| Change donor eligibility status | No | **No (403)** | Yes | Yes |
| View own donation history | No | Yes² | n/a³ | n/a³ |
| Record a donation / view donation list | No | **No (403)** | Yes | Yes |
| Review blood request queue (search/filter) | No | **No (403)** | Yes | Yes |
| Issue blood against a request | No | **No (403)** | Yes | Yes |
| View inventory batch dashboard / adjust a batch | No | **No (403)** | Yes | Yes |
| View the audit log | No | **No (403)** | Yes | Yes |
| View/create administrator accounts, change roles | No | **No (403)** | **No (403)** | Yes |
| Django admin site | No | No | No⁴ | Yes |

¹ Already-authenticated users are redirected away from login/register.
² Scoped to `request.user`'s own profile; the view takes no ID parameter.
³ Staff/admin accounts created outside donor self-registration have no
donor profile at all.
⁴ Unless that staff account is also `is_superuser`.

Enforcement point: `authentication/decorators.py:staff_required` /
`admin_required` — redirect-to-login when anonymous, HTTP 403 when
authenticated but not the required role. Applied on the server in every
restricted view across `inventory`, `donors`, `donations`, `auditlog`
and `accounts`; the nav bar hides links a role can't use for clarity,
but every view re-checks the role on every request regardless of how
the URL was reached, and self-service views (own profile, own donation
history) take no id parameter at all rather than trusting a URL value.
See `donors/tests.py`, `donations/tests.py`, `inventory/tests_access.py`
and `accounts/tests.py` for RBAC/IDOR tests that hit the URLs directly,
including crafted POSTs attempting privilege escalation.

## Functionality status

Full requirement-by-requirement detail, including source file references,
is in [`docs/REQUIREMENTS_TRACEABILITY.md`](docs/REQUIREMENTS_TRACEABILITY.md).
Summary:

**Implemented:** user login/logout (BBMS-F-001/002), donor
self-registration (F-003), donor self-service profile (F-004), staff
donor list/record view (F-005), donor eligibility status management
with history (F-006), donation recording with duplicate protection and
donor/staff history (F-007/008/009), single-sourced blood group list
(F-010), unified batch-level inventory with transaction ledger
(F-011/018/019), availability search (F-012/013), blood request
submission/tracking (F-014/015), staff approve/reject (F-016), blood
issue & distribution with audit log (F-017), search/filter across
donor, donation and request records (F-021), administrator account
management from the application (F-020), expiry exclusion (F-022).

**Known, documented limitation, not "pending":** eligibility is still
staff-set rather than auto-recomputed from donation history —
`donations.models.next_eligible_date()` exists and is surfaced on the
donor dashboard, but nothing currently flips `eligibility_status`
automatically from it. See `docs/KNOWN_ISSUES.md` §8.1.

## Known limitations

- Eligibility is not auto-recomputed from donation history (see above).
- Legacy aggregate stock migrated from the old `requests.BloodInventory`
  model is assigned an assumed 42-day shelf life from the migration
  date, because the old model never recorded a real collection date —
  see `docs/KNOWN_ISSUES.md` §8.2.
- `requests:detail`'s tracking link is a public, unauthenticated URL by
  design (so a requester without an account can track their request) —
  see `docs/KNOWN_ISSUES.md` for the reasoning and the trade-off.
- HTTPS/HSTS settings exist in `bloodbank/settings.py` but are not
  actually served by anything in this repository — no deployment target
  is configured (BBMS-SR-003, see `docs/SECURITY_VALIDATION.md`).
- No browser-based/end-to-end verification of the UI was performed this
  session (automated tests use Django's test client, not a browser) —
  see `docs/TEST_EXECUTION_REPORT.md` §6.

Full write-up, including impact and suggested resolutions, is in
[`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md).

## Future enhancements

Not built, and not claimed as built anywhere in this repository:

- Automatic eligibility recomputation from donation history.
- A real, non-assumed shelf life for legacy migrated stock (would
  require re-collecting collection dates from donors/records, which
  this project has no source for).
- A bespoke per-section sidebar/breadcrumb shell beyond the shared
  `templates/base.html` navigation (Part 7.C of the project's UI
  redesign brief) — the shared nav and theming cover every page, but a
  dedicated breadcrumb trail per section was not built.
- Production deployment configuration (the HTTPS settings in
  `bloodbank/settings.py` are present and DEBUG-gated, but no deployment
  target — web server, process manager, static file hosting — is
  configured in this repository).
- Dependency/vulnerability scanning in CI.
- A true concurrent-request (not sequential-proxy) test for the
  inventory locking path.

## Team

| SRN | Name | Sprint 1/2 area (per the SRS Division of Work) |
|---|---|---|
| PES2UG24CS314 | Nidhi Karkada | User Authentication and Donor Management |
| PES2UG24CS361 | Pramay Dubey | Blood Donation Management and Blood Group Management |
| PES2UG24CS343 | Pavan E Naik | Blood Inventory Management and Blood Availability Search |
| PES2UG24CS326 | Nishit Suresh | Blood Request Management, Issue & Distribution, Administrative Management |

(Allocation as stated in the team's SRS; actual code authorship per
`git log` differs in places — notably, the Donation Management module
(F-007/008/009, allocated to Pramay Dubey) and the administrator user
management module (F-020, allocated to Nishit Suresh) were built in
this patch series. See
[`docs/REQUIREMENTS_TRACEABILITY.md`](docs/REQUIREMENTS_TRACEABILITY.md)
for what was actually built by whom, where that's established.)

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for branch naming, commit
conventions, the pull request workflow, and how to resolve a merge
conflict without a force-push.

## Documentation index

| Document | Covers |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | App structure, models/relationships, views/URLs, templates, auth flow, Mermaid diagrams |
| [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) | Step-by-step workflows for administrators, staff and donors |
| [`docs/TESTING.md`](docs/TESTING.md) | Test framework, how to run tests, what each test file covers |
| [`docs/REQUIREMENTS_TRACEABILITY.md`](docs/REQUIREMENTS_TRACEABILITY.md) | Every SRS requirement ID mapped to implementation status and source files |
| [`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md) | Outstanding technical issues, their impact, and suggested resolutions (including which earlier issues this patch series fixed) |
| [`docs/SECURITY_VALIDATION.md`](docs/SECURITY_VALIDATION.md) | Every SRS security requirement and additional project-level security check, each with test evidence |
| [`docs/DEFECT_LOG.md`](docs/DEFECT_LOG.md) | Defects actually found and fixed while building/testing this patch series |
| [`docs/TEST_EXECUTION_REPORT.md`](docs/TEST_EXECUTION_REPORT.md) | Raw command output for every check/test/performance run, and what was *not* run |
| [`docs/TEST_METRICS.md`](docs/TEST_METRICS.md) | Coverage-by-type, test count over time, defect metrics |
| [`docs/TEST_SIGN_OFF.md`](docs/TEST_SIGN_OFF.md) | The full verification checklist with evidence for each item |
| [`docs/FINAL_DEFINITION_OF_DONE.md`](docs/FINAL_DEFINITION_OF_DONE.md) | The 18-point Definition of Done applied to every requirement |
| [`docs/COMMIT_PLAN.md`](docs/COMMIT_PLAN.md) | An earlier, patch-file-based route to the same history: order, commit messages, and how to apply each `.patch` |
| [`GIT_COMMIT_PLAN.md`](GIT_COMMIT_PLAN.md) | The current route: 24 suggested commits for this final assembled codebase, with exact file groups and commands |
| [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md) | Every requirement: previous status, what was implemented, files, tests, final status, limitations |
| [`DEMO_GUIDE.md`](DEMO_GUIDE.md) | Step-by-step script for demonstrating the full end-to-end workflow with the real seeded demo accounts |
| [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md) | One-page, honest summary of every open limitation (fuller detail in `docs/KNOWN_ISSUES.md`) |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Git workflow for this repository |
| [`SPRINT2_REPORT.md`](SPRINT2_REPORT.md) | The Sprint 2 (donor management) delivery report |
