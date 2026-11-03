# End-to-End Integration Test Report

## 1. Scope

This report covers only the end-to-end integration-testing task for the
Blood Bank Management System. Security/authorization testing, defect-log
preparation, retesting evidence, demo videos, commit, and push are outside
this report's scope.

The test exercises the primary operational journey across the Django HTTP
views:

1. A donor registers and reaches their profile.
2. Staff locates the donor and updates eligibility.
3. Staff records a successful donation.
4. The donation credits the unified inventory.
5. An unauthenticated requester submits a blood request.
6. Staff approves the request.
7. Staff issues blood against the approved request.
8. The request is fulfilled, inventory is reduced, the inventory ledger is
   updated, and the expected audit entries are written.

## 2. Test environment

| Item | Value |
|---|---|
| Operating system | Windows |
| Python | 3.13 (project virtual environment) |
| Framework | Django 6.1.1 |
| Database | SQLite, Django test database |
| Test runner | Django built-in test runner |
| HTTP layer | Django test client |
| Test module | `requests/test_end_to_end.py` |

The test uses Django's isolated test database. It does not modify the
development database contents.

## 3. Test implementation

The new test is:

`BloodBankEndToEndWorkflowTests.test_donor_to_blood_issue_workflow`

Source: [requests/test_end_to_end.py](../requests/test_end_to_end.py)

The test uses real URL routes and POST requests rather than calling service
functions directly. It verifies both response behavior and persisted
cross-module state:

- Registration redirects to the authenticated home page.
- Donor profile is created and rendered.
- Staff eligibility update redirects correctly and creates one
  `EligibilityHistory` row.
- Donation recording redirects to the staff donation list.
- A five-unit O+ donation creates one inventory batch with five available
  units.
- Public request submission redirects to its tracking page and starts in
  `Pending review`.
- Staff approval changes the request to `Approved`.
- Staff issue changes the request to `Fulfilled`.
- Issuing two units leaves exactly three units available.
- A `BloodIssue` record is created for two units.
- Two inventory transactions exist for the batch: one receive and one issue.
- The availability page reports the remaining three O+ units.
- Audit entries exist for eligibility change, donation recording, inventory
  increase, request submission, request approval, and blood issue.

## 4. Execution evidence

### Focused end-to-end run

Command:

```powershell
.\.venv\Scripts\python.exe manage.py test requests.test_end_to_end -v 1
```

Result:

```text
Found 1 test(s).
Ran 1 test in 1.261s
OK
```

### Full regression run

Command:

```powershell
.\.venv\Scripts\python.exe manage.py test -v 1
```

Result:

```text
Found 115 test(s).
Ran 115 tests in 99.865s
OK
```

The total increased from the previously documented 114 tests because this
report adds one end-to-end integration test.

### Django consistency checks

Commands:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Results:

```text
System check identified no issues (0 silenced).
No changes detected
```

## 5. Result

**PASS**

The primary donor-to-distribution workflow completed successfully through
the application HTTP layer. The full regression suite also passed with no
new failures, and the Django system/migration consistency checks were clean.

## 6. Boundaries and limitations

- This is an automated Django test-client integration test, not a browser
  automation run.
- It verifies application routing, view handling, database writes, service
  integration, inventory accounting, and audit persistence in an isolated
  test database.
- It does not claim production deployment, network, browser rendering,
  concurrent-load, or external-email integration coverage.
- Security/authorization testing is intentionally not reported here because
  it is a separate requested task.

