---
id: T-0186
title: ops/mutate population gate - a checker that refuses a new numeric module under services/etl/etl/ or Sources/ with no ops/mutate population, pinned; red on assemble.py and sinuosity.py first
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T08:09:33Z
lease_expires_at: 2026-09-19T13:09:33Z
worktree: .worktrees/T-0186
branch: task/T-0186
exclusive: []
touches: [ops/mutate/, ops/lib/, pins/PINS.yaml, services/etl/tests/, .github/workflows/linux-core.yml]
pins_affected: []
reviewer: agent/rv1-pr114
depends_on: [T-0176, T-0146]
verify: [ops/test, ops/check-pins]
acceptance:
  - "a checker (rule where it lives - ops/mutate/ beside the runners or ops/lib/ beside the other gates - and say why) that lists every module under services/etl/etl/ and Sources/ScenicKit/ whose name a git diff against main ADDS, and refuses by name when ops/mutate/ holds no population for it; RED BY NAME first on a copy of main where assemble.py (T-0146) and sinuosity.py (T-0161) have no population, then green once T-0176 and T-0187 land; an explicit allowlist for non-numeric modules (fetch.py, manifest.py, corpus.py) with the reason beside each"
  - "pins/PINS.yaml pin (anchor: process, runs_on: [linux], the P-GIT-02 interpreter style); --prove-red table (a population file deleted; a new module added with none; the allowlist widened to a numeric module)"
  - "bash ops/check-pins --source-only, bash ops/lib/check-line-cap, bash ops/queue-check bare at the final commit"
---
## Brief

From the 2026-09-19 21:13 panel (PROCESS, grounded). CLAUDE.md's Verification section already makes a new numeric
module ship its mutation population under ops/mutate/ with a literal floor and EQUIVALENT-with-witness entries -
"never prose in a task file". It is unenforced: ops/mutate/ holds sixteen files, all for Swift modules, zero for
Python; sinuosity.py merged via #94 after four rounds and assemble.py (#102) shipped without one; no check under
ops/ or .githooks/ references ops/mutate beyond comments. The population is simultaneously the fixer's brief and
the reviewer's must-enumerate list (T-0176's rationale). Lands after #102 and T-0176 so it does not add a fourth
blocking class to a fix pass in flight.

## Log
- 2026-09-19T03:29:43Z filed by agent/claude-fable-5-1 from the 21:13 panel's grounded synthesis. Not started.
- 2026-09-19T06:29:45Z PROMOTED to ready/ by agent/claude-fable-5-1 (00:13 panel, grounded): depends_on [T-0176, T-0146] are both in queue/done/ (#107 merged 86d0f91). It is the check that would have refused T-0168's tagwriter/scenecheck and T-0170's StraightLineDistance by name for shipping without a population; the honest filler when a slot frees before #101/#110 merge.
- 2026-09-19T08:09:33Z claimed by agent/claude-opus-5; lease until 2026-09-19T13:09:33Z
- 2026-09-19T09:06:22Z RULINGS, before any code (the author rule). Five disagreements between the acceptance,
  ops/mutate/ as it stands and CLAUDE.md's Verification section, ruled here.
  R1 WHERE IT LIVES: `ops/lib/check-mutate-population.py`, beside the other gates, NOT under ops/mutate/.
  Three reasons. (a) It is a read-only gate run by a pin, not a mutation harness - it builds nothing, copies no
  subject, runs no pytest; ops/mutate/ is the population it AUDITS, and a gate that lives inside the directory
  it audits is deleted by the same `rm` that deletes its subject (P-OPS-06's class: a check nothing runs).
  (b) ops/lib/ is where check-line-cap, check-exec-bits, check-schema-version.py already sit, and this is the
  same shape as check-schema-version.py - read two places as TEXT, refuse fail-closed, `--prove-red` table,
  its own pin id as the anchor. (c) `.py` under ops/ is DATA to ops/lib/check-exec-bits (100644, awk line 44)
  and is invoked as an argument to an interpreter, which is exactly the P-GIT-02 assertion style the
  acceptance asks for. A bash wrapper would add a 100755 file whose only job is to call python.
  R2 WHAT A MODULE IS: every `*.py` directly under `services/etl/etl/` (not recursive; there are no
  subpackages) and every `*.swift` anywhere under `Sources/` - BOTH root targets, ScenicKit and Handoff, not
  ScenicKit alone. The acceptance says `Sources/ScenicKit/`; CLAUDE.md's Verification rule says `Sources/`,
  and CLAUDE.md wins. T-0170 shipped `Sources/Handoff/StraightLineDistance.swift` - great-circle hops in
  driving order, a number on a shipping screen - with no population, and T-0199 was filed for it; a gate
  scoped to ScenicKit/ would have passed that PR by construction. `Tests/` and `apps/ios/` are out: the rule
  is about modules that compute, and ops/mutate/ populations mutate subjects, not suites.
  R3 HOW A POPULATION DECLARES ITS SUBJECT: today it does not, in any form a gate can read. Ten drivers state
  their subjects ten ways - `SUBJECTS` as a tuple (budget_paths.py, gates.py, scenic_tags.py), `SUBJECTS` as a
  list (handoff.py), bare `SRC`/`ERR`/`SIGN`/`MAP`/`STRIP`/`FLAG`/`SCORE`/`TERMS` (guidance, hazards, retrace,
  routescore, segmentscore), and geometry.py states its three in a DOCSTRING while the paths themselves are
  relative strings in geometry_mutations.py. Anchoring on a docstring is anchoring on a comment, which
  CLAUDE.md forbids. So the ruling: one identifier, `SUBJECT_MODULES`, a literal tuple of REPO-RELATIVE path
  strings, carried by every population driver, added to all ten in this PR as a minimal edit beside the paths
  each driver already computes. The gate reads it as text (a regex over the file), never by import: importing
  a driver runs module-level code that resolves paths and builds populations.
  WHICH FILES MUST CARRY IT is a WHITELIST, never a scan: `DRIVERS` names the ten, `PROBES` names
  geometry_probe.py with its reason, and any OTHER `ops/mutate/*.py` carrying `if __name__ == "__main__":` is
  a REFUSAL - a new driver must be classified, not silently ignored. geometry_probe.py is exempt rather than
  declaring: if it declared geometry.py's three subjects, deleting geometry.py would leave the coverage intact
  in the gate's eyes, which is the exact defect this gate exists to catch.
  R4 THE POPULATION SET vs THE DIFF: both, with different consequences, because they answer different
  questions. (i) NEW modules - the acceptance's scope, `git diff --diff-filter=A` against the merge-base with
  origin/main - are BLOCKING: a module added by this PR with no population and no allowlist entry refuses by
  name. (ii) A literal `COVERED_FLOOR` of the 22 modules a population covers TODAY is also blocking, in the
  other direction: a driver that narrows its SUBJECT_MODULES, or a population quietly retired, refuses even
  though the diff adds nothing. That is P-PROC-05's lesson one level up - a count of populations would read
  clean while the population that mattered was deleted. (iii) EXISTING modules with no population and no
  allowlist entry print as an informational DEBT table and are NEVER red. Making them red today would either
  block every unrelated PR or force a dishonest allowlist entry for score.py, curvature.py, terrain.py and
  the rest; the debt is a queue of tasks (T-0199 is the first), not a defect in the PR that trips over it.
  R5 THE ALLOWLIST is `ops/lib/mutate-population-allowlist.json`, one entry per module, one REASON per entry,
  DATA rather than code so `--prove-red` can mutate it in a sandbox. Read each and ruled - 'numeric' = it
  computes a number that reaches score, route or tags: NON-NUMERIC (allowlisted) are fetch.py (fetches and
  verifies bytes), manifest.py (a table of inputs and licences), corpus.py (`python -m etl.corpus` wiring),
  corpuswriter.py (writes the sqlite the others computed), extract.py (drives osmium), extractway.py (reads
  the JSON extract), byway_source.py (parses two pulls into entry shape), region.py (a bbox and recorded
  counts), tagfilter.py (osmium filter expressions), terms.py (the term vocabulary), schema.py (DDL and
  SCHEMA_VERSION, already pinned by P-PROD-05), contentdigest.py (a digest of bytes), checkbounds.py
  (compares a built extract's counts, reaching nothing), counts.py (per-class object counts that gate the
  build, not the score), oracle.py / oracle_select.py / oracle_report.py (build and report the curvature
  ORACLE, which is the check on a number rather than a number the product ships), review_sheet.py and
  streetview.py (pages and URLs a human clicks), osmxml.py (a stream copy) and waydoc.py (wiring over
  producers that carry their own numbers) - those last two on T-0168's closing ruling, quoted in
  ops/mutate/scenic_tags.py's header - plus `__init__.py` (empty package marker), and in Swift
  Coordinate.swift (a WGS-84 pair), BywayTier.swift (a three-state enum) and GuidanceManeuver.swift (a
  vocabulary enum). Everything else is NUMERIC and, where uncovered, is DEBT: assemble.py, score.py,
  normalise.py, curvature.py, terrain.py, dem.py, landcover.py, furniture.py, speedfit.py, surface.py,
  geom.py, segid.py, segmenter.py, byways.py, byway_route_key.py, corpusmatch.py, way_record.py, and in
  Swift Geo.swift, SolarMath.swift, SolarEvents.swift, CivilDate.swift (julianDayAtMidnightUTC),
  ScoredEdge.swift, SkylineRoute.swift, StraightLineDistance.swift.
  WHAT IS MECHANICALLY CHECKABLE ABOUT THE ALLOWLIST, and what is not: the gate CANNOT know whether a module
  is numeric - that is a reading, and it is recorded above rather than computed. What it can refuse, and
  does: (a) an entry whose reason is empty or whitespace - a name with no reason is a silent widening;
  (b) an entry for a module that a population ALSO covers - the two claims contradict each other, and that is
  the checkable shadow of 'the allowlist widened to a numeric module', since the only numeric modules the
  gate can NAME are the ones some driver already mutates; (c) an entry naming a module that does not exist -
  a stale entry that would silently cover a future file of that name. What stays uncheckable and therefore
  stays a REVIEW duty: adding `score.py` with a plausible-sounding reason. The allowlist is a whitelist of
  names, and every widening of it shows up in the diff of a DATA file with a reason a reviewer must read.
  RED FIRST, which tree: a COPY of this tree with the geometry_* and scenic_tags* drivers deleted, NOT
  `git show <pre-T-0176 sha>:`. At any pre-T-0176 sha neither this gate nor its allowlist existed, so the
  only way to run it there is to copy today's gate onto that tree - which is a copy of an old tree, the same
  thing, with a fabricated provenance. Deleting the two drivers reproduces the exact property main had (no
  population for sinuosity.py, none for assemble.py) and the sandbox is visibly a sandbox.
- 2026-09-19T09:40Z BUILT, and RED BY NAME BEFORE GREEN. `ops/lib/check-mutate-population.py` (282 lines,
  100644) with its mutation table split off into `ops/lib/mutate_population_red.py` (79 lines, 100644) at the
  300-line cap - the first file is the CHECK, the second is the population it is run against, the same split
  ops/mutate/budget.py has from budget_mutations.py - plus `ops/lib/mutate-population-allowlist.json` (25
  entries, one reason each) and `SUBJECT_MODULES` added to all ten drivers. The red tree is built by
  `.build-t0186/build_redtree.py` (gitignored scratch, header states the two literals it edits and why).
  RED, by name, both modules:
      $ python .build-t0186/redtree/ops/lib/check-mutate-population.py --root .build-t0186/redtree \
          --added services/etl/etl/assemble.py services/etl/etl/sinuosity.py
      P-PROC-06: module(s) added by this branch with no mutation population:
        services/etl/etl/assemble.py
        services/etl/etl/sinuosity.py
        CLAUDE.md, Verification: a new numeric module ships its mutation population under ops/mutate/ with a literal floor.
      RED EXIT=1
  The correction the split bought, recorded rather than smoothed over: the first version imported its table
  at module scope, and the red tree - which did not yet copy the sibling - printed a ModuleNotFoundError
  TRACEBACK out of an ops entry point (T-0087's class). The import moved inside `prove_red` and a missing
  sibling is now this gate's own refusal, exit 2 with a sentence. The measured line count above was re-taken
  after that correction (282, not the 278 the pre-correction file had).
- 2026-09-19T09:55Z FINAL PRE-REVIEW COMMIT. The whole acceptance block re-run BARE on this tree at 270c8a7
  and re-quoted, nothing piped into a gate's exit status (the `gate | tail && next` trap):
      $ python ops/lib/check-mutate-population.py                                        EXIT=0
      P-PROC-06: 71 modules, 22 covered by 10 populations, 25 allowlisted, 0 added by this branch
        DEBT (informational, never red): 24 existing module(s) with no population and no allowlist entry
      P-PROC-06: every added module is covered or allowlisted; the floor of 22 holds
      $ python ops/lib/check-mutate-population.py --prove-red                             EXIT=0
      P-PROC-06 --prove-red: 8 cases against a copy of the tree at ...\.worktrees\T-0186
        case                                         expect  got  verdict
        control: the tree as committed                    0    0  ok
        a population file deleted (geometry.py)           2    2  ok
        a driver narrows SUBJECT_MODULES                  1    1  ok
        a new module added with no population             1    1  ok
        a new module that IS allowlisted                  0    0  ok
        the allowlist widened to a covered module         2    2  ok
        an allowlist entry with no reason                 2    2  ok
        P-PROC-06 deleted from PINS.yaml                  2    2  ok
      P-PROC-06 --prove-red: all 8 cases behaved as stated
      $ bash ops/check-pins --source-only                                                 EXIT=0
      PINS ok=13 skipped=15 pending=1 expired=0 failed=0 tier=linux source-only
      $ bash ops/lib/check-line-cap                                                       EXIT=0
      P-SRC-02: 78 Swift files tracked (Sources=27, Tests=38, apps/ios=13), none over 300 lines
      $ bash ops/lib/check-exec-bits                                                      EXIT=0
      P-OPS-01: 76 files, 23 required present, all modes correct
      $ bash ops/queue-check                                                              EXIT=0
      QUEUE OK (199 tasks)
      $ git ls-files -s <the three new files>
      100644 ops/lib/check-mutate-population.py   100644 ops/lib/mutate-population-allowlist.json
      100644 ops/lib/mutate_population_red.py         (all three DATA to check-exec-bits: .py and .json
                                                       under ops/ are 100644 and invoked as an argument to
                                                       an interpreter, never as ./path - T-0176's ruling)
      $ awk 'END{print NR}'   282 / 79 / 30 lines - all three under the 300-line cap
  P-PROC-06 is anchor: process, so `--source-only` SKIPS it (15 skipped) rather than running it; the
  assertion above is the evidence, exactly as P-PROC-05's --prove-floor is for its pin.
  The two drivers that gained SUBJECT_MODULES and run on this box still pass, after the commit (both compare
  their subjects to `git show HEAD:`, which is why they are run here and not before it):
      $ python ops/mutate/scenic_tags.py    EXIT=0   MUTATE OK  caught=25/25 equivalent_caught=0
      $ python ops/mutate/geometry.py       EXIT=0   POPULATION 12 mutations over 6 classes (floor 12),
                                                     4 equivalent (floor 4); every one killed by the test
                                                     that names it
  STILL OPEN, for the reviewer rather than hidden: (1) the 24 DEBT modules have no population - score.py,
  normalise.py, curvature.py, terrain.py, dem.py, landcover.py, assemble.py and the rest, plus
  StraightLineDistance.swift which is already T-0199. This gate makes the list printable and stops it
  growing; it does not shrink it, and one task per module is the honest way to. (2) The gate cannot decide
  numeric vs non-numeric: adding `score.py` to the allowlist with a plausible reason passes, and only a
  reviewer reading the diff of a 25-entry data file catches it (ruling R5). (3) The added-module set is a
  git diff against the merge base with origin/main, so a module added on a stacked branch whose base is
  another task branch is only seen once that base reaches main (T-0113's tower, the same blind spot every
  diff-scoped gate here has).
- 2026-09-19T09:57:22Z PRE-REVIEW MUTANT PASS - five findings, ruled here BEFORE the code that closes them.
  B0 THE GATE CANNOT BE GREEN ON ANY PULL REQUEST, and CI says so: the `core` job on PR #114 is RED with
  `P-PROC-06: no merge base with origin/main or main`. `.github/workflows/linux-core.yml` checks out at
  actions/checkout@v4's default depth 1 in both jobs; a one-commit clone has no merge base with anything, so
  `added_modules()` refuses (exit 2) on every PR run, forever. The fix is `fetch-depth: 0` on the checkout of
  the job that RUNS ops/check-pins - the `core` job - and nothing else: pins-source-only skips this pin
  (anchor: process), so deepening its checkout would buy nothing and slow every push. REJECTED alternative:
  the gate fetching its own base (`git fetch --deepen` / `git fetch origin main`) when the merge base is
  missing. A check never mutates the repo it is reading - that is ops/sane's rule and the reason this gate
  reads every driver as TEXT rather than importing it; a checker that writes refs would also turn a red
  network into a green gate. Instead the refusal NAMES the fix ("shallow clone: set fetch-depth: 0"), so the
  next clone that lands here is fixed at its source rather than worked around inside the check. This WIDENS
  touches: to `.github/workflows/linux-core.yml` - one line in one job, the smallest change that gives the
  gate the merge base it already refuses without.
  S1 A DECLARATION IS NOT COVERAGE. `SUBJECT_MODULES` is bound to nothing: appending one string to any
  driver's tuple covers a brand-new numeric module with ZERO mutations written and the gate goes green - the
  exact dishonesty the allowlist's `reason` field exists to expose, available for free on the other side of
  the ledger. FIX: every declared subject must also be TARGETED. The subject's repo-relative path, or its
  basename, must occur in the CODE of the driver's own family (`ops/mutate/<stem>*.py`) with COMMENTS,
  DOCSTRINGS and the `SUBJECT_MODULES` declaration itself removed - comments and docstrings because CLAUDE.md
  forbids anchoring on them, the declaration because it is the claim under test. Measured on this tree first:
  all 22 subjects are targeted after stripping, 21 by basename in a mutation table (geometry_mutations.py,
  budget_paths.py, gates_corpus.py) and the rest in the driver's own mutation text; geometry_probe.py is
  excluded from geometry.py's family for PROBES' original reason. Still TEXTUAL - no driver is imported.
  S2 THE DIFF ARM HAS NEVER BEEN SEEN RED. All 8 --prove-red cases pass `--added`, so `added_modules()` is
  never executed by the proof: `return []` in it passes all 8 while the gate stops seeing anything. B0 is the
  same blindness in production - a live arm nothing proves. FIX: `ops/lib/mutate_population_git.py`, three
  cases that run the REAL git arm in a throwaway `git clone --no-hardlinks` under the gitignored
  `.build-mutate-population/`, with a real commit on top: one RED (an uncovered module added), one GREEN (the
  same module added together with its allowlist entry).
  S3 A MOVE IS AN R, NOT AN A. A module moved INTO a root from outside it (services/etl/mutate/, apps/, a
  scratch dir) is a rename to git, and `--diff-filter=A --name-only` never names the destination, so the
  cheapest way past this gate is to write the module elsewhere and move it. FIX: `--no-renames` on the diff,
  and the third git-arm case moves `services/etl/mutate/byway_route_key.py` into `services/etl/etl/` and
  must refuse it by name.
  S4 SUBPACKAGES. `services/etl/etl` was globbed non-recursively on ruling R2's "there are no subpackages",
  which is true TODAY and is not a property anyone maintains; `Sources/` is already recursive. FIX: recursive
  both sides, with a case that adds `services/etl/etl/sub/deep.py` and must refuse it (non-recursive, that
  module is not even in `known` and the gate reports a clean sheet).
  RECORDED, NOT FIXED. `services/etl/mutate/byway_route_key.py` is a population-shaped file OUTSIDE
  ops/mutate/ while `services/etl/etl/byway_route_key.py` is listed as DEBT - i.e. as having no population.
  Ruled: it is a MUTATION POPULATION in the wrong directory, not a module of the ETL package. It is not under
  `services/etl/etl/`, so it is not a subject this gate knows, and it declares no `SUBJECT_MODULES`, so it
  cannot be read as coverage either; CLAUDE.md says a population lives under `ops/mutate/`. Moving it is a
  real edit to a file this task does not own and would silently change what the DEBT table says, so it is
  NOT done here: it stays DEBT and the move is STILL OPEN (4) for its own task. This gate is why the
  contradiction is visible at all.
- 2026-09-19T10:12:00Z THE FIVE CLOSED IN ONE COMMIT, each arm RED BEFORE GREEN. `.build-t0186/
  prove_discrimination.py` (gitignored scratch) backs each fix out of the SOURCE one at a time and runs the
  shipped `--prove-red`; the case that binds the arm goes NOT DISCRIMINATING and the proof exits 1:
      S1 targeting removed          a driver DECLARES a module it never mutates       2  0  NOT DISCRIMINATING
      S2 added_modules returns []   git arm: a module added, uncovered                1  0  NOT DISCRIMINATING
                                    git arm: a module MOVED in from outside a root    1  0  NOT DISCRIMINATING
      S3 --no-renames removed       git arm: a module MOVED in from outside a root    1  0  NOT DISCRIMINATING
      S4 etl/ not recursive         a new module in a SUBPACKAGE of a root            1  0  NOT DISCRIMINATING
      each of the four: "P-PROC-06 --prove-red: N case(s) did not behave as stated. The check is not a
      check." EXIT=1, then restored EXIT=0.
  B0's red is CI itself: `core` on PR #114 failed with `P-PROC-06: no merge base with origin/main or main`
  before `fetch-depth: 0`, which is the one-line change to `.github/workflows/linux-core.yml` (touches
  widened above, 09:57 ruling); the refusal now names the cause - "On CI this means a shallow clone: set
  fetch-depth: 0 on the checkout of the job that runs ops/check-pins. This check never fetches for itself -
  it does not write to the repository it reads."
  WHAT MOVED, and why it is a split of meaning and not a line-count dodge: the `--prove-red` RUNNER moved out
  of the gate into ops/lib/mutate_population_red.py, which now holds both populations and runs them - and
  runs them through `gate.main`, the gate's own shipping entry point, never a helper (CLAUDE.md: a test named
  for a defect binds to the shipping symbol). The gate keeps a nine-line `prove_red` that imports the harness
  INSIDE the function, so a missing sibling stays this gate's refusal rather than a traceback (T-0087).
  FINAL PRE-REVIEW COMMIT - the whole acceptance block re-run BARE on this tree, nothing piped into a gate's
  exit status, and re-measured after the corrections (T-0162's rule):
      $ python ops/lib/check-mutate-population.py                                        EXIT=0
      P-PROC-06: 71 modules, 22 covered by 10 populations, 25 allowlisted, 0 added by this branch
        DEBT (informational, never red): 24 existing module(s) with no population and no allowlist entry
      P-PROC-06: every added module is covered or allowlisted; the floor of 22 holds
      $ python ops/lib/check-mutate-population.py --prove-red                             EXIT=0
      P-PROC-06 --prove-red: 10 sandbox + 3 real-git cases at ...\.worktrees\T-0186
        case                                             expect  got  verdict
        control: the tree as committed                        0    0  ok
        a population file deleted (geometry.py)               2    2  ok
        a driver narrows SUBJECT_MODULES                      1    1  ok
        a new module added with no population                 1    1  ok
        a new module that IS allowlisted                      0    0  ok
        a new module in a SUBPACKAGE of a root                1    1  ok
        a driver DECLARES a module it never mutates           2    2  ok
        the allowlist widened to a covered module             2    2  ok
        an allowlist entry with no reason                     2    2  ok
        P-PROC-06 deleted from PINS.yaml                      2    2  ok
        git arm: a module added, uncovered                    1    1  ok
        git arm: a module added WITH its allowlist entry      0    0  ok
        git arm: a module MOVED in from outside a root        1    1  ok
      P-PROC-06 --prove-red: all 13 cases behaved as stated
      $ bash ops/lib/check-line-cap                                                       EXIT=0
      P-SRC-02: 78 Swift files tracked (Sources=27, Tests=38, apps/ios=13), none over 300 lines
      $ bash ops/lib/check-exec-bits                                                      EXIT=0
      P-OPS-01: 76 files, 23 required present, all modes correct
      $ bash ops/queue-check                                                              EXIT=0
      QUEUE OK (199 tasks)
      $ bash ops/check-pins --source-only                                                 EXIT=0
      PINS ok=13 skipped=15 pending=1 expired=0 failed=0 tier=linux source-only
      (P-PROC-06 is anchor: process, so --source-only SKIPS it - the 13-case table above is its evidence,
       and CI's `core` job, green for the first time on this PR, is the other half.)
      $ awk 'END{print NR}'   294 (check-mutate-population.py) / 207 (mutate_population_red.py) / 30
                              (mutate-population-allowlist.json) - all three under the 300-line cap; the
                              gate is 294 because the runner moved OUT as it gained the S1 reader, and the
                              next edit to it splits rather than squeezes
      $ git ls-files -s   100644 all three, DATA to check-exec-bits, invoked as an argument to an interpreter
      $ python ops/mutate/scenic_tags.py    EXIT=0   MUTATE OK  caught=25/25 equivalent_caught=0
      $ python ops/mutate/geometry.py       EXIT=0   POPULATION 12 mutations over 6 classes (floor 12),
                                                     4 equivalent (floor 4); every one killed by the test
                                                     that names it
      (no driver and no subject changed in this commit, so both were run before it rather than after.)
  STILL OPEN, carried forward and added to: (1) the 24 DEBT modules still have no population; this gate makes
  the list printable and stops it growing. (2) numeric-vs-not stays a REVIEWER READING - adding score.py to
  the allowlist with a plausible reason passes, and only the diff of a data file with a reason per entry
  catches it (ruling R5); S1 closes the other half of that hole, the driver side, where a name could be
  claimed with no mutation behind it. (3) the added-module set is still a diff against the merge base with
  origin/main, so a module added on a branch stacked on another task branch is seen once that base reaches
  main. (4) services/etl/mutate/byway_route_key.py is a population outside ops/mutate/ (09:57 ruling); moving
  it belongs to its own task.
- 2026-09-19T11:05:00Z REVIEW PASS by agent/rv1-pr114 (round 1, harness PR #114). Judged on a detached
  worktree at 87739e7 (.worktrees/rv1-pr114), `git status --short` empty after every mutant.
  CI, read once: `gh pr checks 114` -> `core pass 2m15s`, `pins-source-only pass 1m4s`. B0's fix is proved
  by the green `core` job itself: the run that was red with "P-PROC-06: no merge base with origin/main or
  main" is green with `fetch-depth: 0` on the `core` checkout only, and the refusal text now names the cause.
  RE-RUN BARE on the review worktree, all matching the Log's final block: the gate EXIT=0 ("71 modules, 22
  covered by 10 populations, 25 allowlisted, 0 added by this branch ... the floor of 22 holds", 24 DEBT);
  `--prove-red` EXIT=0 "all 13 cases behaved as stated"; `bash ops/lib/check-line-cap` EXIT=0 (P-SRC-02, 78
  Swift files); `bash ops/lib/check-exec-bits` EXIT=0 (P-OPS-01, 76 files, 23 required, all modes correct);
  `bash ops/queue-check` EXIT=0 (QUEUE OK, 199 tasks); `python ops/mutate/geometry.py` EXIT=0 (12 mutations
  over 6 classes, floor 12, 4 equivalent); `python ops/mutate/scenic_tags.py` EXIT=0 (caught=25/25); `wc -l`
  294 / 207 / 30 as measured; `git ls-tree HEAD` 100644 on all three, matching ops/lib's other .py gates.
  `--source-only` NOT re-run here - CI's pins-source-only is the evidence, and P-PROC-06 is anchor: process
  and skipped by it anyway.
  SURVIVOR REPLAY of the pass's five findings, on the review worktree: S1 - retrace.py's SUBJECT_MODULES
  widened to ScoredEdge.swift with the basename placed ONLY in a `#` comment of the driver -> EXIT=2, "which
  no mutation in the retrace* population targets. A declaration is not coverage". The comment is stripped,
  so the gate does not anchor on one (CLAUDE.md). S2 - `added_modules()` replaced by `return []` -> both
  real-git arms go NOT DISCRIMINATING, EXIT=1, "The check is not a check." S3/S4 - the moved-in module and
  the subpackage module are cases 13 and 6 of the shipped table and both `ok`.
  ALLOWLIST READ against five modules rather than its reasons: checkbounds.py (compares meta.json, `max(rc,
  code)` only), terms.py (no arithmetic at all), BywayTier.swift (a 28-line three-state enum; the weights it
  names live in SegmentTerms.swift, which segmentscore.py covers), counts.py (`DEFAULT_TOLERANCE = 0.15`,
  `pct = (got - want) / want * 100`) and oracle_select.py (`SQUASH_RADIUS_M = 30.0`, `GEOMETRY_TOL_M = 1.0`,
  `CELL_DEG = 0.0005`, a proximity grid). The last two DO arithmetic; both reasons are honest under the
  allowlist's stated test - a number reaching score, route or tags - and neither number leaves the build
  gate or the oracle report. No module that reaches score, route or tags is allowlisted: score.py,
  curvature.py, normalise.py, terrain.py, dem.py, landcover.py and assemble.py are all in the DEBT table,
  where R4 iii put them. The BLOCKING condition - a new numeric module shipping with no population while the
  gate is green - does not hold: this branch adds no module under either root (0 added).
  TWO REVIEWER MUTANTS SURVIVED, both RECORDABLE and neither blocking; filed rather than fixed here, under
  CLAUDE.md's harness two-round cap.
  RV1-A COVERED_FLOOR IS IN THE CHECKER'S OWN SOURCE. Narrowing `ops/mutate/segmentscore.py`'s
  SUBJECT_MODULES to drop SegmentTerms.swift AND deleting that one line from COVERED_FLOOR in
  ops/lib/check-mutate-population.py, in the same edit, leaves the gate green: "21 covered by 10 populations
  ... the floor of 21 holds", EXIT=0 - while segmentscore.py still mutates SegmentTerms.swift, so the
  declaration and the population now disagree and nothing says so. The gate's own refusal text asks for
  exactly this ("take the module out of COVERED_FLOOR in the same commit that removes the mutations, with
  the reason"), but unlike the allowlist - DATA, one reason per entry, re-read on every widening - the floor
  is code with no reason field and is not a serial-only file. The asymmetry is the finding: the widening
  side of the ledger is reasoned data, the narrowing side is a tuple anyone can shorten.
  RV1-B A DUPLICATE KEY IN THE ALLOWLIST JSON SHADOWS A REASONED ENTRY. `json.loads` keeps the LAST value
  for a repeated key; a diff that adds `"services/etl/etl/schema.py": "ok"` above the existing reasoned
  entry runs green (EXIT=0, still "25 allowlisted") with the gate honouring one reason and the reviewer
  reading the other. Mechanically harmless today - the surviving value must still be non-empty, name a real
  module and not be covered - but the allowlist's whole load-bearing property is that a human reads the
  reason the gate uses. `object_pairs_hook` refusing a repeat is the one-line close.
  NOT REACHED, said rather than implied: `bash ops/test` and the full `bash ops/check-pins` were out of
  scope for this review; the eight non-geometry, non-scenic_tags drivers were not run (they need Swift); the
  DEBT backlog itself is unchanged and the Log's STILL OPEN (1)-(4) carry forward as filed.
  Signed off: queue/claimed/ -> queue/done/. Not merged by the reviewer.
