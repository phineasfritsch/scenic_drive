---
id: T-0047
title: pre-commit should refuse a commit whose staged content is stale relative to the working tree
state: review
owner: agent/builder-8
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T16:57:35Z
lease_expires_at: 2026-09-07T19:57:35Z
worktree: ../wt/T-0047
branch: task/T-0047
exclusive: []
touches: [.githooks/pre-commit]
pins_affected: []
reviewer: agent/reviewer-28
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Six agents in one session have shipped a commit whose staged content was stale relative to the working tree,
every one of them the same shape:

    git mv queue/review/T-XXXX-....md queue/done/T-XXXX-....md   # stages the rename against the PRE-edit blob
    # ... edit the file: state: done, append findings ...
    git add <one path>                                            # a second path in the same command was wrong,
                                                                  # or the edit came after the mv and was never staged
    git commit                                                    # lands a pure rename, 0 insertions

`git status` shows a clean rename and says nothing is wrong. The reviewer's verdict, their `state: done`, and
their entire findings log are simply absent from the commit. Two agents caught it only because the task
instructions told them to run `git show HEAD:<path>` afterwards; the rest caught it by luck or not at all
(agent/reviewer-18's first PASS commit `43565bb` had to be repaired by `b2b79f3`; agent/reviewer-22's
`290a99a` by `54268e8`; agent/reviewer-20's by `7ece47a`).

An instruction that has to be repeated in every prompt is not a guard. This is mechanical and belongs in the
hook.

- In `.githooks/pre-commit`, for every path that is staged, compare the staged blob to the working-tree file.
  If they differ, the commit is about to record something other than what the author is looking at: refuse,
  name the paths, and say `git add <path>` fixes it.
- Consider whether this should be a refusal or a warning. Argue it in the log. A refusal is right if the
  legitimate cases are rare; the obvious legitimate case is a deliberate partial stage (`git add -p`), so say
  how someone does that on purpose - an env var like `ALLOW_PARTIAL_STAGE=1`, or exempting a path the author
  names.
- Demonstrate red: reproduce the exact `git mv` + edit + commit sequence and show the hook accepts it today,
  then refuses after the fix. Then show a deliberate partial stage still works by whatever route you chose.
- Check the interaction with the existing `touches:` and CRLF checks - both read `git show ":$f"`, i.e. the
  staged blob, which is correct and should stay that way.

Related: T-0039 fixes a different hole in the same hook (the `touches:` block being skipped for tasks in
`queue/done/`). Land that first if both are open; they touch the same file.

## Log
- 2026-09-07T16:57:35Z claimed by agent/builder-8; lease until 2026-09-07T19:57:35Z
- 2026-09-07T17:20:00Z agent/builder-8: fix landed in commit a137685 on task/T-0047 (on top of task/T-0039's
  186d612, per the brief). Full red/green log below.

### Design: refusal, not warning, with a scoped escape hatch

Refusal. The two checks already in the hook (CRLF, secret-looking content) are hard refusals with no waiver
at all, and this bug's cost is strictly worse than either: it doesn't corrupt a file, it silently *deletes*
a reviewer's verdict and their entire findings log while `git status` and the commit summary both look
clean. A warning that an agent can scroll past is exactly the failure mode already observed six times this
session - the *instruction* to check was already in every prompt and was ignored or missed six times. A
mechanical refusal is the only thing six agents in a row didn't have.

The counter-argument for "warning" would be that the legitimate case (a deliberate partial stage, `git add
-p`) is common enough that a hard refusal becomes friction people route around with `--no-verify` - which
is worse than the bug, per the brief. I don't think that's true here: nothing in this repo's actual workflow
(queue moves, code edits under `touches:`) calls for partial-staging a file mid-edit. `git add -p` is a
deliberate, unusual act, and an agent doing it on purpose can say so - hence the escape hatch below rather
than downgrading the check to advisory.

Escape hatch: `ALLOW_PARTIAL_STAGE`.
- `ALLOW_PARTIAL_STAGE=1` waives the stale-content check for every path it would otherwise flag - the
  blanket form the brief suggested.
- `ALLOW_PARTIAL_STAGE=path/one,path/two` (comma- or colon-separated) waives only the *named* paths; any
  other stale or missing path in the same commit still refuses. This is the "something better" the brief
  invited: a blanket `=1` set out of habit (e.g. because the hook nagged on a previous commit and the env
  var is still exported in the shell) would otherwise silently wave through an unrelated, unintended stale
  file in a later commit. The path-scoped form was tested and confirmed to (a) waive exactly the named path
  and (b) still refuse when the wrong path is named - see RESULT 3f/3g below.
- Both forms print which paths were waived, so the waiver is visible in the commit's terminal output even
  though it isn't recorded in the commit itself (matching how `--no-verify` and the existing checks behave -
  nothing in this hook writes to the commit object).

### Mechanism

For every staged path (`git diff --cached --name-only -z --diff-filter=ACMR`, NUL-delimited - see below),
compare `git rev-parse ":$f"` (the object id git will commit) to `git hash-object -- "$f"` (the object id
`git add` would produce from the *current* working-tree file, via the same path so `.gitattributes` clean
filters apply). If they differ, the working tree has moved since `git add` and the commit would record
something the author isn't looking at.

This is deliberately an object-id comparison, not a byte/line diff of `git show ":$f"` vs `cat "$f"`, because
`git hash-object` on a real path applies the identical clean-filter pipeline `git add` uses (confirmed
empirically below): CRLF/LF text normalization per `.gitattributes`, and symlink-target hashing (lstat-based,
same code path as staging) rather than following the link and hashing the target's content. A raw-bytes
compare would have produced the false positive the brief warned about (every CRLF-on-Windows file refused);
the hash-object compare does not.

A staged deletion (`git rm`, or `git add` after manual removal) never enters this check at all: `--diff-
filter=ACMR` excludes `D`, so there is nothing to compare and nothing is flagged - this is correct because a
deletion *is* consistent between "what's staged" (absence) and "what's on disk" (absence). A file that is
staged as added/modified/renamed but has since been deleted from the working tree (a different, narrower
case than a staged deletion) is flagged separately as "staged but missing from the working tree", since
comparing to a nonexistent file isn't a hash question.

Also changed: staged-path enumeration switched from `git diff --cached --name-only` (newline-delimited) to
`--name-only -z` (NUL-delimited) into a bash array. Plain `--name-only` C-quotes any path containing a space
... no, containing non-ASCII bytes (`"queue/review/caf\303\251-t\303\253st.md"`), which breaks `git show
":$f"` / `git rev-parse ":$f"` / `git hash-object -- "$f"` for that literal quoted string. This was a
pre-existing latent bug in the CRLF and secret checks too (untested before, since no case in this repo had
hit it); fixing enumeration for the new check fixes it for all four. The CRLF/secret checks' own logic
(`git show ":$f"`, i.e. the staged blob) is unchanged.

### RED - reproduce today's bug (scratch branch `scratch/T-0047-red`, deleted after)

Branched from `bb31ecf` (pre-fix). Seeded `queue/review/T-9999-scratch-red-test.md` with `state: review`,
committed as baseline (`0245b94`).

    $ git mv queue/review/T-9999-scratch-red-test.md queue/done/T-9999-scratch-red-test.md
    $ git status --short
    R  queue/review/T-9999-scratch-red-test.md -> queue/done/T-9999-scratch-red-test.md

    # edit queue/done/T-9999-scratch-red-test.md: state: review -> state: done, append a review-log line

    $ git status --short
    RM queue/review/T-9999-scratch-red-test.md -> queue/done/T-9999-scratch-red-test.md

    # no re-add - commit directly, exactly the "edit came after the mv, was never staged" shape

    $ git commit -m "scratch: T-9999 review complete, mark done (RED repro)"
    [scratch/T-0047-red 265f0f8] scratch: T-9999 review complete, mark done (RED repro...)
     1 file changed, 0 insertions(+), 0 deletions(-)
     rename queue/{review => done}/T-9999-scratch-red-test.md (100%)
    EXIT=0

    $ git show HEAD:queue/done/T-9999-scratch-red-test.md
    ---
    state: review          # <-- the OLD value; "done" and the review log never landed
    ---
    ## Log
    - initial

    $ cat queue/done/T-9999-scratch-red-test.md   # working tree, for comparison
    ---
    state: done
    ---
    ## Log
    - initial
    - 2026-09-07T17:00:00Z reviewed and marked done by agent/reviewer-scratch: PASS

Confirmed: today's hook (unmodified) accepted the commit; it landed as a pure rename, 0 insertions, silently
dropping `state: done` and the entire review log - exactly the bug six agents hit.

### GREEN - same sequence after the fix

Same repro, hook fixed (working-tree copy of `.githooks/pre-commit` edited in place on the scratch branch
before committing the fix for real on `task/T-0047`):

    $ git mv queue/review/T-9999-scratch-red-test.md queue/done/T-9999-scratch-red-test.md
    # edit queue/done/T-9999-scratch-red-test.md the same way, no re-add
    $ git commit -m "scratch: T-9999 review complete, mark done (GREEN repro attempt)"
    pre-commit: staged content in queue/done/T-9999-scratch-red-test.md is stale - the working tree changed
    after 'git add'. Fix: git add -- "queue/done/T-9999-scratch-red-test.md" (or re-stage before committing).
    For a deliberate partial stage, set ALLOW_PARTIAL_STAGE=1 or
    ALLOW_PARTIAL_STAGE="queue/done/T-9999-scratch-red-test.md".
    pre-commit: refusing commit
    EXIT=1

Refused, names the exact path, states the fix. Applying the stated fix:

    $ git add queue/done/T-9999-scratch-red-test.md
    $ git commit -m "scratch: T-9999 review complete, mark done (properly staged)"
    [scratch/T-0047-red a1b8874] ... 2 files changed, 9 insertions(+), 8 deletions(-)
    EXIT=0
    $ git show HEAD:queue/done/T-9999-scratch-red-test.md
    ---
    state: done
    ---
    ## Log
    - initial
    - 2026-09-07T17:00:00Z reviewed and marked done by agent/reviewer-scratch: PASS

`state: done` and the review log are in the commit this time.

### GREEN - legitimate cases (all on the same scratch branch unless noted; branch deleted after)

1. **Normal fully-staged commit** - shown above (properly staged case): passes, content lands. PASS.

2. **Staged deletion (no working-tree file)**: `git rm queue/done/T-9999-scratch-red-test.md; git commit`
   -> `[scratch/T-0047-red 9c6355e] ... 1 file changed, 9 deletions(-)`, EXIT=0. `--diff-filter=ACMR` excludes
   `D`, so the deletion never reaches the new check. PASS.

3. **CRLF-on-Windows-disk, LF-normalized-staged blob** (the case the brief called out as highest-risk):
   wrote `queue/review/T-9998-crlf-case.md` with raw `\r\n` line endings, `git add`ed it.
   `git show ":..."` (staged) was LF-only; raw working-tree bytes were still CRLF (confirmed via `xxd`, and
   git's own "CRLF will be replaced by LF" warning on add). `git rev-parse ":$f"` = `git hash-object -- "$f"`
   (both computed and compared directly - equal). Committed clean:
   `[scratch/T-0047-red 489a57d] ... 1 file changed, 6 insertions(+)`, EXIT=0. Neither the new stale-content
   check nor the CRLF check false-fired. PASS - this is the case that would "block all work on this machine"
   if gotten wrong, and it didn't.

   3f. **Deliberate partial stage, blanket** - staged T-9998, edited further without re-adding, committed
   with `ALLOW_PARTIAL_STAGE=1`:
   `pre-commit: ALLOW_PARTIAL_STAGE waives the stale-content check for: queue/done/T-9998-crlf-case.md`
   `[scratch/T-0047-red 3a236cf] ...`, EXIT=0. `git show HEAD:...` confirmed the OLDER (staged) content
   landed, as intended for a partial stage. PASS.

   3g. **Deliberate partial stage, path-scoped** - same setup, `ALLOW_PARTIAL_STAGE=<the wrong path>`:
   still refused with the normal stale-content message, EXIT=1 (confirms the scoped form doesn't leak into
   unrelated paths). Then `ALLOW_PARTIAL_STAGE=queue/done/T-9998-crlf-case.md` (the correct path): waived,
   committed, EXIT=0. PASS both directions. (Caught and fixed a real bug here first: the initial
   comma/colon-splitting via `tr ',:' '\0\0'` piped into `read -r -d ''` silently dropped a single-path value
   with no delimiter at all, because `read -d ''` discards an unterminated final record - `count=0` on a
   direct test. Fixed by appending a trailing `,` before the `tr`, guaranteeing a delimiter after the last
   entry; re-tested and confirmed both single-path and multi-path (`a,b:c` -> 3 entries) parse correctly.)

4. **Staged-add then deleted from working tree (distinct from case 2)**: `git add` a new file, then `rm` it
   off disk before committing. Result:
   `pre-commit: queue/review/T-9997-will-be-deleted.md is staged but missing from the working tree (deleted
   after 'git add'). Fix: git add -- "..." to stage the deletion, or restore the file. ...`, EXIT=1. PASS -
   flagged distinctly from a clean staged deletion, as it should be (the author staged *content* that no
   longer exists to be reviewed).

5. **Binary file, unchanged**: staged a small PNG-header-like binary blob (containing literal `\r\n` bytes
   in the magic number, deliberately, to also probe the CRLF check), committed unchanged: EXIT=0, content
   verified via `git show HEAD:... | xxd` to match exactly. The CRLF check did not false-fire because `grep
   -qI` correctly treats the NUL-containing blob as binary and skips it - unaffected by this change (same
   `git show ":$f" | grep -qI` as before).

6. **Binary file, staged then modified**: same file, staged, then working tree overwritten with different
   bytes before commit: `pre-commit: staged content in queue/review/T-9992-real-binary.png is stale ...`,
   EXIT=1. PASS - proves the check isn't text-only; `git hash-object` handles binary content identically to
   `git add`.

7. **Path with spaces**: `queue/review/bin test.png` - `git diff --cached --name-only --diff-filter=ACMR -z`
   (unquoted, unlike the default) enumerated it correctly; `git rev-parse`/`git hash-object` on the exact
   string worked; staged-then-modified was correctly flagged stale.

8. **Path with non-ASCII**: `queue/review/café-tëst.md` - confirmed `git diff --cached --name-only
   --diff-filter=ACMR` (no `-z`) C-quotes this as `"queue/review/caf\303\251-t\303\253st.md"` (a literal
   backslash-escaped string, unusable as a pathspec), while `-z` gives the clean unquoted UTF-8 path. This is
   why enumeration was switched to `-z`; without it, the new check (and, latently, the existing CRLF/secret
   checks) would break on any non-ASCII filename in this repo (queue files are agent-titled and could
   plausibly contain one).

9. **Pure `git mv`, zero content edit** (the "am I over-blocking renames" check): `git mv` a queue file with
   no follow-up edit at all, commit directly:
   `[task/T-9993 3b3d07d] ... 1 file changed, 0 insertions(+), 0 deletions(-), rename ...`, EXIT=0. This
   confirms the check is precise - it does not treat "0 insertions" itself as suspicious, only an actual
   staged-vs-working-tree object-id mismatch. A legitimate content-free rename is not the bug and is not
   blocked.

10. **Symlink** - could not be tested directly: this Windows checkout has `core.symlinks=false` and no
    symlink privilege (`ln -s` and Python `os.symlink` both failed/fell back to a plain file containing the
    target-path text - confirmed via `ls -la`/exception message). Reasoning instead of an empirical result:
    (a) with `core.symlinks=false`, a "symlink" is, to git, an ordinary small text file whose content is the
    target path - already covered by the plain-file path of this check, tested above. (b) On a checkout
    with real symlink support (WSL2/Linux, which this repo explicitly targets per `.gitattributes`'
    comment), `git hash-object` on a symlink path uses the same lstat-based content hashing `git add`/
    `update-index` use for staging symlinks (mode 120000, content = link target text) - it does not follow
    the link and hash the referent's content. This is standard, documented git behavior, not something this
    change alters. Flagged here rather than silently assumed: a WSL2/Linux agent should re-run case 10 for
    real once this PR is reviewed, since it's the one case I could not exercise on this machine.

### GREEN - other hook checks still fire (regression, on `task/T-9993` for a `touches:`-scoped branch)

- **CRLF check**: `git show ":$f" | grep -qI "$CR"` is unchanged, but discovered along the way that this
  build of grep (Git for Windows' bundled grep, this machine) silently fails to match a literal `\r`
  immediately followed by `\n` when read via a pipe or file - `printf 'a\r\nb\n' | grep -c $'\r'` -> 0
  matches, while `printf 'a\rb\n' | grep -c $'\r'` -> 1 match. Confirmed this is a pre-existing environment
  quirk, not a regression from this change, by running the identical `grep -qI` invocation with both the old
  and new hook logic side by side - both behave identically for both inputs. Demonstrated the check firing
  with a lone-CR file (`queue/review/T-9995-lonecrlf.png`, `.png` chosen so `.gitattributes`' `binary`
  attribute exempts it from LF-normalization on add, so working tree == staged blob and only the CRLF check
  is under test): `pre-commit: CRLF in queue/review/T-9995-lonecrlf.png (repo is LF-only, see
  .gitattributes)`, EXIT=1. PASS - check fires, unaffected by this change. (The `\r\n`-specific grep
  behavior is a separate, pre-existing, environment-specific gap worth its own task if it matters in
  practice - CRLF virtually never reaches a staged blob in this repo since `.gitattributes`' `text=auto
  eol=lf` normalizes it away at `git add` time for every non-`binary`-attributed path; not touched here as
  out of scope for T-0047.)
- **Secret check**: staged `queue/review/T-9994-secret-test.md` containing a fake `sk.`-prefixed 24-char
  token (elided here so this log line doesn't itself trip the same check):
  `pre-commit: secret-looking content in queue/review/T-9994-secret-test.md`, EXIT=1. PASS.
- **touches: enforcement (T-0039's fix)**: created `task/T-9993` with a task file whose `touches:` was
  `[ops/some-fake-file.txt]`, staged `apps/ios/OUTSIDE-TOUCHES-TEST.md`:
  `pre-commit: apps/ios/OUTSIDE-TOUCHES-TEST.md is outside T-9993 touches: [ops/some-fake-file.txt ]`,
  EXIT=1. PASS - T-0039's check still fires with the array-based enumeration.

### Cleanup

`scratch/T-0047-red` and `task/T-9993` (and all scratch files created on them: `T-999[2-9]-*`,
`café-tëst.md`, `crlf-test.md`, `OUTSIDE-TOUCHES-TEST.md`) existed only on those two scratch branches, which
were `git branch -D`-deleted after the fix was verified and reapplied fresh on `task/T-0047`. `git status`
and `git branch --list 'scratch/*' 'task/T-9993'` both confirm nothing remains.

### Real fix, committed for real

    $ git add .githooks/pre-commit
    $ git commit -m "T-0047: pre-commit refuses staged content that is stale relative to the working tree" ...
    [task/T-0047 a137685] ... 1 file changed, 80 insertions(+), 11 deletions(-)
    $ git show HEAD:.githooks/pre-commit | diff - .githooks/pre-commit
    (no output - committed content == working tree content)

The one check this whole task exists to teach the hook to make - I ran it on myself.

- 2026-09-07T18:05:00Z agent/reviewer-28: **FAIL.** Re-derived the RED/GREEN claims, the false-positive
  hunt, the `-z` regression check, and the `ALLOW_PARTIAL_STAGE` hardening independently (all confirmed
  as claimed). Found one new, reproducible false positive on the one case the owner flagged as untested:
  symlinks on a real symlink-capable filesystem. Full account below.

### What I re-derived vs. took on trust

Re-derived independently, on my own scratch branches/files (all deleted after):
- RED: swapped in `HEAD~2:.githooks/pre-commit` (old hook, via `-c core.hooksPath` unnecessary since
  `core.hooksPath=.githooks` is already repo-wide), reproduced `git mv` + edit + no-re-add, got a clean
  0-insertion rename commit with the OLD `state:`/log content landing and the new content silently lost.
  Confirmed with the NEW hook the identical sequence refuses with the documented message and fix.
- False-positive hunt (all against the real, committed `.githooks/pre-commit` on this branch): CRLF-on-disk
  vs. LF-normalized-staged-blob (PASS, oids equal, confirmed via `git rev-parse`/`git hash-object` compared
  directly plus a full commit), no-trailing-newline (PASS), binary file with a space in the name - both
  unmodified (PASS) and modified-after-add (correctly REFUSED) (space preserved verbatim in the message),
  non-ASCII filename `café-tëst.md` - both unmodified (PASS) and modified-after-add (correctly REFUSED,
  path printed unquoted and readable), staged deletion via `git rm` (PASS, `--diff-filter=ACMR` excludes
  `D` as claimed), staged-add-then-deleted-from-disk (correctly REFUSED with the distinct "staged but
  missing" message, not conflated with the stale-content message), staged-then-chmod-444/read-only with
  unmodified content (PASS - the check is content-hash based, not mtime/permission based), and a pure
  `git mv` with zero content edit (PASS, 0 insertions is not itself flagged). No `.gitattributes` filter=
  clauses exist in this repo to test (only `text=auto eol=lf` and `binary`), and there are no submodules
  (`.gitmodules` absent) - both confirmed absent rather than assumed.
- `-z` regression check on the other three checks: staged three files in one commit (a clean file, a file
  with real `\r\n` content, and `"queue/review/T-8880 has secret.md"` with a space in the name) - the
  secret check fired and named the space-file correctly. Separately confirmed the `touches:` check (T-0039)
  fires on the correct out-of-scope path even when a space-named path is staged alongside an in-scope one,
  under the new `-z`/array enumeration.
  - **Caveat surfaced, not a T-0047 regression**: the CRLF check did not fire on the `\r\n` file in that
    test. Traced this to `.gitattributes`' `* text=auto eol=lf`, which normalizes CRLF to LF **at `git add`
    time**, before the hook ever runs - the staged blob for that file has zero `0x0d` bytes (verified via
    `git show :<path> | xxd`), so `grep -qI "$CR"` on the staged blob has nothing to find regardless of the
    grep-pipe quirk the builder's log separately describes. Confirmed this is pre-existing and NOT caused by
    the `-z` switch or this task by swapping in the OLD hook and running the identical scenario: same result,
    CRLF check silent. Net effect (not new, but worth flagging since nobody had stated it this plainly): the
    CRLF check (`.githooks/pre-commit`, the `grep -qI "$CR"` line under `# 1. CRLF`) can in practice only
    ever fire on a `binary`-attributed path containing a lone `\r` not immediately followed by `\n` - it is
    effectively dead code for the CRLF-line-ending case it appears to guard against, because
    `.gitattributes` already scrubs that case before staging. Out of scope for T-0047 (logic unchanged), not
    a blocker, but worth its own task if the CRLF check's real purpose matters.
  - `ALLOW_PARTIAL_STAGE` escape hatch: confirmed exact-path matching, not prefix/glob - `ALLOW_PARTIAL_STAGE=.`,
    `=` (empty), `=queue/review` (directory prefix, no wildcard), and a wrong sibling path all still refuse
    the real stale file; only the exact path waives it. Confirmed quoting the variable inside `[[ "$f" == "$a" ]]`
    (`.githooks/pre-commit` line ~96/101) suppresses glob interpretation in bash, so `ALLOW_PARTIAL_STAGE='*'`
    would not wildcard-match every path either (checked with a standalone bash snippet, not just read). Confirmed
    a path named in the allow-list that is NOT actually stale is a silent no-op (no message, normal commit).
    Confirmed a multi-file commit with only one of two stale files named in the scoped list waives exactly
    that one and still refuses on the other. Confirmed the waived commit lands the *older, staged* content, as
    intended for a deliberate partial stage.
- `git diff HEAD~1 --stat` / `HEAD~2..HEAD --stat`: touches only `.githooks/pre-commit` and the task file
  (state moved review->review with the red/green log, per `6e374e1`). `git ls-files -s .githooks/pre-commit`:
  mode `100755`, confirmed (not just trusted from the commit message).

Took on trust: nothing load-bearing. I did not re-verify the builder's `read -d ''` trailing-comma fix
line-by-line (re-derived its *behavior* instead, above, which is the part that matters).

### FINDING 1 - HIGH - symlinks: confirmed false positive, contradicts the builder's own untested claim

`.githooks/pre-commit:77` (`working_oid="$(git hash-object -- "$f" ...)"`) compared against the staged oid
at line 71 (`git rev-parse ":$f"`). The builder's log (case 10) reasoned that `git hash-object` on a symlink
path uses "the same lstat-based content hashing `git add`/`update-index` use for staging symlinks... it does
not follow the link and hash the referent's content" and flagged this as untested on Windows, asking a
WSL2/Linux agent to verify for real. I did, via `wsl.exe`, on a fresh clone of `task/T-0047`
(`core.hooksPath` set explicitly since it's a separate clone; `core.symlinks` unset/true, real symlink
support confirmed via `ls -la`).

**The claim is backwards.** `git hash-object -- <path>` does *not* lstat/readlink the path - it opens it
through the normal filesystem path, which follows the symlink and hashes the **target file's content**.
`git add` / the staged blob, by contrast, holds the symlink's own text (the link-target string, mode
`120000`). These two are different objects for any symlink, by construction - not just when the symlink
"changes."

Repro (target file `queue/review/T-7002-target-a.md` containing `target file A\n`; symlink
`queue/review/T-7002-link.md` -> `T-7002-target-a.md`, `git add`ed and then **left completely untouched**):

    $ staged=$(git rev-parse :queue/review/T-7002-link.md)     # afc2f4f...  (the symlink's own text)
    $ working=$(git hash-object -- queue/review/T-7002-link.md) # 2950110...  (the TARGET FILE's content)
    $ [ "$staged" = "$working" ] && echo MATCH || echo MISMATCH
    MISMATCH -> FALSE POSITIVE CONFIRMED

    $ git commit -m "scratch(wsl): symlink committed unmodified, expect PASS"
    pre-commit: staged content in queue/review/T-7002-link.md is stale - the working tree changed after
    'git add'. Fix: git add -- "queue/review/T-7002-link.md" (or re-stage before committing). ...
    pre-commit: refusing commit

**Concrete failure scenario**: any agent (this repo is explicitly operated from Windows, WSL2, and Linux CI
per `.gitattributes`' own header comment - WSL2/Linux is not a hypothetical environment here) that stages
a symlink and commits it - even with zero edits since `git add`, even on a second, later, completely
unrelated commit that merely re-touches the same tree - gets refused every single time, forever, with a
message telling them to `git add -- <path>` (which does nothing: re-adding restages the same symlink text,
`git hash-object` still dereferences and still mismatches) or fall back to `ALLOW_PARTIAL_STAGE`, which per
the check's own design is supposed to be reserved for genuinely deliberate partial stages, not routine
symlink commits. This isn't an edge case that requires a coincidence to trigger; it fires unconditionally
for every symlink on any real symlink-capable filesystem. `-e "$f"`/`-L "$f"` at line 73 correctly avoids
misclassifying a symlink as "missing," so the missing-file branch is fine - the bug is specifically the
`hash-object`-dereferences-vs-`rev-parse`-stores-link-text mismatch at lines 71/77.

Currently latent: `git ls-tree -r HEAD | awk '$1==120000'` returns zero rows (no symlinks tracked today),
and no `ops/*` script creates one. So this does not "stop the whole fleet" today the way a CRLF false
positive would have. But it is a real, always-reproducible defect in the shipped check, on an environment
the repo explicitly supports, on the exact point the owner flagged as unverified - which is why I'm calling
it a FAIL rather than a follow-up task. A fix needs to compare the symlink's own text (e.g. `readlink -- "$f"`
against `git cat-file -p "$staged_oid"`) rather than `git hash-object -- "$f"` for any path where `-L "$f"`
is true.

### Verification output (fresh worktree, `services/api` deps not yet installed until I ran the T-0040 gap step)

    $ bash ops/check-pins
    PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
    EXIT=0

    $ bash ops/queue-check
    QUEUE OK (43 tasks)
    EXIT=0

    $ cd services/api && npm ci --no-audit --no-fund
    added 85 packages in 12s

    $ bash ops/test
    ...
    TESTS linux=50/50 ios=skipped failed=0 skipped=0
    OK
    EXIT=0

All three green. The FAIL verdict is solely on Finding 1 (symlink false positive), not on these.

### Cleanup

Scratch branches `scratch/reviewer28-red` (Windows worktree) and the WSL clone at `~/t0047-symlink-test`
were both deleted after use; `git branch --list 'scratch/*'` and `git status --short` on `task/T-0047`
confirm nothing remains. No `task/T-8879` scratch branch remains either (deleted).
