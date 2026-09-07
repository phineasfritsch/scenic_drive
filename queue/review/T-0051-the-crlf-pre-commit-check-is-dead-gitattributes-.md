---
id: T-0051
title: the CRLF pre-commit check is dead - gitattributes normalises CRLF away before the hook sees it
state: review
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-07T21:29:07Z
lease_expires_at: 2026-09-07T23:29:07Z
worktree: null
branch: task/T-0051
exclusive: []
touches: [.githooks/pre-commit, ops/sane]
pins_affected: []
reviewer: agent/reviewer-38
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`.githooks/pre-commit` check 1 reads the STAGED blob and greps it for a carriage return:

    if git show ":$f" | grep -qI "$CR"; then echo "pre-commit: CRLF in $f ..."

But `.gitattributes` says `* text=auto eol=lf`, so git normalises CRLF to LF at `git add` time. By the time
the hook runs, the staged blob has no CR in it — the check cannot fire for the thing it is named after.
Found by agent/reviewer-28 while reviewing T-0047, confirmed identical on the pre-T-0047 hook, so it is
pre-existing and was not introduced by that task.

This is the fourth decorative check found in this repo (three were in
`services/etl/tests/test_dockerfile.py`), and the same species: it tests a thing that cannot happen at the
point it looks.

Whether it should be fixed or deleted is the actual question, and it needs deciding rather than patching:

- **Delete it.** If `text=auto eol=lf` is doing the job, a second check that can never fire is noise, and
  `ops/sane` already refuses a tracked file containing CR and `core.autocrlf=true` — the states that actually
  matter. There is a pin on `.gitattributes` carrying `eol=lf` (P-GIT-01), so the normalisation itself is
  guarded.
- **Fix it.** Check the WORKING TREE rather than the staged blob, so a file written with CRLF is caught
  before it is normalised — useful because `ops/*` scripts are read by `bash`, and a CRLF script fails in
  ways that read as a logic bug. Note T-0047 is adding a working-tree comparison to the same hook, so the
  plumbing will be there.
- **Narrow it.** Only files where CRLF genuinely breaks something — `ops/`, `.githooks/`, `*.sh` — rather
  than everything.

Whichever is chosen, the demonstration is the point: show the check firing on something. A check that has
never been seen red is untested, and this one has never been red because it cannot be.

Also worth confirming while in there: does `.gitattributes` cover files with no extension, which is what most
of `ops/` is?

## Log
- 2026-09-07T21:29:07Z claimed by agent/unknown; lease until 2026-09-07T23:29:07Z

- 2026-09-08T01:35Z claimed and fixed by agent/claude-opus-5, stacked on task/T-0047 (done), which owns
  .githooks/pre-commit.

  **The premise is confirmed by measurement, not by reading.** With a CRLF file staged:

      the file on disk really does have CRLF ......... yes
      the STAGED blob .............................. no CR: .gitattributes normalised it at git add time
      OLD hook ..................................... DID NOT FIRE

  So the check could not catch the thing it was named after, and had never been red because it could not be.

  **Decision: FIX, narrowed - not delete.** The brief offered delete / fix / narrow. Deleting is defensible
  (normalisation works, P-GIT-01 guards `.gitattributes`, `ops/sane` refuses a tracked CR) but it discards a
  real failure that none of those cover: they all protect the COMMITTED bytes, and `bash ops/whatever` reads
  the file ON DISK. A CRLF script fails as `$'': command not found`, or worse, silently, with a trailing CR
  swallowed into a variable - and it reads as a logic bug, which is how it costs an afternoon instead of a
  minute. `.gitattributes` carries `ops/** eol=lf` precisely because that has already happened here.

  So it now checks the WORKING TREE, narrowed to files that are executed as shell - `ops/*`, `.githooks/*`,
  `*.sh`, `*.bash`. Everywhere else normalisation genuinely is the answer and a second check is noise.

  **THE FIRST VERSION OF MY FIX WAS ALSO DECORATIVE, and only running the demonstration found it.** I wrote
  `grep -qI "$CR" "$f"` and it did not fire either. On Windows, git-bash's grep opens the file in TEXT mode
  and strips the CRs before matching. `-U` is what stops that; it is a no-op on Linux, verified directly
  under WSL (`GNU grep -qIU: fires on CR` / `silent on a clean LF file`). I had just written a fix for a
  decorative check and made it decorative in a new way, and the only thing between that and a green commit
  was actually running the red demo instead of assuming it.

  **Four states demonstrated**, all after the fix:

      OLD hook, CRLF script staged ................. DID NOT FIRE   <- the original defect
      NEW hook, same state ......................... pre-commit: CRLF in the working tree: ops/_crlf_demo
      NEW hook, CRLF in docs/_crlf_demo.md ......... silent (narrowing: not executed as shell)
      NEW hook, clean tree ......................... silent on CRLF; hook exit 0

  The third and fourth matter as much as the second: a check that fires on everything is a check people
  disable.

  **The brief's other question, answered: yes.** `.gitattributes` covers extensionless files. `* text=auto
  eol=lf` matches any name, and `ops/**` and `.githooks/**` are listed explicitly on top of it - which is
  most of `ops/`, since almost none of it has an extension.

  **Verification:** `ops/test` -> `TESTS linux=50/50 ios=skipped failed=0 skipped=0` / `OK`;
  `ops/check-pins` -> `PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux` (9 rather than 10 because
  this branch is based on task/T-0047, which predates a pin added later on main - not a regression, and worth
  the reviewer confirming); `ops/queue-check` -> `QUEUE OK (43 tasks)`. The demo script was not committed: it
  stages and deletes files and exists to be run once. GitHub Actions is DISABLED repo-wide (T-0053), so there
  is no CI signal on this at all.

  **What to attack.** The narrowing is a list of globs, and a shell script that lives outside `ops/` with no
  `.sh` extension is now unprotected - `.githooks/commit-msg` is covered by `.githooks/*`, but a future
  `scripts/foo` would not be. Deciding by shebang rather than by path would be more honest and I did not do
  it. Second: the check only looks at STAGED paths, so a CRLF `ops/` file that is not part of this commit
  still breaks the next person; `ops/sane` is the right home for a whole-tree sweep and does not do one.
