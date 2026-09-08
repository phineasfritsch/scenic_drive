---
id: T-0066
title: ops/check-pins reports failed=0 and exits 0 when it ran no assertion at all
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T01:19:36Z
lease_expires_at: 2026-09-08T05:19:36Z
worktree: wt/T-0066
branch: task/T-0066
exclusive: []
touches: [ops/lib/pins.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**`ops/check-pins` can report success having executed nothing, and three separate one-word edits reach that
state.** Found by the self-referential-check sweep, every case executed rather than reasoned about:

    (a) delete every pin from pins/PINS.yaml, keeping the header comments
        -> PINS ok=0 skipped=0 pending=0 expired=0 failed=0 tier=linux   exit 0
        -> identical under --source-only

    (b) change `anchor: source` to `anchor: sources` - one typo, five lines
        -> the CI job `pins-source-only` prints ok=0 skipped=12 ... failed=0, exit 0
        -> the import ban and the 300-line cap stop running on every push, with nothing red

    (c) no file edit at all: `ops/check-pins --tier bogus`
        -> ok=0 skipped=9 pending=3 expired=0 failed=0 tier=bogus        exit 0
        control: the same tree with --tier linux gives ok=1 ... failed=8, so the harness does execute
        assertions when it is not being fooled

**Why it is hollow.** The exit code derives only from `failed` and `expired`, both counted while iterating
the very list the run is supposed to prove non-empty. `load()` on a PINS.yaml with no `- id:` items returns
`[]` with no error. So the population being checked and the evidence that checking happened come from the
same file.

**This is the third instance of one bug.** agent/reviewer-5 fixed exactly this in `ops/lib/check-exec-bits`
(MIN_FILES + a REQUIRED list). agent/reviewer-10 fixed it in `ops/lib/check-line-cap`. **The runner that
executes both of those fixed checks never got the guard itself.** Case (b) is the one that matters most:
`pins-source-only` is the per-push gate, so a typo in a data file silently disables the import ban for
everybody, and nothing anywhere goes red.

- Assert the run actually executed assertions: a floor on the number of pins loaded, and a floor on the
  number that were RUN rather than skipped for the current tier.
- Refuse an unrecognised `--tier`. Case (c) needs no file edit at all, which makes it the easiest to hit by
  accident and the hardest to notice.
- Consider a REQUIRED list of pin ids that must exist, the way `check-exec-bits` has one for paths - a pin
  that silently disappears from PINS.yaml is the same failure as one that never ran.
- Demonstrate red for all three cases above, and green after. Case (b) must be demonstrated against
  `--source-only` specifically, because that is the mode the push gate uses.
- Do NOT weaken the skip logic to make this quieter. `runs_on` skipping is correct behaviour; the defect is
  that a run which skipped EVERYTHING reports success.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from a repo-wide sweep for checks whose expected value comes from
  the thing they check. Eight surfaces, two adversarial verifiers per finding, each required to execute its
  falsification.
- 2026-09-08T01:19:36Z claimed by agent/claude-opus-5; lease until 2026-09-08T05:19:36Z
- 2026-09-08 agent/claude-opus-5 fixed in `ops/lib/pins.py` (269 lines, under the cap). Guards follow the
  shape of `ops/lib/check-exec-bits` (MIN_FILES + REQUIRED) and `ops/lib/check-line-cap` (MIN_FILES): module
  constants `TIERS`, `MIN_PINS=10`, `MIN_RAN=6`, `MIN_RAN_SOURCE_ONLY=2`, `REQUIRED` (12 ids), `REQUIRED_SOURCE`
  (P-SRC-01, P-SRC-02 must carry `anchor: source`); strict `parse_args` refuses an unknown argument or tier
  with exit 2; `ran` counts only pins whose assertion was executed. The `runs_on` skip logic is untouched.

  BASELINE (unchanged before and after the fix):

      $ bash ops/check-pins
      PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
      EXIT=0
      $ bash ops/check-pins --source-only
      PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
      EXIT=0

  RED (a) every pin deleted from pins/PINS.yaml, header comments kept:

      $ bash ops/check-pins
      PINS ok=0 skipped=0 pending=0 expired=0 failed=0 tier=linux
      EXIT=0
      $ bash ops/check-pins --source-only
      PINS ok=0 skipped=0 pending=0 expired=0 failed=0 tier=linux source-only
      EXIT=0

  GREEN (a) same edit, same two commands:

      $ bash ops/check-pins
      PINS FAIL: only 0 pin(s) loaded from pins/PINS.yaml (expected >= 10).
        An empty or truncated pin list must never read as 'every load-bearing property holds'.
      EXIT=1
      $ bash ops/check-pins --source-only
      PINS FAIL: only 0 pin(s) loaded from pins/PINS.yaml (expected >= 10).
        An empty or truncated pin list must never read as 'every load-bearing property holds'.
      EXIT=1

  RED (b) `sed -i 's/^  anchor: source$/  anchor: sources/' pins/PINS.yaml` (4 lines changed), demonstrated
  against `--source-only` because that is what the `pins-source-only` push gate runs. `import SwiftUI` was
  prepended to Sources/ScenicKit/Geo/Geo.swift for the same run, so the gate had a real violation to catch:

      $ bash ops/check-pins --source-only
      PINS ok=0 skipped=12 pending=0 expired=0 failed=0 tier=linux source-only
      EXIT=0

  GREEN (b) same one-word typo:

      $ bash ops/check-pins --source-only
      PINS FAIL: pin(s) the --source-only push gate exists for are not anchor: source: P-SRC-01 (anchor: 'sources') P-SRC-02 (anchor: 'sources').
        The import ban and the 300-line cap would stop running on every push with nothing red.
      EXIT=1

  RED (c) no file edit at all:

      $ bash ops/check-pins --tier bogus
      PINS ok=0 skipped=9 pending=3 expired=0 failed=0 tier=bogus
      EXIT=0

  GREEN (c):

      $ bash ops/check-pins --tier bogus
      PINS FAIL: unknown --tier 'bogus'; accepted: --tier <linux|mac>, --source-only, --verbose. An unknown tier matches no runs_on, so every pin would skip and the run would report failed=0
      EXIT=2
      $ bash ops/check-pins --tier
      PINS FAIL: --tier needs a value; accepted: --tier <linux|mac>, --source-only, --verbose
      EXIT=2
      $ bash ops/check-pins --sourceonly
      PINS FAIL: unrecognised argument '--sourceonly'; accepted: --tier <linux|mac>, --source-only, --verbose
      EXIT=2
      $ bash ops/check-pins --tier mac
      PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=mac
      EXIT=0

  The other two guards, each seen red (a check nobody has seen fail is not a check). P-GIT-01's block deleted:

      $ bash ops/check-pins
      PINS FAIL: required pin id(s) absent from pins/PINS.yaml: P-GIT-01.
        A pin that silently disappears is the same failure as one that never ran.
      EXIT=1

  and the run-floor alone, with P-SRC-01/P-SRC-02 `runs_on` narrowed to `[mac]` (no expiry attaches to mac, so
  nothing else fires) — note `failed=0` on the summary line and exit 1 anyway, which is the whole point:

      $ bash ops/check-pins --source-only
      PINS ok=1 skipped=10 pending=1 expired=0 failed=0 tier=linux source-only
       - only 1 assertion(s) actually ran for tier=linux --source-only (expected >= 2)
            Skipping is correct; reporting success after skipping everything is not.
      EXIT=1

  GATES in wt/T-0066: `bash ops/queue-check` -> `QUEUE OK (66 tasks)` exit 0; `bash ops/sane` -> `SANE OK`
  exit 0; `bash ops/agent-preflight` -> `PREFLIGHT OK` exit 0; `bash ops/check-pins` and
  `bash ops/check-pins --source-only` as in BASELINE above, both exit 0. `bash ops/test` exits 1 with
  `FAIL: services/api exists but vitest produced no report` — PRE-EXISTING and not from this change: the
  identical command on the unmodified tree (`git checkout -- ops/lib/pins.py`, then re-run) prints the same
  line and the same exit 1. `services/api/node_modules` is absent in this worktree; `npm ci` has never run
  here, and CI installs it in the `core` job.
