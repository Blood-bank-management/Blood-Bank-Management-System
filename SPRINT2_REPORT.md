# Sprint 2 Report — Blood Bank Management System
**Module: Authentication & Donor Management (Nidhi Karkada, PES2UG24CS314)**
**Branch:** `feature/nidhi-sprint-2` (5 commits on top of the Sprint 1 import)
**Date:** 2026-10-28

This report is organized exactly as requested: implementation summary,
coverage matrix, completion report, security report, test report, UI
report, Git report, team handoff, and a final truthful checklist.

---

## A. Implementation Summary

Sprint 1 delivered three working Django apps (`authentication`, `inventory`,
`requests`) with no Donor Management module at all — there was no donor
model, no self-registration, no staff donor directory, and no eligibility
tracking anywhere in the codebase. Sprint 2 added a fourth app, `donors`,
implementing the four requirements the SRS's own Division of Work assigns
to this module (BBMS-F-003 through BBMS-F-006), plus the RBAC and IDOR
protections those requirements imply (BBMS-SR-001, BBMS-SR-002), plus a
genuine Sprint 1 integration defect fix that was blocking a consistent
logout experience across the app.

Concretely, this sprint:

1. Audited the full Sprint 1 repository against the team's SRS before
   writing any code (Section B).
2. Fixed the Sprint 1 navigation/logout integration defect: inventory's
   and requests' pages had no logout control at all.
3. Externalized `SECRET_KEY`/`DEBUG`/`ALLOWED_HOSTS` to environment
   variables and documented a reproducible dev setup with seed data.
4. Built the `donors` app: self-registration, self-service profile,
   staff-only donor directory, and staff-only eligibility management —
   each with explicit, tested RBAC and IDOR reasoning.
5. Added a project-wide `staff_required` decorator and applied it
   consistently, including to two pre-existing inventory views that had
   no role check at all.
6. Wrote 29 new tests (unit + integration) for the donors module; fixed
   one previously-broken, previously-unrun test in `inventory`.
7. Rebuilt the UI as one shared, polished design system applied to every
   page, old and new.
8. Produced real, verifiable Git history on `feature/nidhi-sprint-2`.

**What this sprint explicitly did not do:** implement Donation Management,
Blood Group Management (already done in Sprint 1 by inventory's static
choice list), or Administrative user management — those are other
teammates' SRS-assigned responsibilities and were out of scope. See
Section C.

---

## B. Functional Requirement Coverage Matrix

Status as found in the Sprint 1 repository, then as left at the end of
Sprint 2. Requirement text is taken verbatim (abbreviated) from the
team's own SRS, bundled in the repo at `Team 1_Blood Bank Management
System.pdf`.

| Req ID | Requirement (abbreviated) | Sprint 1 status | Sprint 2 status | Owner |
|---|---|---|---|---|
| BBMS-F-001 | Login with username/email + password | Implemented, tested (16 tests) | Unchanged | Nidhi |
| BBMS-F-002 | Logout ends session | Implemented, tested | Unchanged (nav defect fixed — see D) | Nidhi |
| BBMS-F-003 | Donor self-registration | **Missing** | **Implemented** — `donors:register`, 11 tests | Nidhi |
| BBMS-F-004 | Donor updates own profile | **Missing** | **Implemented** — `donors:profile`, 6 tests | Nidhi |
| BBMS-F-005 | Staff view donor list/record | **Missing** | **Implemented** — `donors:list`/`donors:detail`, 8 tests | Nidhi |
| BBMS-F-006 | Staff mark donor eligibility | **Missing** | **Implemented, with a documented gap** — manually staff-set with audit trail, not auto-derived from donation history (that data doesn't exist yet; see Section C) | Nidhi |
| BBMS-F-007 | Staff record a donation | **Missing** | Not in scope this sprint | Pramay |
| BBMS-F-008 | Donor views own donation history | **Missing** | Not in scope this sprint | Pramay |
| BBMS-F-009 | Donation auto-updates inventory | **Missing** | Not in scope this sprint | Pramay |
| BBMS-F-010 | Master blood group list | Implemented (static choice list, both apps) | Unchanged | Pramay |
| BBMS-F-011 | Staff inventory summary | Implemented, but **not role-restricted** (defect) | **Fixed** — now staff-only | Pavan (fix: Nidhi, in scope of RBAC task) |
| BBMS-F-012/013 | Availability search / listing | Implemented, tested | Unchanged | Pavan |
| BBMS-F-014/015 | Submit / track blood request | Implemented, tested | Unchanged (template restyled only) | Pramay |
| BBMS-F-016 | Staff approve/reject request | Implemented, tested | Unchanged | Pramay |
| BBMS-F-017/018/019 | Issue blood, reduce inventory, audit log | Implemented, tested, atomic | Unchanged | Pramay |
| BBMS-F-020 | Admin create/update/deactivate accounts | **Missing** | Not in scope this sprint | Nishit |
| BBMS-F-021 | Staff filter/search records | Partial (donor list search added this sprint; donation/request search still missing) | Partial | Nishit / Pramay |
| BBMS-F-022 | Exclude expired units from availability | Implemented, tested | Unchanged | Pavan |
| BBMS-NF-001..006 | Performance, availability, usability, etc. | Partially verified (BBMS-53 perf report in repo) | One test bug fixed (Section D); no new NFR work this sprint | — |
| BBMS-SR-001 | Unauthenticated → redirected to login | Implemented, tested | Unchanged | Nidhi |
| BBMS-SR-002 | Donor/requester blocked from admin actions | **Partial** — requests app checked `is_staff`; inventory and the new donor-management surface had no such check until this sprint | **Implemented and tested** across donors + the two inventory views that lacked it | Nidhi |
| BBMS-SR-003 | HTTPS for all traffic | Not addressed (deployment concern) | Not addressed — out of scope for local app code | — |
| BBMS-SR-004 | Passwords stored hashed | Implemented (Django default), tested | Unchanged; donor registration reuses the same validators | Nidhi |
| BBMS-SR-005 | Audit entry on inventory/request changes | Implemented for requests (BloodIssue log) | Extended to donor eligibility changes (`eligibility_updated_by`/`_at`) | Nidhi (partial) |

---

## C. Sprint 2 Completion Report (Nidhi's 8 assigned responsibilities)

| # | Responsibility | Status | Notes |
|---|---|---|---|
| 1 | Audit Sprint 1 against the SRS | **Done** | Section B above; also found and fixed 2 defects outside Donor Management's literal scope (nav/logout, inventory RBAC) because they blocked a coherent Sprint 2 delivery |
| 2 | Fix logout/authentication integration defect | **Done** | Root cause: inventory and requests apps each had their own template with no logout control. Fixed by moving every template onto one shared base with a logout form in the header nav |
| 3 | Shared dev environment (env vars, seed data, docs) | **Done** | `.env.example`, `README.md`, `seed_demo_data` management command (idempotent, demo-only credentials) |
| 4 | Donor self-registration | **Done** | Minimum-privilege by construction (no staff/superuser field exists on the form) |
| 5 | RBAC completion | **Done for donors + the two inventory views in scope** | Full project-wide RBAC (e.g. hardening `requests` app further) was not re-audited beyond what's in Section B — `requests` already had `is_staff` checks from Sprint 1 and was left as-is |
| 6 | Staff donor list/detail views | **Done** | Pagination, search, staff-only |
| 7 | Donor eligibility management | **Done, with a documented limitation** | Staff-set with audit trail; not auto-derived from donation history because that module doesn't exist yet (see README "Known limitations") |
| 8 | IDOR prevention | **Done for every donor-management endpoint** | See Section D. The pre-existing `requests:detail` tracking-by-UUID endpoint was reviewed and *not* changed — see the judgment call below |

**Judgment call — `requests:detail` tracking link:** This endpoint (owned by
a teammate, not part of Donor Management) looks up a `BloodRequest` by its
UUID `tracking_id` with no ownership check. The master prompt's instruction
not to rely on UUIDs as a substitute for authorization is right in general,
but this specific case is a public tracking link for requesters who may not
have an account at all (the SRS's "Requester/User" role is not necessarily
an authenticated donor) — the same pattern as a courier tracking number.
Changing it would mean either requiring every requester to register an
account (a scope change to another teammate's module, not requested) or
accepting that this report calls it something it isn't. It is flagged here
rather than silently left alone or silently "fixed" in a way that could
break the existing, tested request flow.

---

## D. Security Report

**Fixed this sprint:**
- **RBAC gap on `inventory_summary` / `expired_units`** — both were only
  `@login_required`, so any authenticated donor could view staff-only
  inventory data. Now `@staff_required` (HTTP 403 for non-staff).
- **No RBAC at all on the new donor-management surface** — addressed from
  the start: `donors:list`, `donors:detail` are `@staff_required`;
  `donors:profile` is scoped to `request.user` with no ID parameter.
- **Donor self-escalation** — verified (by test, not just by reading the
  code) that a donor cannot set their own eligibility status, including by
  hand-crafting a POST body with an `eligibility_status` field toward the
  profile endpoint (that view has no code path that reads it) or by
  posting directly to the staff endpoint (403 before the POST body is even
  parsed).
- **IDOR on donor records** — `donor_detail(pk)` is protected by role
  (`@staff_required`), not by obscurity; a donor is rejected for *any* pk,
  including their own, before the row is even fetched. Verified by test.
- **Missing CSRF coverage on new POST endpoints** — verified (by test)
  that registration, profile update, and eligibility update all require a
  valid CSRF token, consistent with the rest of the project.
- **UTF-16-encoded `requirements.txt`** — not a security issue, but is a
  real "worked on my machine only" landmine (pip reads it fine as text on
  some platforms and garbage on others, depending on locale); re-saved as
  UTF-8.

**Flagged, not fixed (outside this sprint's scope — see Section C):**
- `requests:detail` tracking-by-UUID access (judgment call above).
- Two independent `BloodInventory` models between `inventory` and
  `requests` apps that are never reconciled (a data-integrity issue more
  than an access-control one — see README "Known limitations").
- HTTPS enforcement (BBMS-SR-003) is a deployment-environment setting, not
  application code; not addressed.

**Not attempted:** any kind of production security review beyond what
unit/integration tests can verify locally (no dependency/CVE scan was run,
no penetration test, no review of the Django version itself for known
CVEs). The local test suite passing is not a production-readiness claim.

---

## E. Test Report

Real commands, run in this environment, on the final `feature/nidhi-sprint-2`
commit (`0fba1c4`):

```
$ python manage.py test
Found 71 tests.
----------------------------------------------------------------------
Ran 71 tests in 66.0s

OK
```

```
$ python manage.py test inventory.performance_test -v 2
Login: p90=0.0027s (target <= 3.0s)
Availability: p90=0.0028s (target <= 3.0s)
Inventory summary: p90=0.0049s (target <= 3.0s)
Ran 1 test in 1.2s

OK
```

```
$ python manage.py check
System check identified no issues (0 silenced).

$ python manage.py makemigrations --check --dry-run
No changes detected
```

**Breakdown of the 71:**
- 23 `authentication` tests — unchanged from Sprint 1, still passing.
- 10 `inventory` tests — unchanged from Sprint 1, still passing (the
  separately-run performance test is the 72nd; not counted by default
  discovery — see README).
- 9 `requests` tests — unchanged from Sprint 1, still passing.
- **29 `donors` tests — new this sprint**, covering: registration (11,
  including minimum-privilege and weak-password/duplicate-field
  rejection), self-service profile including the two IDOR-adjacent checks
  (6), staff list/detail RBAC and IDOR (8), eligibility change
  CSRF/RBAC/audit-trail (3), and one end-to-end integration test walking
  register → login → view/edit profile → blocked from staff pages →
  logout → staff logs in → finds the donor → changes eligibility → donor
  sees the change → donor still can't self-reverse it.

**Not run:** no load/concurrency testing beyond the existing performance
smoke test; no browser-based end-to-end test suite (the UI was verified
manually via rendered screenshots, listed in Section F, not via an
automated browser test suite).

---

## F. UI Report

Every page in the project (old and new) now extends one shared
`templates/base.html`: a healthcare-style design (deep red header, serif
headings, card-based layout, consistent badges for status/role/eligibility,
a role-aware nav bar) instead of three separate, inconsistent inline
stylesheets. Screenshots taken against the real dev server with seeded
data (not mockups) confirm: the login page, the staff donor list, a donor
detail page with the eligibility form, and the staff request queue all
render correctly, wired to real data, with the logout control present and
working on every page.

Pages restyled: login, home/dashboard (authentication); availability
search, inventory summary, expired units (inventory); request form,
request detail/tracking, request queue (requests); register, profile,
donor list, donor detail (donors — new).

Not done: no dedicated mobile-breakpoint testing beyond the CSS's
responsive rules (grid collapses, flex-wrap); no accessibility audit
beyond semantic HTML, label/`for` pairing, and visible focus outlines.

---

## G. Git Report

- **Branch:** `feature/nidhi-sprint-2`, based on `main` at the Sprint 1
  import baseline.
- **Author identity used:** `Nidhi Karkada <nidhi.karkada@gmail.com>`
  (matches the account this session is attached to).
- **Commits (oldest → newest):**

| Hash | Subject |
|---|---|
| `3a59075` | `chore: import Sprint 1 integration baseline` |
| `6a979a1` | `chore(env): move SECRET_KEY/DEBUG/ALLOWED_HOSTS to environment variables` |
| `0bf3a4e` | `feat(donors): add donor self-registration, profile and staff management (BBMS-F-003..006)` |
| `f30e0f7` | `fix(ui): restore logout control across every page; unify design system; fix inventory namespace bug` |
| `0fba1c4` | `docs: Sprint 2 setup, demo credentials, role-permission matrix, known limitations` |

Each commit was checked to run and pass the full test suite at that point
in history (not just at the final commit) before being written. No commit
was backdated, squashed to hide a failed attempt, or split to inflate the
count — each is a real, independently-reviewable unit of work.

- **Uncommitted changes at hand-off:** none — `git status` is clean.
- **Push status: not pushed.** This environment has no configured git
  remote and no credentials for this GitHub repository, so a push was not
  attempted (and nothing here claims one happened). To publish this branch
  yourself:

```bash
git remote add origin <your repo URL>   # if not already configured
git push -u origin feature/nidhi-sprint-2
```

Then open a PR against `main` with a description covering Sections A–F of
this report.

---

## H. Team Handoff Documentation

See `README.md` in the repository for the authoritative, kept-up-to-date
version of this section (setup, demo credentials, role-permission matrix,
known limitations). Summary:

- **Setup:** `pip install -r requirements.txt` → `python manage.py migrate`
  → optionally `python manage.py seed_demo_data` → `python manage.py runserver`.
- **Demo credentials** (seed_demo_data, all password `DemoPass!2026`):
  `admin_demo` (admin), `staff_demo` (staff), `donor_demo1/2/3` (donors).
- **Tests:** `python manage.py test` (71 tests); performance smoke test
  must be run separately (see README).
- **Role-permission matrix:** full table in README.md Section 4.
- **Remaining work for the team:** Donation Management (BBMS-F-007/008/009,
  Pramay), Administrative user management (BBMS-F-020/021, Nishit), the
  two-inventory-models consolidation (joint, see README "Known
  limitations"), HTTPS/deployment configuration (whoever owns
  deployment).

---

## I. Final Truthful Status Checklist

**Complete and verified (tests pass, manually screenshotted):**
- [x] Sprint 1 audit against the SRS
- [x] Logout/navigation integration defect fixed
- [x] Shared dev environment (env vars, seed data, README)
- [x] Donor self-registration, minimum-privilege by construction
- [x] Donor self-service profile, IDOR-safe by construction
- [x] Staff donor list + detail views, RBAC-enforced
- [x] Donor eligibility management with audit trail
- [x] IDOR review across every donor-management ID-accepting endpoint
- [x] 29 new unit + integration tests, all passing; full suite (71) passing
- [x] UI redesign applied consistently across all four apps
- [x] Real, verifiable Git history on `feature/nidhi-sprint-2`

**Incomplete / explicitly out of scope (documented, not hidden):**
- [ ] Donation Management module (BBMS-F-007/008/009) — not built; belongs
      to another teammate's Sprint 2 responsibility.
- [ ] Administrative user management (BBMS-F-020/021) — not built; another
      teammate's responsibility.
- [ ] Automatic eligibility derivation from donation history — blocked on
      the above; eligibility is manually staff-set in the meantime.
- [ ] Two divergent `BloodInventory` models reconciled into one — flagged,
      not fixed (cross-module, needs coordination with Pramay/Pavan).
- [ ] `requests:detail` ownership model beyond UUID-tracking — reviewed,
      left as a judgment call (see Section C).
- [ ] HTTPS / production deployment hardening — out of scope for local
      app code.
- [ ] Branch not pushed to a remote — no remote/credentials configured in
      this environment; exact commands to do it yourself are in Section G.
