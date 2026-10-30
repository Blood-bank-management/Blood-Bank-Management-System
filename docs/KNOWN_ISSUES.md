# Known Issues

Genuine outstanding technical issues, found by inspecting the actual code
and git history in this repository — not a generic checklist. Each entry
states what's wrong, who it affects, where it lives, what fixing it would
take, and who needs to be involved. Nothing here is marked resolved unless
it was actually fixed and verified (if it was fixed, this document says
so and points at the commit).

## §1 — Two independent `BloodInventory` models

**Description.** `inventory/models.py` and `requests/models.py` each
define their own `BloodInventory` model, backed by two separate database
tables, with no foreign key or synchronization between them:

- `inventory.BloodInventory` — one row per received batch: `blood_group`,
  `quantity`, `collection_date`, `expiry_date`. Not unique per blood
  group; a group's total is computed by summing non-expired rows.
- `requests.BloodInventory` — one row per blood group (`blood_group` is
  unique), a single `available_units` integer.

`inventory.views.availability_search` and `inventory_summary` read from
the first. `requests.views.issue_blood`'s atomic deduction writes to the
second. Nothing in the codebase keeps them in sync.

**Impact.** The number a donor or requester sees on the public
availability-search page (`inventory.BloodInventory`) can disagree with
what staff actually have authority to issue against
(`requests.BloodInventory`), because issuing blood only touches the
second table. There is no code path today that would make the two drift
apart in a running system *yet*, only because nothing currently writes to
`inventory.BloodInventory` outside the admin site or `seed_demo_data` —
but that is a coincidence of what's built so far, not a safeguard. Once
Donation Management (BBMS-F-009, "donation automatically updates
inventory") is built, this becomes a real correctness bug unless it's
resolved first, since F-009 has to update *some* `BloodInventory`, and
whichever one it updates will disagree with the other.

**Relevant files/modules.** `inventory/models.py`, `inventory/views.py`,
`requests/models.py`, `requests/views.py:issue_blood`, `requests/admin.py`,
`inventory/admin.py`.

**Suggested resolution.** Pick one model and retire the other.
`requests.BloodInventory`'s aggregate shape (one row per group, an
integer count) is already the one the atomic issue/distribution workflow
is built on, and is the simpler base for Donation Management to add to
(F-009 would call the same pattern `issue_blood` already uses:
`select_for_update()` + `available_units` arithmetic inside
`transaction.atomic()`). Migrate `inventory.views` to read from
`requests.BloodInventory` instead, and either drop
`inventory.BloodInventory` or repurpose it as a donation-batch ledger
(collection date, expiry date, source donation) that rolls up into the
aggregate rather than being queried directly for availability.

**Dependencies on other team members.** This spans two SRS-allocated
modules (Pavan E Naik — Blood Inventory Management; Nishit Suresh — Blood
Request Management, Issue and Distribution) and blocks a third (Pramay
Dubey — Blood Donation Management, BBMS-F-009). Needs agreement from at
least Pavan and Nishit before `inventory.views` is repointed, since both
own tests that currently assert against `inventory.BloodInventory`
directly (`inventory/tests.py`).

## §2 — Blood request tracking link has no ownership check

**Description.** `requests.views.request_detail` looks up a
`BloodRequest` by its UUID `tracking_id` from the URL and renders it to
whoever has the link — no login, no check that the viewer submitted that
request. This is a deliberate design choice, not an oversight: BBMS-F-015
is written for a "Requester/User" role that the SRS does not require to
have an account (a hospital desk may submit a request on a patient's
behalf without registering), so the UUID link is the only thing that
identifies "the person who should be able to see this request."

**Impact.** Anyone who obtains a request's tracking link — by having it
shared with them, by it leaking in a browser history/referrer/log, or (in
principle) by guessing a UUID, which is computationally infeasible but
not impossible — can view that request's requester name, e-mail, hospital
name, quantity, purpose, status, and any staff review note. This is
equivalent to a bearer token: possession of the link is the only
authorization check. It is a materially different pattern from an
ID-based access-control bug on an *authenticated* user's own resource
(which this repository does guard against elsewhere — see
`donors.views.profile`, which never accepts an ID at all), and is closer
to a parcel-tracking number: intentional, but worth naming plainly rather
than leaving implicit.

**Relevant files/modules.** `requests/views.py:request_detail`,
`requests/urls.py`, `requests/templates/requests/request_detail.html`.

**Suggested resolution.** Two options, not mutually exclusive: (a)
document this explicitly as the intended trust model (this document is
step one); (b) if the team wants stronger protection without requiring
every requester to register, add a short-lived, single-use access
token alongside `tracking_id`, or require re-entering the requester's
e-mail address on the tracking page as a second factor before the full
details are shown. Requiring an account for every requester (closing the
gap by authentication rather than obscurity) would be a scope change to
BBMS-F-014/015, not currently planned.

**Dependencies on other team members.** Owned by Nishit Suresh's module
(Blood Request Management). Any fix should be designed together with
whoever is also working on BBMS-F-020 (administrator account management),
since a token/e-mail-reverification approach touches the same "does this
person need an account" question.

## §3 — Donor eligibility has no full audit history, only the latest change

**Description.** `DonorProfile.set_eligibility` (in `donors/models.py`)
overwrites `eligibility_status`, `eligibility_note`,
`eligibility_updated_by` and `eligibility_updated_at` on the same row
every time staff change a donor's eligibility. There is no separate
history table — only the most recent change is ever visible; who changed
it to what, and why, on every *prior* occasion is not stored anywhere.

**Impact.** BBMS-SR-005 ("audit entry whenever inventory or request
status is modified") is satisfied for the *current* state, but a
dispute about an eligibility decision made two changes ago ("who marked
this donor ineligible last month, and why?") cannot be answered from the
database — that information has already been overwritten.

**Relevant files/modules.** `donors/models.py:DonorProfile.set_eligibility`,
`donors/views.py:donor_detail`.

**Suggested resolution.** Add a small `EligibilityChange` (or similarly
named) model with a foreign key to `DonorProfile`, one row per change
(status, note, changed_by, changed_at), and have `set_eligibility` create
a new row in addition to updating the summary fields on `DonorProfile`
(keeping the summary fields is worth it — most reads just want "what is
the status right now," not the full history). The donor-detail template
would then list the history below the current-status section.

**Dependencies on other team members.** Self-contained within the
`donors` app; no cross-team dependency. A reasonable Sprint 3 task on its
own.

## §4 — A merge silently dropped HTTPS settings and three dead template files

**Description.** `0221542` ("Merge pull request #10 from
Blood-bank-management/feature/nidhi-sprint-2") merged the Sprint 2 donor
management branch into `main`. That branch's `bloodbank/settings.py` had
been prepared from a snapshot of the repository taken **before**
`e61fdc6` ("Add HTTPS security settings", by Pavan E Naik) was committed
to `main`. Git's merge resolved the conflict on `settings.py` by taking
the feature branch's version of the file wholesale rather than combining
both sides' independent changes, so `SECURE_SSL_REDIRECT`,
`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` and the HSTS settings
silently disappeared from `main` after the merge, with no conflict marker
or warning — the merge was clean. Separately, the same branch's deletion
of three now-superseded template files (`inventory/templates/base.html`,
`inventory/templates/registration/login.html`,
`requests/templates/requests/base.html`, replaced by the shared
`templates/base.html`) also did not survive the merge; the dead files
were still present on `main` afterward.

**Status: fixed.** Both were found while auditing the repository for this
documentation pass, by diffing the pre-merge commit (`bcdb023`) against
the merge commit (`f40683e`) file by file rather than trusting the merge
result. The HTTPS settings were restored verbatim in `69f409a` and the
three dead template files were deleted in `81a2c80`, both on this branch.
`python manage.py check` and the full test suite (71/71) pass with both
changes applied.

**Impact (of the underlying failure mode, now fixed).** A security
setting can be silently lost in a merge with no error at merge time — the
kind of regression that is easy to miss without diffing the actual
settings file against both parents, since nothing about a clean merge
looks wrong.

**Relevant files/modules.** `bloodbank/settings.py`;
`inventory/templates/base.html`,
`inventory/templates/registration/login.html`,
`requests/templates/requests/base.html` (all now deleted).

**Suggested resolution (to prevent a recurrence, not to fix this instance
again).** When merging a long-lived feature branch that touches
`bloodbank/settings.py`, diff the file against both the merge base and
the current `main` tip before approving the PR — see
[`CONTRIBUTING.md`](../CONTRIBUTING.md) "Reviewing changes." A CI check
that fails if `python manage.py check` or the test suite doesn't pass on
the merge commit itself (not just on the feature branch before merging)
would also have caught this at merge time; no CI is currently configured
in this repository.

**Dependencies on other team members.** None remaining — already fixed.
Worth reading by whoever reviews the next large merge into `main`.

## §5 — HTTPS settings are present but no deployment actually serves HTTPS

**Description.** The settings restored in §4
(`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`,
HSTS) are all gated on `DEBUG`, and `DEBUG` defaults to `True` (see
`.env.example`). They are no-ops in local development, as intended — but
this repository also contains no web server configuration, process
manager setup, or deployment target of any kind that would actually serve
the application over HTTPS in the first place.

**Impact.** BBMS-SR-003 ("HTTPS for all communication") cannot be fully
satisfied by application code alone; it also requires a deployment
environment (a reverse proxy or PaaS terminating TLS) that doesn't exist
in this project yet. Running `DEBUG=False` without such a deployment
would not add HTTPS — it would just turn on settings that assume HTTPS is
already there (e.g. `SECURE_SSL_REDIRECT` would redirect to an HTTPS URL
nothing is listening on).

**Relevant files/modules.** `bloodbank/settings.py`; no deployment
configuration files exist to list.

**Suggested resolution.** Out of scope for this documentation pass and
for any single teammate's module — this is a team/deployment-owner
decision: pick a hosting target (e.g. a PaaS with managed TLS, or a VPS
with a reverse proxy and a certificate), add the relevant deployment
configuration, and only then is flipping `DEBUG=False` in that
environment meaningful.

**Dependencies on other team members.** Whoever owns deployment/hosting
for the submitted project — not assigned in the SRS's Division of Work,
since deployment isn't an SRS functional requirement.

## §6 — Missing functionality (Donation Management, Administrative account management)

**Description.** Two SRS-allocated areas have no implementation at all in
this repository:

- **Donation Management (BBMS-F-007, F-008, F-009)** — Pramay Dubey's
  module. No model, view, form, template or URL for recording a
  donation, viewing a donor's donation history, or auto-updating
  inventory from a donation exists anywhere in the codebase.
- **In-app Administrator account management (BBMS-F-020)** — Nishit
  Suresh's module. There is no screen in the application for creating,
  updating or deactivating user accounts; the only way to do so today is
  Django's own `createsuperuser` management command or the `/admin/`
  site directly.

**Impact.** These SRS requirements are unmet by application-specific code
("use the framework's admin site" is not the same as a tailored
BBMS-F-020 screen, e.g. one that respects the project's own role model
rather than Django's generic user-permission UI). BBMS-F-006 (donor
eligibility) and BBMS-F-009 (inventory auto-update from a donation) both
depend on BBMS-F-007 existing — see
[`REQUIREMENTS_TRACEABILITY.md`](REQUIREMENTS_TRACEABILITY.md).

**Relevant files/modules.** None exist for Donation Management. For
Administrative management: `django.contrib.admin` only (no app-specific
code).

**Suggested resolution.** Build each as its own Sprint-3 task, by the
teammate the SRS already assigns it to. Donation Management should follow
the same pattern `requests.views.issue_blood` establishes (atomic
inventory update under `select_for_update()`) once §1 is resolved, so it
only has one `BloodInventory` model to update rather than needing to
decide which.

**Dependencies on other team members.** Pramay Dubey (Donation
Management) and Nishit Suresh (Administrative management), per the SRS's
own Division of Work.

## §7 — A real test file is silently skipped by default test discovery

**Description.** `inventory/performance_test.py` contains a real,
currently-passing test (`AuthenticatedPagePerformanceTests`). Django's
default test runner only imports files matching `test*.py`;
`performance_test.py` does not match, so `python manage.py test` silently
never runs it. This is how a genuine bug in that file (a `reverse("login")`
call using a URL name that doesn't exist) went unnoticed for a full
sprint — see `SPRINT2_REPORT.md` §D — before being found and fixed in
Sprint 2.

**Impact.** Anyone running `python manage.py test` and seeing "71/71
pass" would reasonably assume the full test suite ran; the performance
smoke test for BBMS-NF-001/BBMS-53 did not, unless they already know to
run it separately (now documented in [`TESTING.md`](TESTING.md) and the
README).

**Relevant files/modules.** `inventory/performance_test.py`.

**Suggested resolution.** Rename the file to `test_performance.py` so
default discovery picks it up. Deliberately not done as part of this
documentation pass — it's a one-line rename but touches a file inside
`inventory`, outside the scope of what this pass otherwise changes, and
is left for Pavan E Naik (or whoever owns `inventory`) to make along with
updating anywhere else in the team's own notes that references the old
filename.

**Dependencies on other team members.** Pavan E Naik (Blood Inventory
Management module owner).
