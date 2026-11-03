# Requirements Traceability Matrix

Source: `Team 1_Blood Bank Management System.pdf` (the project's own SRS,
bundled in the repository root), §4 Functional Requirements, §5
Non-Functional Requirements, §5.1.2 Security Requirements, and the
"Division of Work" tables in each section. Requirement IDs and the
module/person allocation are reproduced exactly as the SRS states them —
none invented, none renumbered.

Implementation status is based on inspecting the actual code in this
repository and running its test suite (`python manage.py test`, 114/114
passing — see [`TESTING.md`](TESTING.md)), not on the SRS's own
"N" (not yet) status column, which predates this code.

**Updated for the patch series in [`IMPLEMENTATION_SUMMARY.md`](../IMPLEMENTATION_SUMMARY.md)**
(commits `cdea607`..`474849e`): the rows for BBMS-F-006/007/008/009/010/
018/020, BBMS-NF-001/005, and BBMS-SR-002/005 below reflect the current
code, not the original Sprint 2 state. Where this patch series changed a
row, that is noted inline rather than silently rewritten.

## Functional requirements

| Req ID | Requirement (abbreviated) | SRS module/owner | Status | Source files | Notes |
|---|---|---|---|---|---|
| BBMS-F-001 | Login with valid username/email + password | Nidhi Karkada — User Authentication and Donor Management | **Implemented** | `authentication/views.py`, `forms.py`, `urls.py`, `templates/authentication/login.html`; tests in `authentication/tests/test_login.py` | — |
| BBMS-F-002 | Logout ends the session | Nidhi Karkada | **Implemented** | `authentication/urls.py` (Django's built-in `LogoutView`), `templates/base.html` (logout control); tests in `authentication/tests/test_logout.py` | POST-only, CSRF-protected |
| BBMS-F-003 | Donor self-registration | Nidhi Karkada | **Implemented** | `donors/forms.py:DonorRegistrationForm`, `donors/views.py:register`, `donors/templates/donors/register.html`; tests in `donors/tests.py:DonorRegistrationTests` | Always creates a minimum-privilege account |
| BBMS-F-004 | Donor updates own personal/contact info | Nidhi Karkada | **Implemented** | `donors/forms.py:DonorProfileUpdateForm`, `donors/views.py:profile`, `donors/templates/donors/profile.html`; tests in `donors/tests.py:DonorProfileTests` | — |
| BBMS-F-005 | Staff view donor list and individual records | Nidhi Karkada | **Implemented** | `donors/views.py:donor_list`, `donor_detail`, `donors/templates/donors/donor_list.html`, `donor_detail.html`; tests in `donors/tests.py:StaffDonorManagementTests` | Staff-only, paginated, searchable |
| BBMS-F-006 | Staff mark donor eligibility (eligible / temporarily ineligible) based on donation history | Nidhi Karkada | **Implemented, with a limitation** | `donors/models.py:DonorProfile.set_eligibility`, `donors/models.py:EligibilityHistory`, `donors/views.py:donor_detail`, `donors/forms.py:EligibilityUpdateForm`, `donations/models.py:next_eligible_date` | Eligibility is still set by staff judgment (now with a full change-history audit trail, not just the latest value); `next_eligible_date()` surfaces a donation-history-derived suggestion on the donor dashboard but does not auto-apply it — see `docs/KNOWN_ISSUES.md` §8.1 |
| BBMS-F-007 | Staff record a new blood donation | Pramay Dubey — Blood Donation Management and Blood Group Management | **Implemented** | `donations/models.py:Donation`, `donations/forms.py:DonationRecordForm`, `donations/views.py:record`, `donations/templates/donations/record.html`; tests in `donations/tests.py:DonationServiceTests` | Implemented in this patch series (see `IMPLEMENTATION_SUMMARY.md`), not by Pramay Dubey as the SRS allocates it — divergence noted in "Division of Work" below |
| BBMS-F-008 | Donor views own past donation history | Pramay Dubey | **Implemented** | `donations/views.py:my_donation_history` (no pk in the URL — IDOR-safe by construction), `donations/views.py:donor_donation_history` (staff), `donations/templates/donations/my_history.html`; tests in `donations/tests.py::DonationViewAccessTests` | — |
| BBMS-F-009 | Donation automatically updates blood inventory | Pramay Dubey | **Implemented** | `donations/services.py:record_donation` (atomic; calls `inventory.services.receive_batch`); tests in `donations/tests.py::test_record_donation_creates_donation_and_credits_inventory` | Depended on §1's duplicate-inventory-model fix landing first — see `docs/KNOWN_ISSUES.md` §1 |
| BBMS-F-010 | Maintain a master list of the 8 blood groups | Pramay Dubey | **Implemented** | `bloodbank/constants.py:BLOOD_GROUP_CHOICES` — now the single shared definition imported by `donors/models.py`, `requests/models.py`, `donations/models.py`, `inventory/models.py` and every view that previously hardcoded its own copy of the list | Fixed the "duplicated in two places" limitation this row previously noted |
| BBMS-F-011 | Staff view inventory summary by blood group | Pavan E Naik — Blood Inventory Management and Blood Availability Search | **Implemented** | `inventory/views.py:inventory_summary`, `templates/inventory/inventory_summary.html` | Staff-only (`@staff_required`, added Sprint 2 — this view had no role check at all until then) |
| BBMS-F-012 | Search blood availability by blood group | Pavan E Naik | **Implemented** | `inventory/views.py:availability_search`, `templates/inventory/availability_search.html`; tests in `inventory/tests.py` | Requires login, open to any authenticated role |
| BBMS-F-013 | Display available blood units to authenticated users | Pavan E Naik | **Implemented** | Same as F-012 — availability search shows the current count | — |
| BBMS-F-014 | Requester submits a blood request (group, quantity, reason) | Nishit Suresh — Blood Request Management, Blood Issue and Distribution, and Administrative Management | **Implemented** | `requests/forms.py:BloodRequestForm`, `requests/views.py:request_create`, `templates/requests/request_form.html`; tests in `requests/tests.py` | Open to anonymous requesters by design |
| BBMS-F-015 | Requester views their request's status | Nishit Suresh | **Implemented** | `requests/views.py:request_detail`, `templates/requests/request_detail.html` | Looked up by the request's UUID `tracking_id` — see Known limitations |
| BBMS-F-016 | Staff approve/reject a pending request | Nishit Suresh | **Implemented** | `requests/views.py:request_review`, `templates/requests/request_queue.html`; tests in `requests/tests.py` | Rejecting requires a review note |
| BBMS-F-017 | Staff issue blood against an approved request | Nishit Suresh | **Implemented** | `requests/views.py:issue_blood` | Staff-only |
| BBMS-F-018 | Issuing automatically reduces inventory | Nishit Suresh | **Implemented** | `requests/views.py:issue_blood` (atomic `transaction.atomic()`), `inventory/services.py:issue_units` (`select_for_update()`, FIFO by expiry) | Now operates on the single `inventory.BloodInventory` source of truth — see `docs/KNOWN_ISSUES.md` §1 |
| BBMS-F-019 | Maintain a record of every issue/distribution transaction | Nishit Suresh | **Implemented** | `requests/models.py:BloodIssue`, `inventory/models.py:InventoryTransaction` | One `BloodIssue` row per completed issue, with `issued_by` and `issued_at`, plus a matching `InventoryTransaction` ledger row per batch touched |
| BBMS-F-020 | Administrator creates/updates/deactivates user accounts | Nishit Suresh | **Implemented** | `accounts/views.py:user_list`/`user_create`/`user_detail`, `accounts/forms.py`, built on Django's own `User` model and `UserCreationForm`; tests in `accounts/tests.py` | Implemented in this patch series, not by Nishit Suresh as the SRS allocates it — divergence noted below. Guards against self-escalation and against removing the last active administrator |
| BBMS-F-021 | Staff filter/search donor, donation and request records | Nishit Suresh | **Implemented** | `donors/views.py:donor_list` (search by username/name/e-mail/blood group), `donations/views.py:donation_list` (search by donor/blood group/status), `requests/views.py:request_queue` (filter by status/blood group/hospital) | All three now have search/filter + pagination |
| BBMS-F-022 | Exclude expired units from availability | Nishit Suresh | **Implemented** | `inventory/views.py:availability_search`, `expired_units`; tests in `inventory/tests.py` | — |

## Non-functional requirements

| Req ID | Requirement (abbreviated) | Status | Notes |
|---|---|---|---|
| BBMS-NF-001 | Common page operations (login, search, viewing records) meet a performance target | **Verified for 8 pages** | `inventory/performance_test.py` asserts p90 < 3s for login, request tracking, availability search, inventory dashboard, donor list, donation list, request queue and administrative user list — see `docs/TEST_EXECUTION_REPORT.md` §4. Still not run by default test discovery (file is deliberately not renamed — see `docs/KNOWN_ISSUES.md` §7) and still measures the Django test client, not a production WSGI server. |
| BBMS-NF-002 | System remains available during normal working hours | **Not verifiable from code** | An operational/deployment commitment, not something the current local-dev-server codebase can demonstrate. |
| BBMS-NF-003 | Consistent, simple screen design | **Implemented** | One shared `templates/base.html` design system used by every page in the project (see [`ARCHITECTURE.md`](ARCHITECTURE.md) §6). |
| BBMS-NF-004 | Codebase organized into clearly separated modules | **Implemented** | Four Django apps, each with one clear responsibility (see [`ARCHITECTURE.md`](ARCHITECTURE.md) §3). |
| BBMS-NF-005 | Blood inventory counts stay consistent with records | **Implemented** | `inventory.BloodInventory` is the single source of truth (see `docs/KNOWN_ISSUES.md` §1, now fixed); every write to it goes through `inventory/services.py`, which is atomic and `select_for_update()`-locked, and writes a matching `InventoryTransaction` row. |
| BBMS-NF-006 | Accessible to authorized users from a [compatible environment] | **Implemented, narrowly** | Server-rendered HTML with no JS framework dependency works in any modern browser; no explicit cross-browser or mobile-device testing was performed. |

## Security requirements

| Req ID | Requirement (abbreviated) | SRS owner | Status | Source files | Notes |
|---|---|---|---|---|---|
| BBMS-SR-001 | Require valid username/email + password; unauthenticated requests redirected to login | Nidhi Karkada — Security objectives and authentication-related requirements | **Implemented** | `authentication/decorators.py:staff_required` and every `@login_required`/`@staff_required` view; tests across `authentication/tests/` and `donors/tests.py` | — |
| BBMS-SR-002 | Restrict administrative functions from donor/requester accounts | Pramay Dubey — Role-based access control requirements | **Implemented** | `authentication/decorators.py:staff_required`/`admin_required`, applied to every staff/admin-only view across `donors`, `inventory`, `donations`, `auditlog`, `accounts`; `requests.views` uses its own local `user_passes_test(is_staff)` for the same purpose | `admin_required` (is_superuser) is a separate check from `staff_required` (is_staff), added for the new administrator-only `accounts` app so ordinary staff cannot reach it; see [`ARCHITECTURE.md`](ARCHITECTURE.md) §3 for the one remaining stylistic inconsistency between `requests`' local check and the shared decorators |
| BBMS-SR-003 | HTTPS for all client-server communication | Pavan E Naik — Communication and password-storage security requirements | **Settings present, deployment not configured** | `bloodbank/settings.py` (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS settings — all gated on `DEBUG`) | These are no-ops while `DEBUG=True`; no actual HTTPS-serving deployment (web server, certificate) exists in this repository. These settings were briefly absent from `main` due to a merge issue — see [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md). |
| BBMS-SR-004 | Store passwords using a secure hash | Pavan E Naik | **Implemented** | Django's default password hashing (`django.contrib.auth`), used by both `authentication` login and `donors` registration; tests assert the stored value is not plaintext in both `authentication/tests/test_login.py` and `donors/tests.py` | — |
| BBMS-SR-005 | Audit entry whenever inventory or request status changes | Nishit Suresh — Audit logging requirement and overall security review | **Implemented** | `auditlog/models.py:AuditLog`/`record()`, called from `inventory/services.py`, `donations/services.py`, `requests/views.py` (submit/approve/reject/issue), `donors/models.py:DonorProfile.set_eligibility`, `accounts/views.py` (create/role-change/activate) | Was partial before this patch series (only `BloodIssue` rows and eligibility's two timestamp fields); now one consistent table covering all 14 action types the Jira audit-logging requirement names. Edits made directly via the Django admin site still bypass it, same as any Django admin edit bypasses application-level signals not wired to `post_save` — see `docs/KNOWN_ISSUES.md` §8 for what remains open |

## Division of Work (as stated in the SRS)

The SRS states separate Division-of-Work allocations per section. For
functional requirements (§4, reproduced above), the allocation is by
module: Nidhi Karkada — User Authentication and Donor Management; Pramay
Dubey — Blood Donation Management and Blood Group Management; Pavan E
Naik — Blood Inventory Management and Blood Availability Search; Nishit
Suresh — Blood Request Management, Blood Issue and Distribution, and
Administrative Management. For security requirements (§5.1.2): Nidhi
Karkada — security objectives and authentication-related requirements;
Pramay Dubey — role-based access control requirements; Pavan E Naik —
communication and password-storage security requirements; Nishit Suresh
— audit logging and overall security review.

Actual `git log` authorship does not line up perfectly with this
allocation in every case (for example, `inventory`'s login-protection and
expired-units work was committed by Pavan E Naik, consistent with the
SRS; the RBAC hardening on those same inventory views and the HTTPS
settings restoration in this documentation pass were committed by Nidhi
Karkada, outside her SRS-stated module, because they were found during
this audit and left unaddressed would have undermined requirements
documented here as "Implemented"). The entire Donation Management module
(BBMS-F-007/008/009, SRS-allocated to Pramay Dubey) and the
administrator-only `accounts` app (BBMS-F-020, SRS-allocated to Nishit
Suresh) were likewise built in the patch series this matrix now
reflects, not by those teammates. Where SRS allocation and actual
authorship diverge, this document states the SRS allocation (as
requested) and notes the divergence here rather than silently rewriting
history.

## Known limitations affecting this matrix

See [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) for full detail. §1 (duplicate
inventory models), §3 (eligibility history), and §6 (missing Donation
Management / Administrative account management) are now marked **fixed**
there, matching the "Implemented" rows above. Genuinely still open, as
of this matrix's last update: donor eligibility is staff-set rather than
fully auto-derived from donation history (BBMS-F-006, KNOWN_ISSUES §8.1);
the blood request tracking link's bearer-token trust model (BBMS-F-015,
KNOWN_ISSUES §2); HTTPS settings exist but no deployment serves HTTPS
(BBMS-SR-003, KNOWN_ISSUES §5); `inventory/performance_test.py` is still
excluded from default test discovery (KNOWN_ISSUES §7); the UI redesign
covers the shared design system and dashboard but not a bespoke
sidebar/breadcrumb shell (KNOWN_ISSUES §8.3); no browser-level visual
verification was performed (KNOWN_ISSUES §8.4).
