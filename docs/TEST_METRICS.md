# Test metrics

Derived directly from `docs/TEST_EXECUTION_REPORT.md`'s actual run
output -- nothing here is a separate, re-estimated figure.

## Coverage by test type (Part 5.A/B/C/D)

| Type | Where | Examples |
|---|---|---|
| Unit | Model/form/service validation, no HTTP | `donations/tests.py::DonationServiceTests` (quantity/date validation), `inventory/tests_services.py` (ledger math, FIFO issuing), `donors/tests.py::EligibilityHistoryTests` |
| Integration | A view + the services/models it calls together | `donations/tests.py::test_record_donation_creates_donation_and_credits_inventory`, `requests/tests.py::test_approved_request_issue_deducts_inventory_and_fulfills_request` |
| Access/RBAC/IDOR | Allowed vs. denied, per role, per Part 3.F | `accounts/tests.py::AdminUserManagementAccessTests`, `inventory/tests_access.py`, `donations/tests.py::DonationViewAccessTests`, `auditlog/tests.py` access tests |
| System/workflow | A full multi-step scenario through several views | `donors/tests.py`'s registration -> login -> profile -> staff review -> eligibility change end-to-end test (pre-existing, still passing against the new eligibility-history code path) |
| Regression | Pre-existing Sprint 1/2 tests, re-run unmodified except where the underlying schema genuinely changed | All of `authentication/tests/`, `donors/tests.py`'s original 29, `inventory/tests.py`'s original 10, `requests/tests.py`'s original 9 (updated only where the duplicate-inventory-model removal required it -- see `docs/DEFECT_LOG.md` is NOT where that's logged, since it isn't a defect; see the commit message for `7ffab19`) |
| Performance | p90 response time, 8 pages | `inventory/performance_test.py` |

## Test count over time

| Point | Test count | Result |
|---|---|---|
| Before this patch series (baseline, per `docs/TESTING.md`) | 71 | OK |
| After this patch series | 114 | OK |
| Net new tests | 43 | -- |

## Pass rate

114/114 = **100%** on the final run reported in
`docs/TEST_EXECUTION_REPORT.md`. Two earlier, pre-fix runs during
development were not 100% -- see `docs/DEFECT_LOG.md` for both (8
failures from DEFECT-01, 2 failures from DEFECT-03) -- reported here for
completeness rather than only showing the final green run.

## Defect metrics

From `docs/DEFECT_LOG.md`: 4 defects found across this project's work,
all fixed and retested, 0 reopened, 0 outstanding. 1 of the 4
(DEFECT-03) was a test-authoring defect rather than an application
defect. DEFECT-04 (the demo seed command importing a model this same
series had already removed) was found during a later, separate
demo-readiness pass -- after the first three and after the 114-test
suite had already been reported green -- precisely because no
automated test in that suite actually invokes `seed_demo_data`,
illustrating why that command needed its own explicit verification
rather than being covered implicitly by "all tests pass."

## Known limitation of these metrics

This is a single project's test suite run by one contributor in one
environment, not a measured-over-time trend across multiple
contributors/CI runs -- there is no historical flake rate, no coverage
percentage tool (`coverage.py` was not run), and no CI system in this
repository to pull metrics from automatically. Everything above is this
session's actual commands and their actual output.
