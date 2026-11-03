# Implementation Summary

This document is the single entry point for what this patch series
actually changed: every requirement it touched, what its status was
before, what was built, which files and tests back that claim, and what
limitation (if any) remains. It is a summary — the full detail for any
row lives in [`docs/REQUIREMENTS_TRACEABILITY.md`](docs/REQUIREMENTS_TRACEABILITY.md)
(requirement-by-requirement), [`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md)
(issue-by-issue, including what this series fixed), and
[`docs/TEST_EXECUTION_REPORT.md`](docs/TEST_EXECUTION_REPORT.md) (raw
command output backing every test/check claim below).

**Scope note, stated plainly:** this patch series was built against the
project ZIP supplied as the source of truth for this work session, in a
disposable scratch Git repository used only to produce the patch series
described in [`docs/COMMIT_PLAN.md`](docs/COMMIT_PLAN.md) — it is not a
record of commits made to the real project repository, and no commit,
push, or pull request was made against GitHub at any point. The person
running this project applies the patches and creates the real commits
themselves, from their own machine, using their own Git history and
credentials.

## How to read the status columns

- **Implemented** — the feature exists, is exercised by a test that
  checks the resulting state (not just an HTTP 200), and that test
  passed in this environment (see `docs/TEST_EXECUTION_REPORT.md`).
- **Implemented, with a limitation** — the feature works, but something
  about it is narrower than the requirement's ideal reading; the
  limitation is named, not hidden.
- **Settings present, deployment not configured** — application-level
  code exists but the requirement also needs something outside this
  codebase (a deployment target) that was not built.
- **Not verifiable from code** — the requirement describes an
  operational property (uptime, hosting) that no amount of code review
  can confirm.

## Functional requirements (BBMS-F-xxx)

| ID | Requirement | Previous status | What was implemented | Files | Tests | Final status | Limitation |
|---|---|---|---|---|---|---|---|
| F-001/002 | Login / logout | Implemented (Sprint 1/2) | Unchanged this series | `authentication/` | `authentication/tests/test_login.py`, `test_logout.py` | Implemented | — |
| F-003/004/005 | Donor registration, self-profile, staff donor list/record | Implemented (Sprint 1/2) | Unchanged this series | `donors/` | `donors/tests.py` | Implemented | — |
| F-006 | Staff mark donor eligibility, informed by donation history where possible | Implemented, no history, no audit trail | Added `EligibilityHistory` (every change preserved, not just the latest); `set_eligibility()` now writes history + audit entry in one transaction; donor dashboard surfaces `next_eligible_date()` as a reference point | `donors/models.py`, `donors/views.py` | `donors/tests.py::EligibilityHistoryTests` (3) | Implemented, with a limitation | Still staff-set, not auto-applied from history — see `docs/KNOWN_ISSUES.md` §8.1 |
| F-007 | Staff record a new blood donation | **Missing** — no code existed | New `donations` app: `Donation` model with a unique `collection_reference` (the duplicate-submission guard), `record_donation()` service, staff `record` view/form/template | `donations/models.py`, `services.py`, `forms.py`, `views.py` | `donations/tests.py::DonationServiceTests` (5) | Implemented | Built in this patch series, not by the SRS-allocated owner — see "Division of work" below |
| F-008 | Donor views own donation history | **Missing** | `my_donation_history` (no pk in the URL at all — IDOR-safe by construction, not by permission check), `donor_donation_history` (staff, operational lookup by pk) | `donations/views.py` | `donations/tests.py::DonationViewAccessTests` (5), including `test_donor_sees_only_their_own_history_not_a_url_pk` | Implemented | — |
| F-009 | Donation automatically updates inventory | **Missing** (and blocked by the F-011/018 duplicate-model issue — see below) | `record_donation()` is one `@transaction.atomic` call: create `Donation`, then (only if not rejected) `inventory.services.receive_batch()` — both or neither | `donations/services.py` | `donations/tests.py::test_record_donation_creates_donation_and_credits_inventory`, `test_rejected_donation_credits_nothing` | Implemented | Depended on the inventory-unification fix (§ below) landing first |
| F-010 | Single master list of 8 blood groups | Implemented, but duplicated independently in 3 places | One shared `bloodbank/constants.py:BLOOD_GROUP_CHOICES`, imported everywhere; a guard test (`SharedConstantConsistencyTests`) catches future drift | `bloodbank/constants.py` | `requests/tests.py::SharedConstantConsistencyTests` | Implemented | — |
| F-011/018/019 | Inventory summary; issuing reduces inventory; a record of every transaction | Implemented, but on **two independent, unsynced `BloodInventory` models** | Unified into one model (`inventory.BloodInventory`, batch-level) with `quantity`/`quantity_remaining`, plus an append-only `InventoryTransaction` ledger; `inventory/services.py` is the only code path allowed to mutate stock | `inventory/models.py`, `services.py`, `views.py`; `requests/migrations/0003_remove_duplicate_inventory.py` (data migration, converts legacy rows first) | `inventory/tests.py`, `tests_services.py` (8), `tests_access.py` (4) | Implemented | See `docs/KNOWN_ISSUES.md` §1 for the fix's full history and §8.2 for the one assumption the data migration makes |
| F-012/013 | Availability search, display to authenticated users | Implemented | Unchanged logic; reads from the now-unified model | `inventory/views.py` | `inventory/tests.py` | Implemented | — |
| F-014/015/016/017 | Request submission, tracking, staff review, issue | Implemented | `issue_blood` now calls `inventory.services.issue_units()` (FIFO by expiry, `select_for_update()`) instead of decrementing a local aggregate row; an explicit guard now rejects a second issue against the same request | `requests/views.py` | `requests/tests.py` | Implemented | Tracking link is a public bearer-token-style URL by design — see `docs/KNOWN_ISSUES.md` §2 |
| F-020 | Administrator creates/updates/deactivates accounts, in-app | **Missing** — only `createsuperuser` / Django admin | New `accounts` app on top of Django's own `User`/`UserCreationForm`: create account with a validated `role` dropdown (never a raw `is_staff`/`is_superuser` POST field), update details, change role, activate/deactivate — each guarded against leaving zero active superusers and audited | `accounts/forms.py`, `views.py` | `accounts/tests.py` (10), including `test_staff_cannot_create_admin_account_via_crafted_post`, both last-superuser guard tests | Implemented | Built in this patch series, not by the SRS-allocated owner — see "Division of work" below |
| F-021 | Staff filter/search donor, donation and request records | Partial — donor list only | Added search/filter/pagination to `donations.donation_list` and `requests.request_queue` (status/blood group/hospital) | `donations/views.py`, `requests/views.py` | `donations/tests.py`, `requests/tests.py::test_queue_can_be_filtered_by_status_and_blood_group` | Implemented | All three record types now searchable |
| F-022 | Exclude expired units from availability | Implemented | Unchanged logic, now against the unified model | `inventory/services.py:available_units` | `inventory/tests.py`, `inventory/tests_services.py::test_issue_units_excludes_expired_batches` | Implemented | — |

## Non-functional requirements (BBMS-NF-xxx)

| ID | Requirement | Previous status | What was implemented | Final status | Limitation |
|---|---|---|---|---|---|
| NF-001 | Common pages meet a performance target | Verified for 3 pages | `inventory/performance_test.py` extended to all 8 named pages (login, request tracking, availability search, inventory dashboard, donor list, donation list, request queue, administrator user list); all p90 well under 3s | Verified for 8 pages | Measures Django's in-process test client, not a production WSGI server — see `docs/TEST_EXECUTION_REPORT.md` §4 |
| NF-003/004 | Consistent screen design; modules clearly separated | Implemented | Seven apps, each one responsibility; one shared `templates/base.html` design system with light/dark/system theming | Implemented | — |
| NF-005 | Inventory counts stay consistent with records | Not fully met (two models) | Single source of truth (see F-011/018/019 above), every write atomic and `select_for_update()`-locked | Implemented | — |

## Security requirements (BBMS-SR-xxx)

See [`docs/SECURITY_VALIDATION.md`](docs/SECURITY_VALIDATION.md) for the
full mapping with test evidence. Summary: SR-001/002/004/005
**Implemented** (SR-002 extended to the new `admin_required` decorator
and the three new apps; SR-005 now covers all 14 audit action types,
not just `BloodIssue` rows and eligibility timestamps). SR-003 (HTTPS)
remains **Settings present, deployment not configured** — this patch
series did not add a deployment target, and does not claim to.

**Important honesty note:** the originating task description referred
to security requirements "SEC-01" through "SEC-13." The project's
actual SRS defines exactly five numbered security requirements
(BBMS-SR-001 through 005). Rather than inventing eight additional
official-sounding SRS IDs to reach "13," `docs/SECURITY_VALIDATION.md`
maps the real five and separately lists nine additional, unnumbered
project-level security checks (CSRF, IDOR via no-URL-parameter,
privilege-escalation-via-crafted-POST, last-superuser lockout
prevention, duplicate-submission prevention, no-negative-stock,
session security, input validation) — each with its own test evidence,
clearly distinguished from the numbered SRS items.

## Division of work — a disclosed divergence from the SRS

The SRS's own "Division of Work" allocates Donation Management
(F-007/008/009) to Pramay Dubey and Administrative account management
(F-020) to Nishit Suresh. Both were, in fact, built in this patch
series rather than by those teammates. This is stated here and in
`docs/REQUIREMENTS_TRACEABILITY.md` plainly, not smoothed over — the
person applying these patches should decide how to represent authorship
(e.g. attributing the relevant commits to the actual owner, or noting
the division of work changed) rather than this document silently
implying the original allocation still holds.

## What this patch series did NOT do

- **No Git commits, pushes, or pull requests against the real
  repository.** Every commit referenced above and in
  `docs/COMMIT_PLAN.md` lives only in a disposable local scratch
  repository used to produce the `.patch` files in
  `BBMS_PATCH_SERIES.zip`. Applying those patches and creating the real
  commits is the applier's own action, from their own machine.
- **No browser-based or end-to-end UI verification.** Every test in
  this series uses Django's test client (server-side request/response
  assertions). See `docs/TEST_EXECUTION_REPORT.md` §6.
- **No dependency/vulnerability scan.**
- **No production deployment or HTTPS-serving configuration.**
- **No fabricated test results, defects, or screenshots.** Every number
  in this document and in `docs/TEST_EXECUTION_REPORT.md` was produced
  by actually running the command shown.

## Patch series and verification

See [`docs/COMMIT_PLAN.md`](docs/COMMIT_PLAN.md) for the ordered patch
list, suggested commit messages, and the exact commands to apply them
against a fresh copy of the original project, and
[`docs/TEST_SIGN_OFF.md`](docs/TEST_SIGN_OFF.md) /
[`docs/FINAL_DEFINITION_OF_DONE.md`](docs/FINAL_DEFINITION_OF_DONE.md)
for the full verification checklist this series was held to.
