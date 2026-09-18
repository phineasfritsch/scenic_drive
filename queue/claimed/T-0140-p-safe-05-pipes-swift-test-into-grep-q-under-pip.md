---
id: T-0140
title: P-SAFE-05 pipes swift test into grep -q under pipefail, so a SIGPIPE fails the pin at random
state: claimed
owner: agent/claude-opus-5
owner_session: 014SvHby9PhsKZqo5FkfuP2D
claimed_at: 2026-09-16T09:30:00Z
lease_expires_at: 2026-09-16T15:30:00Z
worktree: .worktrees/T-0140
branch: task/T-0140
exclusive: []
touches: [.githooks/pre-commit, ops/, pins/PINS.yaml]
pins_affected: [P-SAFE-05, P-SEC-01, P-OPS-03]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "python ops/lib/check-secret-scan.py -> five secret sizes refused with the reason, 4096 KB clean committed, staged-blob-object-deleted refused with 'cannot read the staged blob for leak.txt', SECRET-SCAN OK (7 cases), exit 0"
  - "RED: git show ffa9b6c:.githooks/pre-commit > .artifacts/v-hook; python ops/lib/check-secret-scan.py --hook .artifacts/v-hook -> FAIL 256 KB / 1024 KB / 4096 KB secret COMMITTED, FAIL staged blob object deleted (committed), exit 1"
  - "RED (the fail-closed branch): the hook with 'if ! git show ... fi' replaced by 'git show ... || : > \"$blob\"' -> FAIL staged blob object deleted, only; exit 1"
  - "RED (the negative control): the hook's pattern with an empty alternative appended -> FAIL 4096 KB clean must COMMIT, refused; exit 1"
  - "bash ops/lib/check-pipe-consumers -> PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (42 scanned, 42 tracked), exit 0"
  - "RED (the scan, at ffa9b6c in a detached worktree with the scan copied in, git add -N) -> 8 PIPE-CONSUMERS: lines, FAIL: 8 pipeline(s), exit 1"
  - "RED (the scan's regex): eleven early-exit spellings in a probe file - grep --quiet, --silent, -E -q, -e PAT -q, egrep -q, fgrep -q, -w -q, -m1, -m 1, -qE, -iq - all 11 match; 'grep p >/dev/null', 'grep -c p', 'grep -E p | sort' do not"
  - "RED (the scan's population): the tree with .githooks dropped from both path lists tracks 40, not 42 -> PIPE-CONSUMERS REFUSING: 40 tracked file(s), EXPECTED_TRACKED says 42, exit 2. An untracked file added under ops/ does NOT refuse: 43 scanned, 42 tracked, exit 0"
  - "mechanism: bash -o pipefail -c \"(echo 'Test run with 20 tests passed'; seq 1 200000) | grep -q passed\" -> exit 141; with 'grep passed >/dev/null' -> exit 0"
  - "python ops/lib/check-touches-merge.py -> TOUCHES-MERGE OK (10 cases), exit 0 - the merge fixture on the changed hook"
  - "bash ops/check-pins -> PINS ok=16 skipped=0 pending=3 expired=0 failed=0 tier=linux, exit 0"
  - "bash ops/queue-check -> QUEUE OK, exit 0"
---
## Brief

Two independent round-6 reviewers reported `bash ops/check-pins` as FLAKY in their worktrees: P-SAFE-05
failed 1 run in 3 on one box, with the pin text and the solar sources byte-identical to `main`, where the
same pipeline passed 3/3. Both diagnosed it the same way and both declined to attribute it to their PR.

The mechanism: P-SAFE-05's assertion ends by piping `swift test --filter SolarFixtureTests` into `grep -qE
'... passed'`, and `ops/lib/pins.py` runs every assertion under `bash -o pipefail`. `grep -q` exits at its
FIRST match. If the producer is still writing it gets SIGPIPE and exits 141, and pipefail makes 141 the
pipeline's status. Whether swift has anything left to write after its summary line is a matter of timing,
so the pin's verdict is a race. Deterministic with a chatty producer:

    bash -o pipefail -c "(echo 'Test run with 20 tests passed'; seq 1 200000) | grep -q passed"           -> 141
    bash -o pipefail -c "(echo 'Test run with 20 tests passed'; seq 1 200000) | grep passed >/dev/null"   -> 0

### It is a class, and the worst member is the secret scan

`grep -rn '| grep -q'` over the places a verdict is computed found EIGHT sites, and two of them are in
`.githooks/pre-commit`, under the hook's own `set -uo pipefail`: the CRLF scan and the secret scan, both
`git show ":$f" | grep -q PAT`. There the race is not a flake but a **fail-open with a threshold**. Measured
with the shipped hook, a file carrying an `sk.` token on line 1 and filler after it:

        1 KB  refused             64 KB  refused
      256 KB  COMMITTED, exit 0, nothing printed
     1024 KB  COMMITTED         4096 KB  COMMITTED

Any file larger than the pipe buffer beat the gate CLAUDE.md says "greps for them". `ops/merge:45` is the
same shape on the merge gate itself - a SIGPIPE from `gh api` listing `queue/done/` reads as "task not in
done/" and refuses a merge that should land.

### Do

1. Every gate that decides from a pipeline reads its producer to EOF: `grep PAT >/dev/null`, never `grep -q`.
2. The hook reads each staged blob ONCE into a temp file with `git show`'s exit status checked - a blob
   that cannot be read fails CLOSED - and greps the file, where an early exit costs nothing.
3. `ops/lib/check-secret-scan.py`: five sizes straddling the buffer, each must be REFUSED for the secret
   REASON. Red against the pre-fix hook from git, green after. Pin P-SEC-01.
4. `ops/lib/check-pipe-consumers`: a text scan that refuses any `| grep -q` in `ops/`, `.githooks/` or
   `pins/PINS.yaml`, with a floor on files enumerated. Pin P-OPS-03.

## Log
- 2026-09-16T09:30:00Z claimed by agent/claude-opus-5; worktree `.worktrees/T-0140`, branch `task/T-0140`,
  off `ffa9b6c`. `ops/new-task` allocated **T-9902 for the fourth time** ([[T-0138]], still live); renamed by
  hand. `touches:` widened from `[pins/PINS.yaml, ops/lib/]` to `[.githooks/pre-commit, ops/, pins/PINS.yaml]`
  once the scan showed where the class lived.
- 2026-09-16T10:40:00Z **Fixed as a class. The flake was the small member; the secret scan was the large one.**

  **RED, the flake itself, honestly: not reproduced here.** `.artifacts/sigpipe-probe.py` ran the tail of
  P-SAFE-05 ten times under `bash -o pipefail` exactly as `pins.py` does: `OLD grep -q runs=10 failures=0`.
  The reviewer saw 1 in 3 on a different box. So the flake is stated as the reviewers measured it, not as
  something I watched; what IS shown deterministically is the mechanism, with a producer that keeps
  writing: `| grep -q` -> exit 141 three times of three, `| grep >/dev/null` -> 0 three of three.

  **RED, the secret scan, reproduced and then pinned.** `.artifacts/secret-sigpipe.py` against the shipped
  hook: 1 KB and 64 KB refused, 256 KB / 1 MB / 4 MB **committed with exit 0**. After the fix, all five
  refused. Then the probe became `ops/lib/check-secret-scan.py`, which asserts the REASON printed (a hook
  that refuses everything cannot pass it) and refuses if its own size list is not the five it claims:

      $ git show ffa9b6c:.githooks/pre-commit > .artifacts/prefix-hook   (blob 03b1ac2)
      $ python ops/lib/check-secret-scan.py --hook .artifacts/prefix-hook
        ok    1 KB   ok   64 KB   FAIL 256 KB COMMITTED   FAIL 1024 KB   FAIL 4096 KB
        SECRET-SCAN FAIL (5 sizes)                                                      exit 1
      $ python ops/lib/check-secret-scan.py
        SECRET-SCAN OK (5 sizes)                                                        exit 0

  **RED, the class.** `bash ops/lib/check-pipe-consumers` against the tree before the edits: 8 hits
  (`.githooks/pre-commit:18` and `:27`, `ops/deploy:12`, `ops/lib/check-failure-naming:76-77`,
  `ops/merge:45`, `ops/sane:41`, `pins/PINS.yaml:123`), `PIPE-CONSUMERS FAIL: 8 pipeline(s)`, exit 1.
  GREEN after: `PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (41 files scanned)`, exit 0.
  Its first green was false: the scan caught the prose of the new pin, which quoted the shape it forbids.
  The prose was reworded rather than the scan taught to skip YAML - an exclusion for "lines that describe
  the pattern" is an exclusion an assertion line can be worded into.

  **The hook change is the one that matters.** Each staged blob is now read once into a temp file with
  `git show`'s own exit status checked - "could not look" fails CLOSED, never reads as "nothing there" -
  and both greps run on the file. `ops/lib/check-touches-merge.py` still passes all ten cases on the new
  hook, including case 7 (a secret arriving across a merge), exit 0.

  **VERIFICATION.** `bash ops/check-pins` -> `PINS ok=16 skipped=0 pending=3 expired=0 failed=0 tier=linux`,
  exit 0 (14 on `main`; P-SEC-01 and P-OPS-03 are the two). Its first run said `failed=1 - P-OPS-02:
  duplicate id` - I had numbered the new pin over an existing one, and the gate caught it; renumbered.
  `bash ops/queue-check` -> `QUEUE OK`, exit 0.

  **Not changed, named.** The remaining `| head -N` pipelines in `ops/sane` and `ops/agent-preflight` sit
  inside `$( )` for DISPLAY and no verdict reads their status; they are the same mechanism but not the same
  defect, and the scan is deliberately narrow to the pattern that decides. P-SAFE-05 still runs `swift
  test` without `--scratch-path`, against CLAUDE.md's rule for shared boxes - pre-existing, not this task.
- 2026-09-16T10:55:00Z The first commit of this fix was REFUSED by the hook it fixes: `pre-commit:
  secret-looking content in ops/lib/check-secret-scan.py`. The check's fixture token was one literal, and
  the fixed hook - now reading the whole blob - found it. It is assembled at run time now (`"sk." + "..."`),
  the way `check-touches-merge.py`'s case 7 already does. Recorded because a gate refusing its own author
  is the behaviour this repository pays for, and because the previous hook would have let a 1 KB file
  through only by luck of size.
- 2026-09-16T15:40:00Z **CI failed this PR on its own lint, and the reason is the lesson.** `PIPE-CONSUMERS
  FAIL: 2 pipeline(s)` - both hits in the DOCSTRING of `ops/lib/check-secret-scan.py`, which quoted the
  shape it exists to describe. Locally the scan had printed OK over 41 files, because it enumerated with
  plain `git ls-files` and `check-secret-scan.py` was still UNTRACKED when I ran it: the check saw every file
  except the one being written. CI, where the file was tracked, saw it. The right way round, and still a
  gap. The scope is now `git ls-files --cached --others --exclude-standard` - what git knows or would add,
  ignored paths still out - so a new file is scanned before it is committed; 42 files now. The docstring is
  reworded, as the pin's prose was, rather than the scan taught to skip docstrings.
- 2026-09-17T01:30:00Z **ROUND 2 - agent/claude-opus-5, owner, answering agent/rv-pr87's FAIL.** All three
  blocking reproduced; the two non-blocking that were code are closed too.

  **BLOCKING 2 - the regex claimed a class and matched a spelling.** `-[A-Za-z]*q` directly after `grep`
  caught `-q`, `-qE`, `-iq` and nothing else: `grep -E -q`, `grep -e PAT -q`, `grep --quiet`, `--silent`,
  `egrep -q`, `fgrep -q`, `-m1` all passed the scan and each measured exit 141 under the chatty producer.
  P-OPS-03's statement said "every such pipeline". The regex now matches grep/egrep/fgrep followed anywhere
  on the line by a short group containing q, `--quiet`, `--silent` or `-m<N>`. Probe: eleven early-exit
  spellings all match; `grep p >/dev/null`, `grep -c p`, `grep -E p | sort` do not.

  **BLOCKING 3 - `MIN_FILES=20` over 42 files.** Dropping `.githooks` from the path list scanned 40 and
  printed OK with both original hook sites back in the tree. `EXPECTED_FILES=42`, an equality: the same
  edit now prints `REFUSING: scanned 40 files, EXPECTED_FILES says 42`, exit 2.

  **BLOCKING 1** - acceptance line 3 quoted 41 files after the 15:40 entry had said 42. Rewritten; every
  acceptance line re-run at this head.

  **NON-BLOCKING 4 and 5 - closed in the check, not in prose.** The hook's fail-CLOSED branch was claimed in
  four places and exercised by nothing; a seventh case deletes the staged blob's loose object and requires
  `cannot read the staged blob for leak.txt`. And "a hook that refuses everything cannot pass it" was not
  true of this check - an empty alternative in the pattern refused every size WITH the secret reason - so a
  sixth case stages a CLEAN 4096 KB file and requires it to COMMIT. RED, each on a copy of the hook:

      fail-open on unreadable (|| : > "$blob")   -> FAIL staged blob object deleted, only        exit 1
      refuses everything (empty alternative)     -> FAIL 4096 KB clean must COMMIT, only         exit 1
      pre-fix hook from git (ffa9b6c)            -> FAIL 256 KB, 1024 KB, 4096 KB secret COMMITTED,
                                                    and FAIL staged blob object deleted          exit 1

  That last line is new information: the pre-fix hook was fail-open on an unreadable blob too, not only on
  a large one. `SECRET-SCAN OK (7 cases)`, `EXPECTED_CASES = 7`.

  **NON-BLOCKING 6** - a staged submodule (mode 160000) would have been refused by the fail-closed branch;
  gitlinks are skipped explicitly now, read from the index, with the reason in the hook. No `.gitmodules`
  exists today.

  **One process note.** Between two runs I typed `git checkout -- ops/lib/check-pipe-consumers` to undo a
  probe edit and reverted my own uncommitted widening with it; the next gate run printed OK over the old
  regex. Caught by grepping for the new constant before committing rather than by the output, which is the
  only way that class is ever caught.
- 2026-09-18T00:20:00Z **CI failed this PR a second time, on the equality I had just added.**
  `PIPE-CONSUMERS REFUSING: scanned 44 files, EXPECTED_FILES says 42`. Locally both enumerations return 42;
  on the runner, after the earlier steps had run, two untracked-but-unignored files existed under those
  paths. So the number I asserted was a fact about MY DISK, not about the commit - the same class as
  everything else this task has been about, one level up: a population claim that moves with the machine is
  not a population claim.

  The two jobs the one number was doing are now split. SCANNED stays tracked + untracked-unignored, because
  that is why `--others` is here at all - it is what makes a file scanned before it is committed, which the
  first CI failure taught. COUNTED is what git TRACKS, which is the same wherever the commit is. Measured
  both ways: an untracked file added under `ops/` -> `43 scanned, 42 tracked`, exit 0; `.githooks` dropped
  from the path lists -> `40 tracked file(s), EXPECTED_TRACKED says 42`, exit 2. A second guard refuses a
  scan smaller than the tracked set, so the two cannot drift apart silently.
