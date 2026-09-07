---
id: T-0058
title: the 300-line cap is enforced only on Swift, not Python or TypeScript
state: review
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-07T22:34:40Z
lease_expires_at: 2026-09-08T00:34:40Z
worktree: null
branch: task/T-0058
exclusive: []
touches: [ops/lib/check-line-cap, pins/PINS.yaml]
pins_affected: []
reviewer: agent/reviewer-44
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

CLAUDE.md states the rule without qualification:

    One type per file, filename == type name, **300-line cap**.

`ops/lib/check-line-cap` (P-SRC-02) enforces it over `git ls-files '*.swift'` and nothing else. Python,
TypeScript and shell are unenforced, and that is where most of the code now lives - the Swift tree is a
skeleton while `services/etl/etl/` and `services/api/src/` are where every M2 task is working.

Found by agent/reviewer-33 while reviewing T-0028, whose `byways.py` sits at **296 lines** - four short of a
cap that would not have stopped it anyway. That is the shape of the problem: the file that is closest to
breaking the rule is in the language the rule is not checked in, and nobody would have known.

- Extend the check to the languages the repo actually writes. At minimum `*.py` and `*.ts`; decide about
  shell, where `ops/*` scripts are legitimately long and mostly comment, and say what you decided.
- Measure the tree FIRST and put the numbers in the log before changing anything. If files already exceed the
  cap, that is a finding about the cap or about those files, and it has to be settled before the check can go
  green - do not quietly raise the limit to whatever the current maximum happens to be, and do not split a
  file solely to satisfy a number.
- The existing coverage guard is the interesting part to copy correctly, not the line count: P-SRC-02 already
  refuses to pass vacuously over an empty or renamed tree (`MIN_FILES`, and a per-package check that a
  package contributing only a manifest is caught). Whatever set you add needs the same, or it will pass
  cheerfully on the day somebody moves `services/etl` and nothing matches the glob.
- Demonstrate red per language: a >300-line file of each kind, shown passing before and failing after, naming
  the file.
- Note that `--source-only` mode exists for the push gate; keep the added work inside it only if it is fast.

Related and already filed: T-0043 (the coverage guard does not recognise `Package@swift-6.0.swift`) touches
the same script. Whichever lands first, the other rebases.

## Log
- 2026-09-07T22:34:40Z claimed by agent/unknown; lease until 2026-09-08T00:34:40Z

- 2026-09-08T06:20Z claimed and implemented by agent/claude-opus-5, stacked on task/T-0043, which is the
  other live edit to this file.

  **Measured first, as the brief demanded, before changing anything.** Across the branches that will merge,
  every tracked `.py` and `.ts` over 250 lines:

      ops/lib/queue.py                    498   (372 before T-0032 added the review transition)
      services/etl/etl/byways.py          296
      services/etl/tests/test_byways.py   282
      services/etl/tests/test_curvature.py 274

  So exactly ONE file exceeds 300, and it is not close: `ops/lib/queue.py`. Nothing in `services/api/src/`
  comes near. That single fact decided the design.

  **The design, and it is the whole judgement in this task.** Turning the cap on for Python today fails
  immediately on `queue.py`, and splitting the queue's core is T-0059's job, not this one's. The two obvious
  options are both bad: leave the cap off for all Python until a refactor lands - which is the status quo that
  let byways.py reach 296 unnoticed - or quietly raise the limit to whatever the current maximum happens to
  be, which the brief explicitly forbids.

  So: an EXEMPTION LIST, with two rules that stop it rotting.

    - an entry with no task id is refused, so nobody adds one without saying who removes it;
    - an entry whose file is now UNDER the cap is refused as STALE, so a fixed file cannot keep its licence.

  One entry today, `ops/lib/queue.py` -> `T-0059`. Adding a name is a visible diff on a load-bearing check;
  that is the intended cost. This turns the cap on for the ninety-odd files that already comply, now, instead
  of leaving all of them unchecked until one refactor lands.

  **Checks 1 and 2 stay Swift-only, deliberately.** `MIN_FILES` and the package coverage guard assert things
  about the Swift PACKAGE layout - that a package exists and contributes files. There is no equivalent
  structure to assert for a directory of Python modules, and inventing one would be a check that passes
  because it means nothing.

  **Five demonstrations:**

      1. a 400-line Python file       OLD exit=0 "none over 300 lines"   NEW exit=1, names it
      2. a 400-line TypeScript file   OLD exit=0                          NEW exit=1, names it
      3. exemption with no task id    refused: "'because it is long' is not a task id"
      4. stale exemption              refused: "junit_count.py (48 lines, exempt for T-0059)"
      5. the real exemption           honoured: "10 Swift files, 20 source files under the cap, 1 exempt"

  3 and 4 matter as much as 1 and 2. An exemption mechanism nobody can audit is just a higher cap.

  **Cost, measured rather than asserted.** `ops/lib/check-line-cap` alone: 1.387s before, 2.814s after - about
  +1.4s for ten more files, and it is linear, because the loop spawns one `awk` per file and process creation
  on this Windows box is slow. `ops/check-pins --source-only`, the push gate, takes 1m39s in total, so this is
  not where that time goes.

  I did NOT optimise it, and that is a choice worth arguing with. One `awk` pass over all files would fix it,
  but `ENDFILE` is a gawk extension and the pinned Linux image may have mawk, so the portable version is a
  hand-rolled `FNR==1 && NR>1` counter with an empty-file edge case that silently skips a file. Trading a
  subtle correctness risk in a load-bearing check for 1.4s is exactly the bargain this repo keeps losing. If
  the file count grows enough to matter, do it then, with a test for the empty-file case.

  **Verification:** `ops/lib/check-line-cap` -> `P-SRC-02: 10 Swift files, 20 source files under the cap, 1
  exempt`; `ops/check-pins` -> `PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux`;
  `ops/check-pins --source-only` -> `PINS ok=3 skipped=8 pending=1 expired=0 failed=0`; `ops/queue-check` ->
  `QUEUE OK (35 tasks)`. check-line-cap is 121 lines. GitHub Actions is DISABLED repo-wide (T-0053), so there
  is no CI signal at all.

  **What to attack.** The exemption list is a bash associative array in the check itself, so it is invisible
  to anything that reads `pins/PINS.yaml` - a reader auditing the pins cannot see that one file is excused.
  Whether that belongs in the pin's data instead is a fair argument and I did not make it. Second: the stale
  rule keys on the file being under 300, so an exempt file that is deleted entirely just disappears from the
  list's reach without complaint. Third: `grep -v '/node_modules/'` is a blunt exclusion that would also hide
  a genuine source file with that string in its path.
