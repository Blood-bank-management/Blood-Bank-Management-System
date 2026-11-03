# Security validation

This document maps every security control actually implemented in this
repository to the requirement it satisfies, where it lives, how it is
tested, and what running that test actually showed.

**On the "SEC-01 through SEC-13" item**: the Jira security-validation task
refers to 13 controls (SEC-01..SEC-13), but neither the bundled SRS
("Team 1_Blood Bank Management System.pdf") nor any document in this
repository defines 13 numbered security controls. The SRS defines exactly
five security requirements, **BBMS-SR-001 through BBMS-SR-005** (see
`docs/REQUIREMENTS_TRACEABILITY.md`). Per this task's own instruction
("if the SRS does not actually define 13 controls, do not invent official
SRS IDs"), this document maps the five real SR items in Part A below, and
lists the additional security-relevant checks this project actually has
-- which happen to number more than 13 once IDOR, CSRF, RBAC and input
validation are broken out per app -- as unnumbered, clearly-separate
project-level checks in Part B, rather than inventing SRS IDs for them.

## Part A: SRS security requirements (BBMS-SR-001..005)

| ID | Requirement | Implementation | Test case | Result | Evidence |
|---|---|---|---|---|---|
| BBMS-SR-001 | Unauthenticated requests to protected pages are redirected to login | `django.contrib.auth.decorators.login_required` on every view that needs it; `authentication.decorators.staff_required`/`admin_required` wrap it for role-gated views | `authentication/tests/test_access.py::test_auth_ut_07_unauthenticated_user_cannot_access_protected_page`; equivalents in `donors/tests.py`, `donations/tests.py`, `inventory/tests_access.py`, `auditlog/tests.py`, `accounts/tests.py` | **Pass** (ran as part of the 114-test suite, see TEST_EXECUTION_REPORT.md) | Each test asserts a 302 redirect to the login URL for an anonymous client |
| BBMS-SR-002 | Donor/requester accounts cannot reach administrative functions | `staff_required`/`admin_required` decorators, enforced server-side in the view, not just hidden from navigation | `donors/tests.py` (staff-only donor list/detail), `inventory/tests_access.py`, `donations/tests.py`, `auditlog/tests.py`, `accounts/tests.py::test_staff_cannot_access_user_list`/`test_donor_cannot_access_user_list` | **Pass** | Each asserts 403 for an authenticated-but-unauthorized user, distinct from the 302 an anonymous user gets |
| BBMS-SR-003 | HTTPS for all client-server communication | `bloodbank/settings.py`: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_*`, all `not DEBUG` | Manual inspection (grep) of `bloodbank/settings.py` | **Settings present, deployment not configured** -- unchanged from before this patch series. These are no-ops while `DEBUG=True` (the project's local-dev default) and no deployment in this repository actually serves HTTPS. This is a genuine, documented gap, not something this patch claims to fix -- see `docs/KNOWN_ISSUES.md` §5 | `grep -n SECURE_ bloodbank/settings.py` |
| BBMS-SR-004 | Passwords stored using a secure hash | Django's default password hashing (`django.contrib.auth`), used by login, donor self-registration (`donors.forms.DonorRegistrationForm`) and admin account creation (`accounts.forms.AdminUserCreateForm`, which subclasses `UserCreationForm`) | `authentication/tests/test_login.py`, `donors/tests.py` | **Pass** | Tests assert the stored `User.password` value is not the plaintext password |
| BBMS-SR-005 | Audit entry whenever inventory or request status changes | `auditlog.models.record()`, called from `inventory.services` (receive/issue/adjust), `donations.services.record_donation`, `requests.views` (submit/approve/reject/issue), `donors.models.DonorProfile.set_eligibility`, `accounts.views` (create/role-change/activate). Before this patch series this was **partially implemented** (only `BloodIssue` rows and the two `eligibility_updated_by/_at` fields); it is now a single, consistent `AuditLog` table covering all 14 action types listed in the Jira audit-logging requirement | `auditlog/tests.py`, `accounts/tests.py::test_role_change_is_audited`, `donors/tests.py::EligibilityHistoryTests::test_eligibility_change_writes_an_audit_log_entry` | **Pass** | Each test asserts a matching `AuditLog` row exists after the action |

## Part B: additional project-level security checks

These are not separately numbered in the SRS; they are broken out here
because each is independently meaningful and independently tested.

| Check | Implementation | Test evidence |
|---|---|---|
| CSRF protection on every POST | Django's `CsrfViewMiddleware` (on by default, never disabled for any view in this project -- confirmed by grep for `csrf_exempt`, which returns no matches) and `{% csrf_token %}` in every form template | `authentication/tests/test_login.py::...assertContains(response, "csrfmiddlewaretoken")`; equivalent assertions elsewhere |
| IDOR protection: donor's own profile/history has no URL parameter to tamper with | `donors.views.profile`, `donations.views.my_donation_history` never take a pk/id from the URL -- they always resolve to `request.user`'s own records | `donations/tests.py::test_donor_history_url_has_no_id_parameter_to_tamper_with` (asserts `resolve(...).kwargs == {}`); `test_donor_sees_only_their_own_history_not_a_url_pk` |
| IDOR protection: request tracking by unguessable UUID, not sequential ID | `requests.models.BloodRequest.tracking_id` is a `UUIDField`, not the row's integer PK; the integer PK is never exposed in any URL | Design-level control (see `docs/ARCHITECTURE.md`); unchanged from before this patch series |
| Privilege escalation via crafted POST | Role is only ever set through `accounts.forms.AdminUserCreateForm`'s validated `role` ChoiceField / `accounts.forms.RoleChangeForm`, both reachable only through `admin_required` views -- there is no code path that reads `is_staff`/`is_superuser` directly from request data | `accounts/tests.py::test_staff_cannot_create_admin_account_via_crafted_post` |
| Self-escalation / lockout prevention | `accounts.views._active_superuser_count()` blocks a role change or deactivation that would leave zero active superusers | `accounts/tests.py::test_cannot_demote_the_last_active_superuser`, `test_cannot_deactivate_the_last_active_superuser` |
| Duplicate-submission / double-credit prevention | `donations.models.Donation.collection_reference` has a unique DB constraint; resubmitting raises `DuplicateDonationError` instead of crediting stock twice | `donations/tests.py::test_duplicate_collection_reference_is_rejected` |
| No negative stock / overselling | `inventory.services.issue_units` locks candidate batches with `select_for_update` inside `transaction.atomic()` and raises before any write if requested quantity exceeds availability | `inventory/tests_services.py::test_issue_units_raises_on_insufficient_stock_and_changes_nothing`, `test_no_negative_stock_possible_via_adjust`, `test_concurrent_issue_cannot_drive_balance_negative` |
| Session security | Django's default session framework; `SESSION_COOKIE_SECURE` set per BBMS-SR-003 above; no custom session handling that could bypass Django's own protections | Covered by Django's own test suite (not re-tested here) plus the SR-003 row above |
| Input validation | Every form (`DonorRegistrationForm`, `DonationRecordForm`, `BloodRequestForm`, `InventoryAdjustmentForm`, `AdminUserCreateForm`, ...) is a Django `Form`/`ModelForm` with explicit field types/validators; nothing parses raw `request.POST` without going through form validation first | Covered throughout the 114-test suite; explicitly for quantity/date validation in `donations/tests.py::test_donation_quantity_must_be_positive`, `test_donation_collection_date_cannot_be_future` |

## What this document does not claim

- It does not claim HTTPS is actually being served anywhere (BBMS-SR-003
  remains a configuration-only control -- see above and
  `docs/KNOWN_ISSUES.md` §5).
- It does not claim a penetration test, dependency vulnerability scan, or
  any tooling-based security scan was run. Every result above comes from
  the project's own Django test suite (`python manage.py test`), run and
  reported in `docs/TEST_EXECUTION_REPORT.md`.
