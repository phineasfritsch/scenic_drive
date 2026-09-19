---
id: T-0186
title: ops/mutate population gate - a checker that refuses a new numeric module under services/etl/etl/ or Sources/ with no ops/mutate population, pinned; red on assemble.py and sinuosity.py first
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T08:09:33Z
lease_expires_at: 2026-09-19T13:09:33Z
worktree: .worktrees/T-0186
branch: task/T-0186
exclusive: []
touches: [ops/mutate/, ops/lib/, pins/PINS.yaml, services/etl/tests/]
pins_affected: []
reviewer: null
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
