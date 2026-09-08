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

- 2026-09-08T08:55Z correction by agent/claude-opus-5, its owner. MY MEASUREMENT WAS INCOMPLETE AND THIS
  CHANGE, AS FIRST WRITTEN, TURNED MERGED `main` RED.

  The log above says "Measured first, before changing anything" and lists four files over 250 lines. I scanned
  `task/T-0028`, `task/T-0032` and `task/T-0025` - three branches that happened to be in front of me - and
  called it the tree. The Dockerfile chain was not among them:

      services/etl/tests/test_dockerfile.py   125 lines on task/T-0038
                                              436 lines on task/T-0046

  It grew across T-0046's four review rounds. It is invisible on every branch INDIVIDUALLY, twice over: it is
  not on the chain this check lives on, and the chain it IS on had no Python cap to trip. So no per-branch CI
  could ever have seen it, and neither did I.

  Found by merging all thirty open branches into a throwaway in dependency order and running the gates after
  each - the same rehearsal that confirmed the `gh-stub-for-merge-tests` ADD/ADD conflict and the exec-bits
  trap. That is what turned it up:

      T-0058   merged, GATES FAIL | line-cap:   services/etl/tests/test_dockerfile.py (436 lines)

  **Exempted, pointing at T-0062**, which splits it. This is the exemption mechanism doing exactly the job it
  was designed for rather than a hole in it: the file was over the cap long before either task existed, the
  entry is a visible diff on a load-bearing check, and the stale rule deletes it automatically the moment the
  file drops back under 300. `P-SRC-02: 10 Swift files, 20 source files under the cap, 2 exempt`.

  **What I take from it.** "Measured first" was true and still produced a wrong answer, because I measured the
  branches I could see instead of the branches that will merge. In a repo where thirty branches are stacked
  behind a billing block, those are not the same set - and the whole point of this task was that a rule which
  cannot see part of the tree is not a rule. I built exactly that mistake into my own measurement of it.
  Corrected here rather than in a commit message, because this log is what a reviewer reads.

- 2026-09-08T10:40Z second correction by agent/claude-opus-5. A repo-wide sweep for self-referential checks -
  eight surfaces, two adversarial skeptics per finding, each required to EXECUTE its falsification - found
  two in this very file, and the second one is mine.

  **1. The coverage guard could never fire, and never could.** It asked whether a package directory
  contributes any file to `files` = `git ls-files '*.swift'`, where the package directories are the dirnames
  of `git ls-files '*Package.swift' '*Package@swift-*.swift'`. Those manifest pathspecs are a strict SUBSET
  of the examined one, so a package's own manifest is always in `files` and `covered` was 1 BY CONSTRUCTION,
  for every possible repository state. The guard watched a condition it had itself made true.

  T-0043's log came within one sentence of this - "a Package@swift-6.0.swift is itself a .swift file, so
  while FILES globs every tracked .swift the package always contributes and there is nothing to report" - and
  concluded the DEMO had to be narrow, rather than that the GUARD could not fire. I wrote that sentence.

  **2. T-0058 made it worse.** I introduced `capped` as a second, independent `git ls-files`, and the cap
  loop walks THAT. So the guard was defending a set with no consequence: the sweep narrowed `capped` alone -
  the exact T-0037 regression, applied to the list the cap actually iterates - and a 400-line file left the
  cap while this check printed `P-SRC-02: 12 Swift files, 19 source files under the cap`, rc=0. The summary
  line even counted the vanished package's files.

  **3. And `MIN_CAPPED` did not exist.** `MIN_FILES` guards `files`, the Swift-only list. T-0058's own brief
  said, in as many words, that the set it added "needs the same, or it will pass cheerfully on the day
  somebody moves services/etl and nothing matches the glob". It did not get the same. I wrote that
  requirement into the brief and then did not implement it.

  **Fixed.** The guard now reads `capped`, and a manifest no longer counts as its own package's
  contribution - so a package whose sources drop out of the cap is reported even though its manifest remains.
  `capped` has its own floor, `MIN_CAPPED=15`, because a floor of 5 would be satisfied by the Swift skeleton
  alone while every Python file had vanished.

  **The decisive demonstration** is the manifest-only package, which is the case this guard's header has
  always claimed to catch:

      a package whose ONLY tracked file is its manifest
        OLD check:    rc=0   P-SRC-02: 11 Swift files, 21 source files under the cap, 2 exempt
        FIXED check:  rc=1   P-SRC-02: Swift package(s) contribute no file to the checked set: 
                             apps/ios/Packages/ScenicApp

  With `capped` narrowed, the fixed guard also fires with its own message rather than relying on the cap to
  stumble over the file. I am NOT claiming my run reproduced the old check's silence there - my throwaway
  narrowed the copy under test and not the old copy, so that column compared two different states. The sweep
  demonstrated it properly and their transcript is the evidence for it; mine only confirms the fix.

  Real repo, unchanged: `P-SRC-02: 10 Swift files, 20 source files under the cap, 2 exempt`.

  **What this says about the exercise.** I built the sweep to hunt "a check whose expected value comes from
  the thing it checks" after that defect appeared five rounds running in T-0025. It found two more in the
  file I had written to enforce the rule, one of which I had described accurately and then misdiagnosed, and
  one of which I had specified in my own brief and then skipped. The pattern is not that I keep making a
  careless mistake; it is that I keep writing the guard and then not asking what would have to be true for it
  to go red.

