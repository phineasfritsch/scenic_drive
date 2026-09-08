---
id: T-0067
title: ops/check-pins reports failed=0 and exits 0 when it ran no assertion at all
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
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
