# Defect Log and Retesting Evidence

## 1. Scope

This report covers defect tracking and retesting evidence for the Blood Bank
Management System. It consolidates the defects already recorded in
[DEFECT_LOG.md](./DEFECT_LOG.md) and records the latest regression evidence.

No commit or push was performed.

## 2. Defect summary

| ID | Severity | Defect | Status | Retest result |
|---|---|---|---|---|
| DEFECT-01 | High | Administrative user-management URLs were shadowed by Django's `/admin/` route and returned 404 | Fixed | Accounts tests passed; administrative routes are reachable |
| DEFECT-02 | Low | Hand-written migrations differed from model definitions and caused pending migration changes | Fixed | `makemigrations --check --dry-run` returned `No changes detected` |
| DEFECT-03 | Low | Two last-active-superuser tests asserted messages on the redirect response instead of the followed page | Fixed | Accounts tests passed after using `follow=True` |
| DEFECT-04 | High | Demo seed command imported the removed duplicate inventory model | Fixed | Seed workflow was run twice; the second run created no duplicate records |

**Current defect status:**

- Confirmed defects: 4
- Fixed and retested: 4
- Reopened: 0
- Outstanding: 0

DEFECT-03 was a test-authoring defect rather than an application defect. The
other three defects affected application availability, migration correctness,
or demo readiness.

## 3. Retesting performed in the current verification run

### Regression test command

```powershell
.\.venv\Scripts\python.exe manage.py test authentication donors donations inventory requests auditlog accounts -v 1
```

Result:

```text
Found 115 test(s).
Ran 115 tests in 97.697s
OK
```

This run includes the authentication, donor, donation, inventory, request,
audit-log, and account tests that cover the affected areas of DEFECT-01,
DEFECT-03, and the related authorization and workflow behavior. It also
includes the end-to-end integration test added for the primary donor-to-issue
workflow.

### Django system check

```powershell
.\.venv\Scripts\python.exe manage.py check
```

Result:

```text
System check identified no issues (0 silenced).
```

### Migration consistency check

```powershell
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Result:

```text
No changes detected
```

This directly retests the condition that exposed DEFECT-02.

### Demo seed retest evidence

The seed command was previously retested against a fresh database as
documented in [DEFECT_LOG.md](./DEFECT_LOG.md), DEFECT-04:

1. The first run completed and created the demo users, inventory, donations,
   requests, issue, and audit entries.
2. The command was run a second time against the same database.
3. The second run created no additional records.

This confirms both that the removed-model import was fixed and that the
command is idempotent.

## 4. Defect-by-defect retest evidence

### DEFECT-01 — Administrative URLs returned 404

- **Fix:** moved the application user-management routes from the conflicting
  `/admin/users/` prefix to `/administration/users/`.
- **Retest:** account-management tests passed in the current 115-test run.
- **Result:** **PASS — fixed; not reproduced.**

### DEFECT-02 — Migration state drift

- **Fix:** generated follow-up migrations matching the current model
  definitions.
- **Retest:** `manage.py makemigrations --check --dry-run`.
- **Result:** **PASS — `No changes detected`; not reproduced.**

### DEFECT-03 — Incorrect test assertion for redirect message

- **Fix:** changed the affected tests to follow the redirect before checking
  the rendered message.
- **Retest:** account-management tests passed in the current 115-test run.
- **Result:** **PASS — fixed; not reproduced.**

### DEFECT-04 — Demo seed command imported removed model

- **Fix:** rewrote demo seeding to use the unified inventory and donation
  service layer.
- **Retest:** executed the seed command twice on the same fresh database and
  verified stable row counts.
- **Result:** **PASS — fixed and idempotent; not reproduced.**

## 5. Conclusion

**PASS — all recorded defects have been fixed and retested.**

The current regression run passed all 115 tests, Django system checks passed,
and migration state is clean. No defect was reopened and no outstanding
defect was identified in this retesting cycle.

## 6. Testing limitations

- The seed-command evidence is a previously recorded execution in the
  repository's existing defect log; it was not rerun in this verification
  cycle to avoid altering the local development database.
- The evidence is automated Django test and management-command evidence, not
  a browser-based exploratory retest or a production deployment test.
- Performance, penetration testing, and dependency scanning are outside this
  report's scope.

