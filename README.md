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
- Donation recording and donor donation history — **pending**, no
  Donation Management module exists yet (see
  [Functionality status](#functionality-status))
- Administrator user management (create/deactivate accounts from the
  app) — **pending**, currently done via Django admin / `createsuperuser`
  only

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
| `authentication` | Login, logout, the authenticated landing page | — (uses Django's built-in `User`) |
| `donors` | Donor self-registration, self-service profile, staff donor directory and eligibility management | `DonorProfile` |
| `inventory` | Blood availability search, inventory summary, expired-unit tracking | `BloodInventory` (per-batch) |
| `requests` | Blood request submission/tracking, staff review, blood issue and distribution | `BloodRequest`, `BloodInventory` (aggregate), `BloodIssue` |

`inventory` and `requests` each define their own, different
`BloodInventory` model — see
[Known limitations](#known-limitations) and
[`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md).

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

It also seeds starting inventory (five blood groups) and one sample
blood request. These are fake, local-only development credentials —
never reuse this password anywhere real, and never run this command
against a shared or production database.

## Running tests

```bash
python manage.py test
```

Executed in this environment on the current `main` branch: **71/71
tests pass.** Django's default test discovery only picks up files
matching `test*.py`, which `inventory/performance_test.py` does not — run
it explicitly:

```bash
python manage.py test inventory.performance_test -v 2
```

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
├── authentication/              # Login, logout, landing page
│   ├── templates/authentication/
│   ├── tests/
│   ├── decorators.py            # staff_required (shared RBAC decorator)
│   ├── forms.py                 # username-or-email login form
│   ├── urls.py
│   └── views.py
├── donors/                      # Donor self-registration, profile, staff management
│   ├── management/commands/seed_demo_data.py
│   ├── migrations/
│   ├── templates/donors/
│   ├── admin.py
│   ├── decorators.py            # re-exports authentication.decorators.staff_required
│   ├── forms.py
│   ├── models.py                # DonorProfile
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── inventory/                   # Availability search, inventory summary, expired units
│   ├── migrations/
│   ├── templates/inventory/
│   ├── models.py                # BloodInventory (per-batch)
│   ├── performance_test.py      # BBMS-53 perf smoke test (run separately)
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── requests/                    # Blood requests, staff review, issue/distribution
│   ├── migrations/
│   ├── templates/requests/
│   ├── models.py                # BloodRequest, BloodInventory (aggregate), BloodIssue
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── bloodbank/                   # Project settings, root URLconf
│   ├── settings.py
│   └── urls.py
├── templates/base.html          # Shared design system every app's templates extend
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
| Review blood request queue | No | **No (403)** | Yes | Yes |
| Issue blood against a request | No | **No (403)** | Yes | Yes |
| View inventory summary / expired units | No | **No (403)** | Yes | Yes |
| Django admin site | No | No | No⁴ | Yes |

¹ Already-authenticated users are redirected away from login/register.
² Scoped to `request.user`'s own profile; the view takes no ID parameter.
³ Staff/admin accounts created outside donor self-registration have no
donor profile at all.
⁴ Unless that staff account is also `is_superuser`.

Enforcement point: `authentication/decorators.py:staff_required` —
redirect-to-login when anonymous, HTTP 403 when authenticated but not
staff. Applied on the server in every staff-only view across `inventory`
and `donors`; the nav bar hides links a role can't use for clarity, but
every view re-checks the role on every request regardless of how the URL
was reached. See `donors/tests.py` for RBAC/IDOR tests that hit the URLs
directly.

## Functionality status

Full requirement-by-requirement detail, including source file references,
is in [`docs/REQUIREMENTS_TRACEABILITY.md`](docs/REQUIREMENTS_TRACEABILITY.md).
Summary:

**Implemented:** user login/logout (BBMS-F-001/002), donor
self-registration (F-003), donor self-service profile (F-004), staff
donor list/record view (F-005), donor eligibility status management
(F-006), blood group master list (F-010), inventory summary (F-011),
availability search (F-012/013), blood request submission/tracking
(F-014/015), staff approve/reject (F-016), blood issue & distribution
with audit log (F-017/018/019), expiry exclusion (F-022).

**Partially implemented:** staff filter/search (F-021) — present for the
donor list only, not yet for donation or request records.

**Pending (no code exists for these):** donation recording and donor
donation history (F-007/008/009), administrator account
create/update/deactivate from the application itself (F-020) — currently
only possible via `createsuperuser` or the Django admin site directly.

## Known limitations

- Two independent `BloodInventory` models (`inventory` app: per-batch;
  `requests` app: per-group aggregate) that are not kept in sync with
  each other.
- Donor eligibility is staff-set manually, not auto-derived from donation
  history, because the donation-history data doesn't exist yet.
- `requests:detail`'s tracking link is a public, unauthenticated URL by
  design (so a requester without an account can track their request) —
  see `docs/KNOWN_ISSUES.md` for the reasoning and the trade-off.

Full write-up, including impact and suggested resolutions, is in
[`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md).

## Future enhancements

Not built, and not claimed as built anywhere in this repository:

- Donation Management module (record a donation, auto-update inventory,
  donor donation history) — BBMS-F-007/008/009.
- In-app administrator account management — BBMS-F-020.
- Search/filter across donation and request records, beyond the existing
  donor-list search — BBMS-F-021.
- Reconciling the two `BloodInventory` models into one.
- Automatic eligibility calculation once donation history exists.
- Production deployment configuration (the HTTPS settings in
  `bloodbank/settings.py` are present and DEBUG-gated, but no deployment
  target — web server, process manager, static file hosting — is
  configured in this repository).

## Team

| SRN | Name | Sprint 1/2 area (per the SRS Division of Work) |
|---|---|---|
| PES2UG24CS314 | Nidhi Karkada | User Authentication and Donor Management |
| PES2UG24CS361 | Pramay Dubey | Blood Donation Management and Blood Group Management |
| PES2UG24CS343 | Pavan E Naik | Blood Inventory Management and Blood Availability Search |
| PES2UG24CS326 | Nishit Suresh | Blood Request Management, Issue & Distribution, Administrative Management |

(Allocation as stated in the team's SRS; actual code authorship per
`git log` differs in places — see
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
| [`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md) | Outstanding technical issues, their impact, and suggested resolutions |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Git workflow for this repository |
| [`SPRINT2_REPORT.md`](SPRINT2_REPORT.md) | The Sprint 2 (donor management) delivery report |
