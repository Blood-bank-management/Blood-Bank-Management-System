# Security and Authorization Test Report

## 1. Scope

This report covers security and authorization testing for the Django
application. It focuses on authentication enforcement, role separation,
CSRF protection, IDOR resistance, privilege-escalation controls, session
handling, and protection of inventory/request state transitions.

No commit or push was performed.

## 2. Test environment

| Item | Value |
|---|---|
| Operating system | Windows |
| Python | 3.13 (project virtual environment) |
| Framework | Django 6.1.1 |
| Database | Isolated Django test database |
| Test runner | Django built-in test runner |

## 3. Controls tested

### Authentication and authorization

- Anonymous users are redirected from protected pages to login.
- Donor accounts cannot access staff or administrative functions.
- Ordinary staff accounts cannot access administrator-only user management.
- Staff-only operations are protected server-side, not only hidden in the UI.
- State-changing workflows require the appropriate staff or administrator role.

### CSRF and session controls

- Login and logout POST requests require CSRF tokens.
- State-changing forms use Django CSRF protection.
- No `csrf_exempt` usage was found.
- Logout uses Django's built-in POST-only `LogoutView`.
- Session replay after logout is rejected by the existing logout tests.
- Secure session/CSRF cookie settings are enabled when `DEBUG=False`.

### Object-level and workflow protections

- Donor profile and personal donation history resolve through the logged-in
  user instead of accepting a user-controlled donor ID.
- Blood request tracking uses an unguessable UUID.
- Crafted role fields cannot grant staff or administrator privileges.
- The last active administrator cannot be demoted or deactivated.
- Duplicate donation references cannot double-credit inventory.
- Inventory issuance rejects insufficient stock and prevents negative balances.
- Inventory/request writes are covered by transactions and audit/ledger rows.

## 4. Test evidence

The relevant existing test modules cover the controls above:

- `authentication/tests/test_login.py`
- `authentication/tests/test_logout.py`
- `authentication/tests/test_access.py`
- `donors/tests.py`
- `donations/tests.py`
- `inventory/tests_access.py`
- `inventory/tests_services.py`
- `requests/tests.py`
- `auditlog/tests.py`
- `accounts/tests.py`

Full test command:

```powershell
.\.venv\Scripts\python.exe manage.py test -v 1
```

Result:

```text
Found 115 test(s).
Ran 115 tests in 99.865s
OK
```

Additional static consistency checks:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Results:

```text
System check identified no issues (0 silenced).
No changes detected
```

## 5. Findings

**No exploitable security or authorization vulnerabilities were identified
in the reviewed source and tested workflows.**

The application has server-side role checks, CSRF middleware, authenticated
session handling, object-scoped donor self-service views, protected
state-changing endpoints, and tests for privilege escalation and inventory
integrity.

## 6. Configuration and testing limitations

These are limitations of the test environment, not reported vulnerabilities:

- HTTPS was not tested against a deployed server. The project enables
  `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and
  HSTS settings only when `DEBUG=False`; local development defaults to
  `DEBUG=True`.
- No production reverse proxy, browser-origin policy, external identity
  provider, or deployed network configuration was available.
- No dependency vulnerability scanner such as `pip-audit` or `bandit` was
  run.
- The automated checks are Django test-client checks, not a penetration
  test or a browser-based security assessment.

## 7. Conclusion

**PASS — no security or authorization defects found in the tested scope.**

