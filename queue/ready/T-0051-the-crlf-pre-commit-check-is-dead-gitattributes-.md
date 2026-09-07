---
id: T-0051
title: the CRLF pre-commit check is dead - gitattributes normalises CRLF away before the hook sees it
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [.githooks/pre-commit, ops/sane]
pins_affected: []
reviewer: null
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
