# Final Definition of Done

Project-wide Definition of Done for this patch series. A requirement is
only "Done" below when every one of these 18 criteria that applies to it
is actually met -- see `IMPLEMENTATION_SUMMARY.md` for per-requirement
status against this bar.

1. **Requirement implementation** -- the feature does what the SRS/Jira
   item describes, verified against the actual code (not a template or
   placeholder standing in for it).
2. **Input validation** -- every form field that can be wrong is
   validated server-side (Django Form/ModelForm fields and `clean*`
   methods), not just client-side `type="number"` hints.
3. **Authorization** -- every view that should be restricted has a
   server-side decorator (`login_required`/`staff_required`/
   `admin_required`) or equivalent check; a hidden nav link is never the
   only protection.
4. **IDOR prevention** -- no view trusts a URL parameter as proof of
   ownership; self-service views (profile, own donation history) take no
   id parameter at all.
5. **CSRF protection** -- every POST form includes `{% csrf_token %}`;
   `csrf_exempt` is never used anywhere in this project.
6. **Database integrity** -- foreign keys have an explicit `on_delete`;
   unique constraints exist where duplicates would be a real problem
   (e.g. `Donation.collection_reference`).
7. **Transaction safety** -- any operation that writes to more than one
   table (donation -> inventory, issue -> inventory -> audit log) is
   wrapped in `transaction.atomic()`, with `select_for_update()` where
   concurrent access could otherwise race.
8. **Unit tests** -- model/form/service-level validation has a test that
   exercises it directly, not only through an HTTP round-trip.
9. **Integration tests** -- the view + the services/models it calls are
   tested together, asserting the resulting state change, not just a 200
   status code.
10. **System tests** -- at least one test per major workflow (donor
    registration through to eligibility change, request submission
    through to issue) exercises the whole path.
11. **Regression testing** -- the pre-existing Sprint 1/2 suite (71
    tests) still passes, unmodified except where a requirement
    genuinely changed the schema it tested against.
12. **Performance checks** -- the page is included in
    `inventory/performance_test.py` and meets the 3-second p90 target
    against the test client (with the test-client-vs-production caveat
    documented in `docs/TEST_EXECUTION_REPORT.md`).
13. **Security checks** -- the relevant row(s) in
    `docs/SECURITY_VALIDATION.md` are "Pass", not "assumed".
14. **Responsive UI** -- the page extends `templates/base.html` (whose
    tables/forms/nav/metric-grid all have a mobile breakpoint) or has its
    own verified responsive behavior.
15. **Light/dark theme verification** -- the page uses only the shared
    CSS custom properties (no hardcoded color), confirmed by grepping its
    template for `style="` and checking any hit is layout-only.
16. **Documentation** -- the feature is described in the relevant doc(s)
    (`README.md`, `docs/ARCHITECTURE.md`, `docs/USER_GUIDE.md`, etc.) as
    it actually behaves, not as originally planned.
17. **Defect resolution** -- any defect found while building/testing the
    feature is in `docs/DEFECT_LOG.md` with a retest, not silently fixed
    and forgotten.
18. **Acceptance evidence** -- a specific test name or command + output
    backs every claim of "Done", traceable from
    `IMPLEMENTATION_SUMMARY.md` through `docs/REQUIREMENTS_TRACEABILITY.md`
    to `docs/TEST_EXECUTION_REPORT.md`.

## Explicit exceptions (documented, not silently skipped)

- Criterion 12/14/15 for a handful of pre-existing templates this patch
  series did not touch beyond inheriting the new base.html (e.g.
  `donors/templates/donors/register.html`) were verified by the same
  "grep for hardcoded color" method as criterion 15, not by opening each
  page in a browser -- see `docs/TEST_EXECUTION_REPORT.md` §6 for what
  browser-level verification was and wasn't done.
- BBMS-SR-003 (HTTPS actually served) does not meet criterion 1 for this
  patch series or any prior one -- it remains a documented, open gap
  (`docs/KNOWN_ISSUES.md` §5), not something marked Done.
