# Requirements Traceability Matrix

Source: `Team 1_Blood Bank Management System.pdf` (the project's own SRS,
bundled in the repository root), §4 Functional Requirements, §5
Non-Functional Requirements, §5.1.2 Security Requirements, and the
"Division of Work" tables in each section. Requirement IDs and the
module/person allocation are reproduced exactly as the SRS states them —
none invented, none renumbered.

Implementation status is based on inspecting the actual code in this
repository and running its test suite (`python manage.py test`, 71/71
passing — see [`TESTING.md`](TESTING.md)), not on the SRS's own
"N" (not yet) status column, which predates this code.

## Functional requirements

| Req ID | Requirement (abbreviated) | SRS module/owner | Status | Source files | Notes |
|---|---|---|---|---|---|
| BBMS-F-001 | Login with valid username/email + password | Nidhi Karkada — User Authentication and Donor Management | **Implemented** | `authentication/views.py`, `forms.py`, `urls.py`, `templates/authentication/login.html`; tests in `authentication/tests/test_login.py` | — |
| BBMS-F-002 | Logout ends the session | Nidhi Karkada | **Implemented** | `authentication/urls.py` (Django's built-in `LogoutView`), `templates/base.html` (logout control); tests in `authentication/tests/test_logout.py` | POST-only, CSRF-protected |
| BBMS-F-003 | Donor self-registration | Nidhi Karkada | **Implemented** | `donors/forms.py:DonorRegistrationForm`, `donors/views.py:register`, `donors/templates/donors/register.html`; tests in `donors/tests.py:DonorRegistrationTests` | Always creates a minimum-privilege account |
| BBMS-F-004 | Donor updates own personal/contact info | Nidhi Karkada | **Implemented** | `donors/forms.py:DonorProfileUpdateForm`, `donors/views.py:profile`, `donors/templates/donors/profile.html`; tests in `donors/tests.py:DonorProfileTests` | — |
| BBMS-F-005 | Staff view donor list and individual records | Nidhi Karkada | **Implemented** | `donors/views.py:donor_list`, `donor_detail`, `donors/templates/donors/donor_list.html`, `donor_detail.html`; tests in `donors/tests.py:StaffDonorManagementTests` | Staff-only, paginated, searchable |
| BBMS-F-006 | Staff mark donor eligibility (eligible / temporarily ineligible) based on donation history | Nidhi Karkada | **Implemented, with a limitation** | `donors/models.py:DonorProfile.set_eligibility`, `donors/views.py:donor_detail`, `donors/forms.py:EligibilityUpdateForm` | Eligibility is set by staff judgment, not auto-derived from donation history — see Known limitations below |
| BBMS-F-007 | Staff record a new blood donation | Pramay Dubey — Blood Donation Management and Blood Group Management | **Missing** | — | No donation model, view or template exists anywhere in the repository |
| BBMS-F-008 | Donor views own past donation history | Pramay Dubey | **Missing** | — | Depends on BBMS-F-007 |
| BBMS-F-009 | Donation automatically updates blood inventory | Pramay Dubey | **Missing** | — | Depends on BBMS-F-007 |
| BBMS-F-010 | Maintain a master list of the 8 blood groups | Pramay Dubey | **Implemented** | `inventory/models.py` (`blood_group` field used with a fixed 8-value list in `views.py`), `requests/models.py:BloodRequest.BloodGroup` (`TextChoices`) | Implemented as a fixed choice list in two places, not one shared source — see Known limitations |
| BBMS-F-011 | Staff view inventory summary by blood group | Pavan E Naik — Blood Inventory Management and Blood Availability Search | **Implemented** | `inventory/views.py:inventory_summary`, `templates/inventory/inventory_summary.html` | Staff-only (`@staff_required`, added Sprint 2 — this view had no role check at all until then) |
| BBMS-F-012 | Search blood availability by blood group | Pavan E Naik | **Implemented** | `inventory/views.py:availability_search`, `templates/inventory/availability_search.html`; tests in `inventory/tests.py` | Requires login, open to any authenticated role |
| BBMS-F-013 | Display available blood units to authenticated users | Pavan E Naik | **Implemented** | Same as F-012 — availability search shows the current count | — |
| BBMS-F-014 | Requester submits a blood request (group, quantity, reason) | Nishit Suresh — Blood Request Management, Blood Issue and Distribution, and Administrative Management | **Implemented** | `requests/forms.py:BloodRequestForm`, `requests/views.py:request_create`, `templates/requests/request_form.html`; tests in `requests/tests.py` | Open to anonymous requesters by design |
| BBMS-F-015 | Requester views their request's status | Nishit Suresh | **Implemented** | `requests/views.py:request_detail`, `templates/requests/request_detail.html` | Looked up by the request's UUID `tracking_id` — see Known limitations |
| BBMS-F-016 | Staff approve/reject a pending request | Nishit Suresh | **Implemented** | `requests/views.py:request_review`, `templates/requests/request_queue.html`; tests in `requests/tests.py` | Rejecting requires a review note |
| BBMS-F-017 | Staff issue blood against an approved request | Nishit Suresh | **Implemented** | `requests/views.py:issue_blood` | Staff-only |
| BBMS-F-018 | Issuing automatically reduces inventory | Nishit Suresh | **Implemented** | `requests/views.py:issue_blood` (atomic `transaction.atomic()` + `select_for_update()`) | Operates on `requests.BloodInventory`, the aggregate model — see Known limitations |
| BBMS-F-019 | Maintain a record of every issue/distribution transaction | Nishit Suresh | **Implemented** | `requests/models.py:BloodIssue` | One `BloodIssue` row per completed issue, with `issued_by` and `issued_at` |
| BBMS-F-020 | Administrator creates/updates/deactivates user accounts | Nishit Suresh | **Missing** | — | No in-application screen; only Django's own `createsuperuser` / admin site |
| BBMS-F-021 | Staff filter/search donor, donation and request records | Nishit Suresh | **Partially implemented** | `donors/views.py:donor_list` (search by username/name/e-mail/blood group) | Donor list search only; no search on donation records (none exist) or on the request queue |
| BBMS-F-022 | Exclude expired units from availability | Nishit Suresh | **Implemented** | `inventory/views.py:availability_search`, `expired_units`; tests in `inventory/tests.py` | — |

## Non-functional requirements

| Req ID | Requirement (abbreviated) | Status | Notes |
|---|---|---|---|
| BBMS-NF-001 | Common page operations (login, search, viewing records) meet a performance target | **Partially verified** | `inventory/performance_test.py` asserts p90 < 3s for login, availability search and inventory summary; not run by default test discovery — see [`TESTING.md`](TESTING.md). No other pages are performance-tested. |
| BBMS-NF-002 | System remains available during normal working hours | **Not verifiable from code** | An operational/deployment commitment, not something the current local-dev-server codebase can demonstrate. |
| BBMS-NF-003 | Consistent, simple screen design | **Implemented** | One shared `templates/base.html` design system used by every page in the project (see [`ARCHITECTURE.md`](ARCHITECTURE.md) §6). |
| BBMS-NF-004 | Codebase organized into clearly separated modules | **Implemented** | Four Django apps, each with one clear responsibility (see [`ARCHITECTURE.md`](ARCHITECTURE.md) §3). |
| BBMS-NF-005 | Blood inventory counts stay consistent with records | **Not fully met** | `requests/views.py:issue_blood`'s deduction is atomic and race-safe within `requests.BloodInventory`, but that model and `inventory.BloodInventory` are never reconciled with each other — see Known limitations. |
| BBMS-NF-006 | Accessible to authorized users from a [compatible environment] | **Implemented, narrowly** | Server-rendered HTML with no JS framework dependency works in any modern browser; no explicit cross-browser or mobile-device testing was performed. |

## Security requirements

| Req ID | Requirement (abbreviated) | SRS owner | Status | Source files | Notes |
|---|---|---|---|---|---|
| BBMS-SR-001 | Require valid username/email + password; unauthenticated requests redirected to login | Nidhi Karkada — Security objectives and authentication-related requirements | **Implemented** | `authentication/decorators.py:staff_required` and every `@login_required`/`@staff_required` view; tests across `authentication/tests/` and `donors/tests.py` | — |
| BBMS-SR-002 | Restrict administrative functions from donor/requester accounts | Pramay Dubey — Role-based access control requirements | **Implemented** | `authentication/decorators.py:staff_required`, applied to `donors.views.donor_list`/`donor_detail`, `inventory.views.inventory_summary`/`expired_units`; `requests.views` uses its own local `user_passes_test(is_staff)` for the same purpose | Both mechanisms reject non-staff; see [`ARCHITECTURE.md`](ARCHITECTURE.md) §3 for the one stylistic inconsistency between them |
| BBMS-SR-003 | HTTPS for all client-server communication | Pavan E Naik — Communication and password-storage security requirements | **Settings present, deployment not configured** | `bloodbank/settings.py` (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS settings — all gated on `DEBUG`) | These are no-ops while `DEBUG=True`; no actual HTTPS-serving deployment (web server, certificate) exists in this repository. These settings were briefly absent from `main` due to a merge issue — see [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md). |
| BBMS-SR-004 | Store passwords using a secure hash | Pavan E Naik | **Implemented** | Django's default password hashing (`django.contrib.auth`), used by both `authentication` login and `donors` registration; tests assert the stored value is not plaintext in both `authentication/tests/test_login.py` and `donors/tests.py` | — |
| BBMS-SR-005 | Audit entry whenever inventory or request status changes | Nishit Suresh — Audit logging requirement and overall security review | **Partially implemented** | `requests/models.py:BloodIssue` (one row per issue transaction, with `issued_by`); `donors/models.py:DonorProfile.set_eligibility` (`eligibility_updated_by`/`_at`) | No audit trail for `request_review` (approve/reject) beyond `reviewed_by`/`reviewed_at` on the request itself, and none for plain inventory edits made via the Django admin |

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
documented here as "Implemented"). Where SRS allocation and actual
authorship diverge, this document states the SRS allocation (as
requested) and notes the divergence here rather than silently rewriting
history.

## Known limitations affecting this matrix

See [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) for full detail. In summary:
two independent `BloodInventory` models that aren't reconciled (affects
BBMS-F-009, F-011, F-018, NF-005); donor eligibility is staff-set rather
than donation-history-derived (BBMS-F-006); Donation Management and
in-app Administrative account management don't exist yet (BBMS-F-007/
008/009/020); the blood group master list (BBMS-F-010) is duplicated as
a fixed choice list in two apps rather than defined once.
