# Testing

## Framework

Django's built-in test framework (`django.test.TestCase`, built on
Python's `unittest`) and test client (`self.client`). No third-party
testing library (`pytest`, `factory_boy`, etc.) is used anywhere in this
repository — `requirements.txt` lists only `asgiref`, `Django`,
`sqlparse` and `tzdata`.

## How to run the test suite

```bash
python manage.py test
```

**Actually executed in this environment, on the current `main` branch:**

```
Found 71 test(s).
----------------------------------------------------------------------
Ran 71 tests in ~23s

OK
```

All 71 tests pass. Nothing in this document claims a result that was not
observed by running the command above.

For a single app:

```bash
python manage.py test authentication
python manage.py test donors
python manage.py test inventory
python manage.py test requests
```

For one test file or one test method:

```bash
python manage.py test donors.tests.DonorRegistrationTests
python manage.py test donors.tests.DonorRegistrationTests.test_donor_ut_01_valid_registration_creates_user_and_profile
```

### The performance test needs a separate command

```bash
python manage.py test inventory.performance_test -v 2
```

Django's default test discovery only imports files matching `test*.py`.
`inventory/performance_test.py` does not match that pattern, so
`python manage.py test` silently skips it — it is not part of the 71
above. Run it explicitly, as shown. Actually executed in this
environment:

```
Login: p90=0.0021s (target <= 3.0s)
Availability: p90=0.0024s (target <= 3.0s)
Inventory summary: p90=0.0048s (target <= 3.0s)
Ran 1 test in ~0.4s

OK
```

This is a known limitation of the file as it stands today, not a defect
in what it tests — see "Known test limitations" below.

### Supporting checks

```bash
python manage.py check                              # Django system checks
python manage.py makemigrations --check --dry-run    # no un-made model changes
```

Both run clean (no issues, no changes detected) on the current `main`
branch.

## Test files and what they cover

| File | Tests | Covers |
|---|---:|---|
| `authentication/tests/test_login.py` | 16 | Valid/invalid credentials, login by username or e-mail, empty-field rejection, an e-mail shared by two accounts, an inactive account, password hashing, CSRF enforcement on the login POST, `?next=` redirect handling (including rejecting an off-site `next`), and that an already-logged-in user is redirected away from the login page. |
| `authentication/tests/test_logout.py` | 4 | Logout actually ends the session (including that the server-side session row is deleted, and a replayed old session cookie no longer works), logout requires POST (a GET returns 405), logout requires a CSRF token, and logging out while already anonymous is harmless. |
| `authentication/tests/test_access.py` | 3 | An anonymous request to the protected home page is redirected to login with `?next=`; a logged-in user can reach it; the page itself renders a CSRF-protected logout form. |
| `donors/tests.py` | 29 | Four test classes — see breakdown below. |
| `inventory/tests.py` | 10 | `BloodInventory` model validation (negative quantity rejected, expiry-before-collection rejected), the availability-search view (missing blood group, unsupported blood group, zero stock, available quantity, excluding expired units from the sum), and one basic non-negative-quantity integrity check. |
| `inventory/performance_test.py` | 1 (run separately) | p90 response time for the login, availability-search and inventory-summary pages, asserted to stay under 3 seconds (BBMS-53/BBMS-NF-001 groundwork). |
| `requests/tests.py` | 9 | Submitting and tracking a request, rejecting a request with missing fields or non-positive quantity, that only staff can review a request and rejecting requires a note, approving and rejecting, and the issue/distribution workflow: a successful issue deducts inventory and marks the request fulfilled, an issue is rejected for an unapproved request or insufficient stock, and an issue is rejected when no inventory row exists for that blood group at all. |

### `donors/tests.py` breakdown (4 classes, 29 tests)

- **`DonorRegistrationTests`** (11) — valid registration creates both the
  `User` and the `DonorProfile`; the created account is never staff or
  superuser; registration logs the user in; duplicate username/e-mail is
  rejected; missing required fields are rejected; mismatched passwords
  are rejected; a weak password is rejected (reusing the project's
  `AUTH_PASSWORD_VALIDATORS`); a future date of birth is rejected; the
  stored password is hashed, not plaintext; an already-authenticated user
  hitting the registration page is redirected away.
- **`DonorProfileTests`** (6) — anonymous access is redirected to login;
  a donor can view and update their own profile; the profile update form
  has no eligibility field at all; posting an eligibility value to the
  profile endpoint by hand is silently ignored (there's no code path
  that reads it); the profile view has no id/pk parameter for an
  attacker to swap, and does not leak another donor's data.
- **`StaffDonorManagementTests`** (8) — anonymous and donor-role access
  to the donor list and donor detail pages are both rejected (redirect
  and 403 respectively); a donor is rejected from a donor-detail page
  even when the `pk` in the URL is their own profile; a non-existent
  `pk` returns a proper 404, not a crash; staff can view any donor and
  update eligibility, with the audit fields (`eligibility_updated_by`,
  `eligibility_updated_at`) correctly stamped; a donor cannot change
  their own eligibility via a direct POST; eligibility updates require a
  CSRF token.
- **`DonorIntegrationWorkflowTests`** (1 end-to-end test) — register →
  land on the home page → view/edit own profile (no eligibility field
  visible) → blocked from the staff donor list and from the own-record
  staff detail page → log out → protected pages become inaccessible
  again → a staff account logs in, finds the new donor, opens their
  record, changes their eligibility → the donor logs back in and sees
  the updated status on their own profile → the donor still cannot
  reverse the change themselves.

## Known test limitations

- **`inventory/performance_test.py` is excluded from default test
  discovery** (see above) — anyone running `python manage.py test`
  without reading this document will not know it exists or ran. The
  simplest fix (renaming it to `test_performance.py`) was deliberately
  not made outside this documentation pass, since it touches a file
  outside the scope of the change that added this doc set; it's flagged
  here and in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) for the team to decide.
- **No browser-based/end-to-end test suite.** All tests use Django's
  test client (server-side request/response assertions), not a real
  browser. Rendered-page correctness (layout, JavaScript, if any were
  added) is not covered by this suite.
- **No load or concurrency testing beyond the existing performance
  smoke test.** `requests.views.issue_blood`'s `select_for_update()`
  locking is exercised by ordinary sequential tests, not by a
  concurrent-request test that would actually prove the race condition
  it's meant to prevent is closed.
- **No test for the two-`BloodInventory`-models inconsistency.** Because
  `inventory.tests` and `requests.tests` each test their own model in
  isolation, nothing in the suite would catch the two models drifting
  out of sync with each other — see
  [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) §1.
- **Donation Management and Administrative user management have no
  tests**, because no code for those requirements exists yet (BBMS-F-007
  to 009, BBMS-F-020).
