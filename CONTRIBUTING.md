# Contributing

How this repository is actually used, based on its real history
(`git log --merges`), plus the practices this documentation pass adds.
Every command below was tested against this repository's own branches —
none of it is generic boilerplate.

## Branch naming

The project's real history uses `feature/<description>`:

```
feature/blood-inventory
feature/blood_request_and_issue_distribution
feature/nidhi-sprint-2
```

Both kebab-case and snake_case show up in the existing history — pick
kebab-case (`feature/short-description`) for new branches so the
convention converges, but don't rename branches that already exist.

Suggested prefixes for new work:

| Prefix | For |
|---|---|
| `feature/<name>` | A new capability (what every branch above was) |
| `fix/<name>` | A bug fix |
| `docs/<name>` | Documentation only (this branch: `docs/project-documentation`) |
| `chore/<name>` | Dependency bumps, cleanup, no behavior change |

## Creating a feature branch

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

## Making meaningful commits

What this repository's own history already does well, worth keeping:

- One logical change per commit (`e61fdc6 Add HTTPS security settings`,
  `29a315c Add expired blood units view` — each commit is one
  independently-reviewable thing, not a dump of the day's work).
- A commit message that says *what* and, where it's not obvious, *why*.

```bash
git add path/to/changed/file.py
git commit -m "fix(inventory): require staff role for inventory summary"
```

Avoid:

- Committing unrelated changes together (a bug fix bundled with an
  unrelated template restyle).
- Empty or placeholder commits made only to inflate a commit count — a
  commit should correspond to a real, reviewed change.
- Rewriting commit history that's already been pushed and might be in
  someone else's local branch (`git commit --amend` / `git rebase` are
  fine on a branch only you are working on, before it's pushed, or after
  explicit agreement with whoever else has it checked out).

## Running tests before pushing

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py test inventory.performance_test -v 2   # not run by `test` alone — see docs/TESTING.md
```

All four should be clean before you open a pull request. If
`makemigrations --check` reports pending changes, run
`python manage.py makemigrations`, commit the generated migration file,
and re-run the check.

## Pushing and opening a pull request

```bash
git push -u origin feature/your-feature-name
```

Then open a pull request against `main` on GitHub (this repository has
always merged via PR — every feature branch in its history was merged
with `Merge pull request #N from ...`, never pushed straight to `main`).
Describe, in the PR body:

- What changed and why.
- How you tested it (paste the real command output, as this document
  tries to do throughout).
- Anything you know is incomplete or out of scope, rather than letting a
  reviewer discover it.

## Reviewing changes

- Check out the branch locally and run the test suite yourself, don't
  review by reading the diff alone — this repository has already had one
  case (see [`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md) §4) where a
  merge silently dropped settings that were only in one side of the
  merge, which a full local test run plus a settings-file diff would have
  caught.
- For a change to `bloodbank/settings.py` specifically: diff it against
  both `main` and the branch's own base commit before approving — a
  three-way merge can silently prefer one side's version of a file
  wholesale rather than combining both sides' changes.

## Merging into main

Prefer "Merge pull request" (a merge commit) over squash or rebase for
this repository, since that's what its entire history already does — a
mixed strategy makes `git log --graph` harder to read. After merging:

```bash
git checkout main
git pull origin main
git branch -d feature/your-feature-name          # delete the local branch
git push origin --delete feature/your-feature-name   # and the remote one, if GitHub didn't already
```

## Never force-push

Never run `git push --force` (or `--force-with-lease`) on `main`, and
avoid it on a shared feature branch unless everyone working on that
branch has explicitly agreed. A force-push can silently discard a
teammate's already-pushed commits. If your local branch has diverged from
its remote because someone else pushed to it, merge or rebase onto their
changes instead:

```bash
git fetch origin
git merge origin/feature/your-feature-name
# or, if you prefer a linear history and are the only one on the branch:
git rebase origin/feature/your-feature-name
```

## Resolving a merge conflict

```bash
git checkout main
git pull origin main
git checkout feature/your-feature-name
git merge main
```

Git will mark conflicting sections in the affected files with
`<<<<<<<` / `=======` / `>>>>>>>` markers. Open each one, decide what the
merged result should be, remove the markers, then:

```bash
git add <the files you resolved>
git commit            # completes the merge commit
python manage.py test # re-run the suite -- a clean merge can still be a broken one
git push
```

If the conflict is in `bloodbank/settings.py`, read both sides carefully
before picking one — this is exactly the file where a careless resolution
previously dropped real security settings (`docs/KNOWN_ISSUES.md` §4).
When in doubt, keep both sides' changes rather than discarding either.
