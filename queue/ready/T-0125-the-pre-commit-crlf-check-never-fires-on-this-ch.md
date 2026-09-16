---
id: T-0125
title: the pre-commit CRLF check never fires on this checkout because MSYS grep strips CR in text mode
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [.githooks/pre-commit, ops/lib/check-touches-merge.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "the hook refuses a staged file that genuinely contains a carriage return, proven with od -c"
  - "RED: it accepts that same file today, and the word CRLF appearing in the commit message is not evidence"
---
## Brief

**The pre-commit CRLF check never fires on the machine this project is driven from.** It has never refused
anything here, and nobody noticed because a check that always passes looks exactly like a codebase with no
CRLF in it.

Found by reviewer-pr78 while attacking the merge gate, and confirmed binary-safe after their own first
attempt gave a false green:

    .githooks/pre-commit:  grep -qI "$CR" ...

MSYS2's GNU grep 3.0 opens files in TEXT mode and strips `\r` before matching, so `grep -qI` cannot see a
carriage return that is genuinely in the blob. `grep -qU` (force binary) matches. The reviewer proved the
byte is really there with `od -c` on the staged blob.

**Their method note is the finding underneath the finding.** Their first probe reported the check working -
because it matched the word "CRLF" in the *commit message*, not a carriage return in a file. They caught it,
rewrote the probe binary-safe, and the verdict reversed. That is this repository's signature defect inside
the harness written to hunt it, which is now the ninth or tenth time it has appeared in one session.

## Why this matters here specifically

`.gitattributes` sets `* text=auto eol=lf` and `ops/sane` exits 2 on `core.autocrlf true`, so there are two
other lines of defence and the tree is currently clean. But the hook is the one that runs on every commit by
every agent, and it is the one that would catch a file introduced with CRLF by a Windows editor before it
reaches the tree. It has been inert for the entire history of the repository on this checkout.

It is also the same shape as [[T-0124]]: a check that is green in Linux CI and non-functional in git-bash on
the Windows checkout, read as "fine" because it never says anything.

Do:

1. Make the CRLF scan binary-safe. `grep -qU` is the one-character fix; whatever is chosen must be verified
   against a blob that genuinely contains `\r`, checked with `od -c` rather than by eye.
2. **RED FIRST, and binary-safe.** Stage a file whose content really holds a carriage return and show the
   hook refusing it. Beware the trap the reviewer fell into and documented: matching the word "CRLF"
   anywhere in the commit message, the filename, or the hook's own output is not evidence that the check
   fired. Assert on the refusal text the hook prints for a CRLF file, and prove the byte is present.
3. Add the case to `ops/lib/check-touches-merge.py`, which already builds throwaway repos with the real hook
   installed and now asserts on the refusal REASON rather than the exit code. A CRLF case belongs beside the
   secret-across-a-merge case.
4. Check the other `grep` calls in `.githooks/pre-commit` for the same text-mode assumption - the secret
   scan greps blob content too, and a secret split across a CRLF boundary is the obvious next question.

**Do not fix this by changing `.gitattributes` or `core.autocrlf`.** Those are already correct and are a
different layer; the defect is that the hook cannot see what it is looking at.

## Log
