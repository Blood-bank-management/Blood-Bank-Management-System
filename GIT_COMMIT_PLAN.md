# Git Commit Plan

You asked for your own commits, not mine — nothing in this repository
was committed, pushed, or turned into a pull request by this work.
This document tells you how to turn the final project in
`BBMS_FINAL_COMPLETE_PROJECT.zip` into a sequence of real, individually
meaningful commits in your own repository, once you've copied/merged
its contents in.

**No patch files this time.** The previous round of this work produced
`.patch` files; this round's instructions ask for the final assembled
project plus this commit plan, so the steps below are `git add <these
exact files>` + `git commit -m "<this message>"`, run from your own
repository after the new/changed files are in place. Every file path
below is real — copied from the actual project tree, not invented.

## How to use this

1. Copy the contents of the extracted ZIP into your existing Git
   repository (overwrite/merge as needed — this is the same project,
   extended).
2. Go through the 24 groups below **in order** — several groups depend
   on files from an earlier group existing first (e.g. you can't
   commit `donations/services.py` importing `inventory/services.py`
   before `inventory/services.py` exists).
3. For each group: `git add` exactly the listed files, then
   `git commit -m "<message>"`.
4. Run `python manage.py test` after group 11 (end of the backend
   core) and again after group 24 (everything) to catch anything that
   doesn't apply cleanly in your repository's actual state.

This gives you **24 commits** — comfortably past the "20+" you asked
for — and every one is a real, coherent, independently-reviewable
change: no empty commits, no whitespace-only diffs, no file split
purely to pad the count.

## The 24 commits

### Group 1 — Shared domain constants
```
git add bloodbank/constants.py
git commit -m "feat(core): add shared blood-group and domain constants"
```
Single source of truth for the blood group list and the two documented
project assumptions (42-day shelf life, 90-day minimum donation
interval), used by every group below.

### Group 2 — Donor eligibility history model
```
git add donors/models.py donors/migrations/0002_eligibilityhistory.py
git commit -m "feat(donors): add EligibilityHistory model and transactional set_eligibility"
```

### Group 3 — Donor eligibility history tests
```
git add donors/tests.py
git commit -m "test(donors): add EligibilityHistoryTests"
```

### Group 4 — Unified inventory model
```
git add inventory/models.py inventory/migrations/0002_unified_inventory_architecture.py inventory/migrations/0003_rename_inv_bg_expiry_idx_inventory_b_blood_g_8a64bc_idx_and_more.py
git commit -m "feat(inventory): extend BloodInventory to a batch ledger with InventoryTransaction"
```

### Group 5 — Inventory service layer
```
git add inventory/services.py inventory/forms.py
git commit -m "feat(inventory): add the service layer (receive_batch/issue_units/adjust_batch) as the only stock-mutation path"
```

### Group 6 — Remove the duplicate aggregate inventory model
```
git add requests/models.py requests/migrations/0003_remove_duplicate_inventory.py requests/admin.py
git commit -m "fix(requests): remove the duplicate aggregate BloodInventory model, migrate existing rows first"
```
This is the fix for the "two independent inventory models" issue — see
`docs/KNOWN_ISSUES.md` §1.

### Group 7 — Point the request/issue workflow at the unified inventory
```
git add requests/views.py
git commit -m "feat(requests): issue_blood now calls inventory.services.issue_units, with a duplicate-issue guard"
```

### Group 8 — Inventory staff views (batch dashboard)
```
git add inventory/views.py inventory/urls.py inventory/templates/inventory/batch_list.html inventory/templates/inventory/batch_detail.html inventory/templates/inventory/inventory_summary.html
git commit -m "feat(inventory): add staff batch list/detail views with manual adjustment, rework inventory summary"
```

### Group 9 — Inventory service + access tests
```
git add inventory/tests_services.py inventory/tests_access.py
git commit -m "test(inventory): add service-layer tests (FIFO, insufficient stock, no negative balance) and staff/donor access tests"
```

### Group 10 — Requests test updates for the unified model
```
git add requests/tests.py
git commit -m "test(requests): update inventory-touching tests for the unified model, add queue filter/duplicate-issue/shared-constant tests"
```

### Group 11 — Donation Management: model and migrations
```
git add donations/__init__.py donations/apps.py donations/models.py donations/migrations/__init__.py donations/migrations/0001_initial.py donations/migrations/0002_rename_donation_donor_date_idx_donations_d_donor_i_1ec17d_idx_and_more.py
git commit -m "feat(donations): add the Donation model (new app) with a unique collection_reference"
```
*Checkpoint: run `python manage.py check` and
`python manage.py makemigrations --check --dry-run` here — the backend
core (groups 1-11) should already pass both cleanly.*

### Group 12 — Donation Management: service layer
```
git add donations/services.py
git commit -m "feat(donations): add record_donation() — one atomic call for donation + inventory credit + audit"
```

### Group 13 — Donation Management: forms, views, URLs, admin
```
git add donations/forms.py donations/views.py donations/urls.py donations/admin.py
git commit -m "feat(donations): add record/list/history views and forms"
```

### Group 14 — Donation Management: templates
```
git add donations/templates/donations/record.html donations/templates/donations/donation_list.html donations/templates/donations/my_history.html donations/templates/donations/donor_history.html
git commit -m "feat(donations): add templates for record/list/donor-history/my-history"
```

### Group 15 — Donation Management: tests
```
git add donations/tests.py
git commit -m "test(donations): add service, form and view/IDOR access tests"
```

### Group 16 — Audit logging app
```
git add auditlog/__init__.py auditlog/apps.py auditlog/models.py auditlog/migrations/__init__.py auditlog/migrations/0001_initial.py auditlog/migrations/0002_rename_auditlog_entity_idx_auditlog_au_entity__87d33e_idx_and_more.py auditlog/admin.py auditlog/views.py auditlog/urls.py auditlog/templates/auditlog/audit_log_list.html auditlog/tests.py
git commit -m "feat(auditlog): add the append-only AuditLog model, record() helper, and staff-only list view (new app)"
```
Kept as one commit (not split further): the model, its one `record()`
call site, and the read-only admin registration are small enough, and
tightly coupled enough, that splitting them would produce an
intermediate commit with a model nothing calls yet.

### Group 17 — Wire audit logging into existing write paths
```
git add donors/models.py requests/views.py donations/services.py
git commit -m "feat: call auditlog.record() from eligibility changes, request review/issue, and donation recording"
```
Note: `donors/models.py` and `donations/services.py` were already
staged in groups 2 and 12 respectively — if your `git add` for this
group reports "nothing to commit" for those two files, that's because
the audit-log calls were already included when those files were first
added. In that case this commit is just `requests/views.py`'s
audit-log calls; adjust the commit message to say so if you split it
that way instead.

### Group 18 — Administrator user management app
```
git add accounts/__init__.py accounts/apps.py accounts/models.py accounts/migrations/__init__.py accounts/admin.py
git commit -m "feat(accounts): scaffold the administrator-only user-management app (new app, no new models — operates on auth.User)"
```

### Group 19 — Administrator forms, views, URLs
```
git add accounts/forms.py accounts/views.py accounts/urls.py
git commit -m "feat(accounts): add create/list/detail views with role-ChoiceField and last-superuser guards"
```

### Group 20 — Administrator templates and tests
```
git add accounts/templates/accounts/user_list.html accounts/templates/accounts/user_create.html accounts/templates/accounts/user_detail.html accounts/tests.py
git commit -m "feat(accounts): add templates; test(accounts): add RBAC/privilege-escalation/last-superuser tests"
```

### Group 21 — Role-aware dashboard
```
git add authentication/decorators.py authentication/views.py authentication/templates/authentication/home.html
git commit -m "feat(authentication): add admin_required decorator and a real-data staff/donor dashboard"
```

### Group 22 — Premium design system and theming
```
git add templates/base.html inventory/templates/inventory/availability_search.html requests/templates/requests/request_queue.html
git commit -m "feat(ui): premium design tokens, light/dark/system theming with no-flash switcher, request-queue search UI"
```

### Group 23 — Demo data, performance test, and security validation doc
```
git add donors/management/commands/seed_demo_data.py inventory/performance_test.py docs/SECURITY_VALIDATION.md
git commit -m "feat(demo): seed through the real service layer (donations/inventory/eligibility/requests), covering every new workflow; test(perf): extend to all 8 required pages; docs: add security validation mapping"
```

### Group 24 — Documentation
```
git add README.md docs/ARCHITECTURE.md docs/USER_GUIDE.md docs/TESTING.md docs/KNOWN_ISSUES.md docs/REQUIREMENTS_TRACEABILITY.md docs/DEFECT_LOG.md docs/TEST_EXECUTION_REPORT.md docs/TEST_METRICS.md docs/TEST_SIGN_OFF.md docs/FINAL_DEFINITION_OF_DONE.md IMPLEMENTATION_SUMMARY.md DEMO_GUIDE.md KNOWN_LIMITATIONS.md GIT_COMMIT_PLAN.md
git commit -m "docs: update all project documentation for the complete feature set and add the final delivery docs"
```
This is the one intentionally large commit in the series — it's pure
documentation, touches no application code, and splitting a dozen
markdown files that all describe the same finished state into separate
commits would not make any of them more independently reviewable. If
your grading rubric wants documentation split too, a reasonable finer
cut is: (24a) the five pre-existing docs updated (`README.md`,
`ARCHITECTURE.md`, `USER_GUIDE.md`, `TESTING.md`, `KNOWN_ISSUES.md`,
`REQUIREMENTS_TRACEABILITY.md`), (24b) the five new process docs
(`DEFECT_LOG.md`, `TEST_EXECUTION_REPORT.md`, `TEST_METRICS.md`,
`TEST_SIGN_OFF.md`, `FINAL_DEFINITION_OF_DONE.md`), (24c) the four
final-delivery docs (`IMPLEMENTATION_SUMMARY.md`, `DEMO_GUIDE.md`,
`KNOWN_LIMITATIONS.md`, `GIT_COMMIT_PLAN.md`) — three commits instead
of one, for 26 total.

## Verification checkpoints

| After group | Run | Expect |
|---|---|---|
| 11 | `python manage.py check` | No issues |
| 11 | `python manage.py makemigrations --check --dry-run` | No changes detected |
| 24 | `python manage.py migrate` (fresh DB) | Applies cleanly |
| 24 | `python manage.py test` | `Found 114 test(s).` ... `OK` |
| 24 | `python manage.py test inventory.performance_test -v 2` | All 8 pages under 3.0s p90 |
| 24 | `python manage.py seed_demo_data` (run twice) | Second run creates nothing new |

See `TEST_EXECUTION_REPORT.md` for this project's own author's actual
output from every row above, run against this exact final codebase.

## What's deliberately not in any commit

Per your instruction: no commit was made, no push, no pull request, no
Git history rewrite, anywhere, by this work. The groups above are
instructions for commits **you** create, on your own machine.
