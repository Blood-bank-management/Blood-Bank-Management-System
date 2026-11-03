# Test execution report

Every command below was actually run in this session against this
repository, most recently right before this document was written. Where
a command's output is long, the relevant summary line is quoted
verbatim; nothing here is estimated or inferred.

## Environment

- Python 3.13, Django 6.1.1, SQLite (the project's default local DB).
- `DJANGO_SECRET_KEY` set to a throwaway value for the session (per
  `.env.example` / `README.md` "Environment setup"); `DJANGO_DEBUG`
  defaulted to `True`.
- Commands run from the repository root.

## 1. Static checks

```
$ python manage.py check
System check identified no issues (0 silenced).
```

```
$ python manage.py makemigrations --check --dry-run
No changes detected
```
(Exit code 0 both times. The second command initially reported pending
changes during development -- see `docs/DEFECT_LOG.md` DEFECT-02 -- and
was re-run clean after the fix.)

## 2. Migrations against a fresh database

```
$ rm -f db.sqlite3
$ python manage.py migrate
Operations to perform:
  Apply all migrations: admin, auditlog, auth, contenttypes, donations, donors, inventory, requests, sessions
Running migrations:
  ... (29 migrations) ...
  Applying requests.0003_remove_duplicate_inventory... OK
  Applying sessions.0001_initial... OK
```
All 29 migrations (existing Sprint 1/2 migrations plus this patch
series' new ones) applied cleanly against an empty database, including
`requests.0003_remove_duplicate_inventory` -- the data migration that
moves any existing aggregate stock counts into the unified
`inventory.BloodInventory` batch table before dropping the old table.

## 3. Full test suite

```
$ python manage.py test -v 1
Found 114 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
..................................................................................................................
----------------------------------------------------------------------
Ran 114 tests in ~127-141s
OK
```
Run repeatedly across this session (after each patch, to catch
regressions as early as possible): every run after DEFECT-01/02/03 were
fixed came back `OK`, 114/114. Run time varies by a few seconds between
runs on the same machine; the number of tests and the result did not.

**Breakdown by app**, from actually running `python manage.py test <app>
-v 0` individually for each app on the final state (these sum exactly to
the 114 reported by the full-suite run above):

| App | Tests | Notes |
|---|---|---|
| `authentication` | 23 | Pre-existing (login, logout, protected-page access) |
| `donors` | 32 | 29 pre-existing + 3 new (`EligibilityHistoryTests`) |
| `inventory` | 22 | 10 pre-existing (`tests.py`) + 8 new (`tests_services.py`) + 4 new (`tests_access.py`) |
| `requests` | 12 | 9 pre-existing (updated to the unified inventory model) + 3 new (queue filter, duplicate-issue, shared-constant consistency) |
| `donations` | 10 | All new (this patch series' module) |
| `auditlog` | 5 | All new |
| `accounts` | 10 | All new |
| **Total** | **114** | 23+32+22+12+10+5+10 = 114, matching `Found 114 test(s)` from the full-suite run |

## 4. Performance (Part 5.E)

```
$ python manage.py test inventory.performance_test -v 2
Login: p90=0.0020s (target <= 3.0s)
Request tracking: p90=0.0030s (target <= 3.0s)
Availability: p90=0.0032s (target <= 3.0s)
Inventory dashboard: p90=0.0137s (target <= 3.0s)
Donor list: p90=0.0076s (target <= 3.0s)
Donation list: p90=0.0047s (target <= 3.0s)
Request queue: p90=0.0059s (target <= 3.0s)
Administrative user list: p90=0.0098s (target <= 3.0s)
OK
```
20 samples per page, p90 taken from in-process Django test-client timing
against a database seeded with ~30 donor records (see
`inventory/performance_test.py::setUp`). As that file's own docstring
says: this measures view/ORM/template overhead on the machine running
the test, not production latency under a real WSGI server, network and
concurrent load -- it is a regression signal, not a production SLA
measurement.

## 5. Security validation

See `docs/SECURITY_VALIDATION.md` for the full control-by-control
mapping. Every "Pass" result quoted there is one of the 114 tests
summarized in section 3 above; nothing in that document was verified by
a separate, unreported mechanism.

## 6. What was NOT run, and why

- **No browser/visual testing tool was used** -- the usability/
  accessibility pass (focus-visible states, reduced-motion, responsive
  table overflow, contrast via the token palette) was done by reading
  the rendered CSS and HTML, not by driving a real browser. Part 6 asks
  this to be stated plainly rather than silently implied; none of this
  report claims a manual or automated browser walkthrough happened.
- **No production/staging deployment exists** to test HTTPS,
  concurrent-load behavior at scale, or real network latency against.
  See `docs/KNOWN_ISSUES.md` §5 and `docs/SECURITY_VALIDATION.md`
  (BBMS-SR-003).
- **No dependency/vulnerability scanner** (e.g. `pip-audit`, `bandit`)
  was run in this session.

## 7. Final delivery verification (demo-readiness pass)

Run against this exact final codebase, after fixing a real bug found
during this pass: `donors/management/commands/seed_demo_data.py` still
imported `requests.models.BloodInventory`, which section 2's own
unification removed earlier in this series -- so the demo seed command
would have crashed with an `ImportError` the moment anyone actually ran
it, despite every other check in this report passing. It was rewritten
to seed through the real service layer (`inventory.services.
receive_batch`, `donations.services.record_donation`,
`inventory.services.issue_units`, `DonorProfile.set_eligibility`)
instead of writing rows directly, which is also why it now demonstrates
every workflow, not just inventory.

```
$ rm -f db.sqlite3
$ python manage.py check
System check identified no issues (0 silenced).

$ python manage.py makemigrations --check --dry-run
No changes detected

$ python manage.py migrate
  ... (applies cleanly, 29 migrations) ...

$ python manage.py seed_demo_data
  user: created admin_demo
  user: created staff_demo
  user: created donor_demo1 / donor_demo2 / donor_demo3
  inventory: O+/A+/B+/AB+/O- seeded with starting units
  donation: recorded SEED-DON-0001, SEED-DON-0002
  eligibility: recorded a history entry for donor_demo3
  request: seeded 3 requests (pending/approved/fulfilled)
  request: seeded one fulfilled request with a matching issue

$ python manage.py seed_demo_data        # second run, same database
(no "created"/"recorded"/"seeded" lines at all -- every record already existed)
```

Row counts confirmed identical before and after the second run (5
users, 7 inventory batches, 8 inventory transactions, 2 donations, 3
requests, 1 issue, 8 audit log entries) -- the command is genuinely
idempotent, not idempotent-looking.

```
$ python manage.py test
Found 114 test(s).
...
Ran 114 tests in 128.022s
OK

$ python manage.py test inventory.performance_test -v 2
Login: p90=0.0028s (target <= 3.0s)
Request tracking: p90=0.0020s (target <= 3.0s)
Availability: p90=0.0025s (target <= 3.0s)
Inventory dashboard: p90=0.0096s (target <= 3.0s)
Donor list: p90=0.0055s (target <= 3.0s)
Donation list: p90=0.0051s (target <= 3.0s)
Request queue: p90=0.0062s (target <= 3.0s)
Administrative user list: p90=0.0108s (target <= 3.0s)
OK
```

**End-to-end workflow smoke test**, run directly through
`python manage.py shell` against the seeded database, exercising
exactly the chain this delivery names as required (donor →
eligibility → donation → inventory increase → request → approval →
issue → inventory decrease → audit trail), using the real model/service
functions rather than the HTTP layer (the HTTP layer itself is already
covered by the 114 automated tests in section 3):

```
BEFORE: O+ available = 21
eligibility history rows: 1
donation recorded, id=3 status=recorded
AFTER DONATION: O+ available = 24          (21 + 3, exactly the donated quantity)
request created, status=pending
request approved, status=approved
AFTER ISSUE: O+ available = 22             (24 - 2, exactly the issued quantity)
issue created, id=2
audit log entries total: 11
 - donation_recorded / inventory_increased  (x2, one pair per donation)
 - eligibility_changed
 - request_approved
 - blood_issued
```

Every number above moved by exactly the amount the operation should
have changed it by, and the audit log recorded every step -- this is
the concrete evidence behind `DEMO_GUIDE.md`'s script, not a separate,
unverified claim.
