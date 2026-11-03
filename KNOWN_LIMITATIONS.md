# Known Limitations

A short, honest summary for anyone about to demo or grade this project.
Full detail, impact, and suggested resolutions for each item are in
[`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md) — this file is the
one-page version of that, plus the handful of items specific to this
final delivery pass.

Nothing below is hidden or glossed over in the demo: if you hit one of
these during a walkthrough, it's expected, not a bug you found.

## Functional

1. **Donor eligibility is still staff-set, not auto-computed.**
   `donations.models.next_eligible_date()` calculates the date a donor
   may give blood again and shows it on the donor dashboard, but nothing
   automatically flips `eligibility_status` from it — a staff member
   still makes that call via the donor detail page. See
   `docs/KNOWN_ISSUES.md` §8.1.
2. **The public request-tracking link is a bearer token, not an
   authenticated check.** Anyone who has the tracking URL can see that
   request's details — this is deliberate (so a hospital desk without
   an account can still track a request), not an oversight. See
   `docs/KNOWN_ISSUES.md` §2.
3. **Legacy migrated stock gets an assumed shelf life.** The data
   migration that removed the old duplicate inventory model assigns a
   42-day shelf life from the migration date to any pre-existing
   aggregate stock, because the old model never recorded a real
   collection date. This only matters if you run this migration against
   a database that already had real stock data in the old model — a
   fresh database (like the one `seed_demo_data` builds) has nothing to
   migrate, so this doesn't affect the demo. See `docs/KNOWN_ISSUES.md`
   §8.2.

## UI / design

4. **The application shell is a restyled top navigation, not a sidebar
   with breadcrumbs.** Every page uses the same premium design system
   (palette, typography, light/dark/system theming), but the brief's
   sidebar-with-breadcrumbs layout was not built — the existing
   top-nav shell was kept and re-themed instead. See
   `docs/KNOWN_ISSUES.md` §8.3.
5. **No browser-based visual/accessibility verification was performed
   by me.** Focus states, dark-mode contrast, responsive table
   overflow, and `prefers-reduced-motion` are implemented and were
   code-reviewed, but no browser-automation tool was used to actually
   open the pages during development. **Before your demo**, open the
   app in a real browser once — both themes, and at a narrow/mobile
   width — so you're not discovering a CSS surprise live. See
   `docs/KNOWN_ISSUES.md` §8.4.

## Infrastructure / deployment

6. **No HTTPS deployment.** `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`,
   HSTS, etc. exist in `bloodbank/settings.py` but are gated on `DEBUG`
   and there is no deployment (web server, reverse proxy, certificate)
   in this repository that would actually serve the app over HTTPS.
   None of this matters for a local demo on `runserver`. See
   `docs/KNOWN_ISSUES.md` §5.
7. **SQLite only — no MySQL configuration exists in this project.**
   `bloodbank/settings.py` has always used
   `django.db.backends.sqlite3`; there is no MySQL setup anywhere in
   the codebase to preserve. If your submission needs to claim MySQL
   support, that would be new work, not something this patch series
   found and kept.
8. **No dependency/vulnerability scan was run.**
9. **No CI pipeline** — `python manage.py check` / `test` /
   `makemigrations --check` are run by hand, not automatically on push.

## Testing

10. **Performance numbers are from Django's in-process test client**,
    not a production WSGI server under real load — see
    `TEST_EXECUTION_REPORT.md` §4 for the actual numbers and that
    caveat stated again in context.
11. **The inventory locking path has a sequential proxy test, not a
    true concurrent-request test.** `inventory/tests_services.py`
    verifies a second issue against already-exhausted stock is
    rejected, in sequence — it does not spin up actual concurrent
    requests to prove the `select_for_update()` lock holds under real
    parallelism.

None of the above block a local demo of every workflow named in this
delivery's required scope (donor registration → eligibility → donation
→ inventory update → request → approval → issue → inventory deduction
→ distribution log) — see [`DEMO_GUIDE.md`](DEMO_GUIDE.md) for the exact
script.
