---
id: T-0134
title: ScenicKit SegmentScore: the geometric mean that keeps a curvy industrial road apart from a straight redwood one
state: review
owner: agent/unknown
owner_session: null
claimed_at: 2026-09-08T21:21:50Z
lease_expires_at: 2026-09-08T23:21:50Z
worktree: null
branch: task/T-0134
exclusive: []
touches: [Sources/ScenicKit/Scoring/, Tests/ScenicKitTests/, ops/mutate/]
pins_affected: []
reviewer: agent/reviewer-pr-segmentscore
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

This is the scenic engine's centre. Everything else - the lambda search, the route score, the corridor
learner - is machinery around the number this produces per way.

From the plan:

```
score = GATE × M^0.35 × E^0.65          in [0,1]     alpha = 0.35, scenery-led, because this is a car product
M = 0.45·curv + 0.20·elev_gain + 0.20·speed_fit + 0.15·sinuosity
E = 0.24·canopy + 0.22·relief + 0.16·(1−impervious) + 0.14·poi + 0.12·water + 0.12·(1−furniture)
    (+0.15 byway, capped)
Soft multipliers: tunnel > 300 m ×0.15 ; within 150 m of a motorway ×0.7
Absent surface: primary/secondary/tertiary → treat as paved
                unclassified/residential   → ×0.8 and raise a surface_unknown flag
highway ∈ {motorway, motorway_link, trunk, trunk_link} → score 0 (dull, NOT a routing gate)
```

### The design decision the tests must protect

**The mean is geometric, not arithmetic**, and the plan says why: *"keeps a curvy industrial road (0.32) apart
from a straight redwood road (0.62)"*. A road that is thrilling to drive but ugly should not average out to
the same number as a road that is beautiful but dull, because those are different products - and an
arithmetic mean says they are the same. The exponents 0.35 / 0.65 are the statement that this is a **car**
product where scenery leads.

An arithmetic mean is exactly the "simplification" a later agent will reach for, and most fixtures will not
notice: the two means agree whenever M and E are close. **A test that does not include a case with M and E far
apart pins nothing.** Build the discriminating fixture deliberately and say in the test why those numbers.

### The other invariant

`highway = motorway` scores **0** and is **not gated**. Those are different mechanisms and this task must not
blur them: [[T-0133]] owns the gate (a motorway is `.allowed`), this owns the score (a motorway is dull). The
whole freeway-shoulders design depends on both being true at once. A test should assert the pair together, so
that anyone changing one meets the other.

### Do

1. `Sources/ScenicKit/Scoring/SegmentTerms.swift` - the inputs, as a plain value with named terms in `0...1`.
   Validate rather than clamp: a term outside `0...1` is a bug upstream, and quantising it hides that.
2. `Sources/ScenicKit/Scoring/SegmentScore.swift` - the formula, the soft multipliers, the surface rule, and
   the motorway-scores-zero rule. Every weight a named constant, since these are the numbers the tuning
   process in the plan will move.
3. Tests pinning, at minimum: each weight set summing to 1 (asserted against a literal, never by summing the
   constants under test); the geometric mean, with a fixture where arithmetic and geometric disagree
   **loudly**; the exponents; each soft multiplier at and either side of its threshold (tunnel 300 m, motorway
   proximity 150 m); the surface rule for both road classes; output always in `0...1`; and motorway scoring 0
   while `Gates.decide` allows it.
4. `ops/mutate/segmentscore.py` on the corrected contract - the reference is `ops/mutate/gates.py`, which is
   the only one carrying all of: pass condition `caught == len(MUTATIONS)`; `--prove-vacuity` requiring
   `caught == 0` AND `missed == len(MUTATIONS)` over **every** test file ([[T-0132]]); an `EQUIVALENT` arm
   asserted the other way round; and a **baseline build retried twice** before it is believed. **Most
   mutations must move a NUMBER** - this is a file of thirteen weights, and a structural-only mutation set
   would be blind exactly where it matters. `arithmetic mean instead of geometric` is the mutation that
   matters most.
5. **No `Package.swift` change**: `Sources/ScenicKit/Scoring/` is inside the existing target path.

### Do not invent an oracle

The plan quotes two worked outputs - 0.32 for a curvy industrial road and 0.62 for a straight redwood one -
but **does not give the term values that produce them**. Do not reverse-engineer inputs to hit those numbers
and then present the result as an oracle: that is fitting the answer to the target, and this repository has
already rejected one oracle for less. Pin the formula's *structure and behaviour* with fixtures whose expected
values are computed by hand from the stated weights, and say plainly in the log that the plan's two numbers
are unreproduced. When the ETL exists, the real oracle is the Curvature project's Vermont output, which the
plan names.

### Not in scope

The ETL, the raster inputs, `scenic_score`'s 0-10 scaling for GraphHopper, and the Bradley-Terry tuning. This
is the reference formula in Swift, on given terms.

## Log
- 2026-09-09T00:30:00Z filed by agent/claude-opus-5. Filed with id T-0134 by hand; `ops/new-task` allocated
  T-9902 again - see [[T-0128]].
- 2026-09-08T21:21:50Z claimed by agent/unknown; lease until 2026-09-08T23:21:50Z
- 2026-09-09T01:00:00Z GREEN: `swift test --scratch-path .build-T0134` -> **30 tests in 4 suites passed**. `bash ops/check-pins --source-only` -> `PINS ok=5 skipped=9 pending=0 expired=0 failed=0`. `bash ops/queue-check` -> `QUEUE OK`. Line counts 127 / 95 / 237 / 318 - the three Swift files are under the 300 cap; the harness is over it and the Python cap only lands with T-0058 (PR #44), which is flagged below rather than pre-empted.
- 2026-09-09T01:00:00Z **THE MEAN IS THE PRODUCT DECISION AND IT IS PINNED WHERE IT ACTUALLY DIFFERS.** An arithmetic mean agrees with the geometric one whenever M and E are close, which is most fixtures, so a suite without a deliberately unbalanced case pins nothing. Built two: M=0.9/E=0.1 (a hairpin through a scrapyard) and M=0.1/E=0.9 (a straight road through redwoods). **Expected values computed by hand from the weights before running anything** - `0.9^0.35 * 0.1^0.65 = 0.9637955 * 0.2238721 = 0.2157672` and `0.1^0.35 * 0.9^0.65 = 0.4466839 * 0.9338075 = 0.4171165` - and both matched to 1e-5 on the first run, which is independent confirmation rather than a value read off the code. The arithmetic mean would give 0.38 and 0.62 for the same two roads, so each test also carries a bound the arithmetic answer fails.
- 2026-09-09T01:00:00Z A companion test records the trap rather than only avoiding it: at M=E=0.5 both means give exactly 0.5, so `balancedRoadHidesTheDifference` exists to stop somebody "simplifying" the mean, seeing a balanced fixture pass, and believing it.
- 2026-09-09T01:00:00Z **BOTH WEIGHT SETS ARE PROVED TO SUM TO ONE THROUGH THE FORMULA, not by adding the constants.** Adding `curvatureWeight + elevationGainWeight + ...` and checking the total asks each set about itself. Instead: every term at 1 must give M=1 and E=1, so the score must be exactly 1 - which holds only if each set sums to 1. Two mutations move a single weight so a set sums to 1.05; both caught by that one test without it knowing the split. The individual weights are *also* written out as literals, because the plan's tuning process will move them and a moved weight should be a deliberate act with a visible diff.
- 2026-09-09T01:00:00Z **A MOTORWAY SCORES ZERO AND IS NOT GATED - and this branch can only assert half of that.** `Gates` lives on `task/T-0133` and is not on `main`, so the paired assertion is impossible here. `motorwayScoresZero` pins the half this file owns (all four dull classes score 0 given the *best possible* terms, and an otherwise identical `secondary` road scores 1.0, so the rule is about the class and not about the fixture). The gate half is pinned in T-0133. **The pairing test belongs wherever those two first meet on one branch, and does not exist yet** - said here rather than implied.
- 2026-09-09T01:00:00Z Thresholds pinned strictly and on both sides: a tunnel of exactly 300 m is *not* penalised while 301 m is; a road exactly 150 m from a motorway is *not* penalised while 149 m is. Both mutations that relax `>` to `>=` are caught. The multipliers **compound** rather than replacing one another (0.5 x 0.15 x 0.7), and the mutation making them mutually exclusive is caught.
- 2026-09-09T01:00:00Z Absent surface follows the plan and never becomes evidence of unpaved: `residential` with no `surface` tag takes x0.8 **and** raises the flag; `tertiary` takes neither; a `residential` road that *does* carry a surface tag takes neither. The flag is a separate function from the score on purpose - the penalty is the scoring function's business and the flag is the hazard strip's, and a route can accumulate enough flagged distance to be worth a line on screen without any single way scoring badly.
- 2026-09-09T01:00:00Z Terms are **validated, not clamped**: a value outside `0...1`, a NaN, or a negative tunnel length returns nil. A plausible score computed from a wrong input is the hardest kind of error to find later, and `SegmentTerms.unitTerms` lists every unit term so a term added later cannot quietly escape validation - a mutation dropping one from that list is caught.
- 2026-09-09T01:00:00Z HARNESS `ops/mutate/segmentscore.py`: **31 of 31 caught by a named test**, 0 trapped, 0 compile-only, 0 MISSED, 0 skipped, exit 0. `--prove-vacuity` -> `caught=0 (need 0) and MISSED=31 of 31`, OK. Most mutations move a NUMBER, as the brief required - this is thirteen weights and two exponents, and a structural-only set would be blind exactly where it matters. Built on `ops/mutate/gates.py`, the only sibling carrying every correction (pass condition `caught == len(MUTATIONS)`, complete-MISSED vacuity over every test file, EQUIVALENT asserted the other way, and a **retried baseline build**).
- 2026-09-09T01:00:00Z **ONE MUTATION SCORED SKIP AND THE FIX WAS TO STOP ANCHORING ON A COMMENT.** "Swap the exponents" originally rewrote both declarations, which are separated by a doc comment, so the anchor spanned one - and CLAUDE.md forbids anchoring a guard on a comment precisely because a rewording breaks it silently. Re-expressed at the point of USE, `pow(m, sceneryExponent) * pow(e, driveExponent)`, which touches only identifiers. Caught.
- 2026-09-09T01:00:00Z **THE PLAN'S TWO WORKED NUMBERS ARE UNREPRODUCED, DELIBERATELY.** The plan quotes 0.32 for a curvy industrial road and 0.62 for a straight redwood one, but gives no term values that produce them. Reverse-engineering inputs to hit those targets and presenting the result as an oracle would be fitting the answer to the target - this repository already rejected an oracle for less (T-0011, where the first source disagreed with USNO). Every expected value here is hand-computed from the stated weights instead. The real oracle is the Curvature project's Vermont output, which arrives with the ETL.
- 2026-09-09T01:00:00Z NOT FIXED: `ops/mutate/segmentscore.py` is 318 lines. The 300-line cap reaches Python only when T-0058 (PR #44) lands, so P-SRC-02 is green today and will not be then - flagged rather than pre-emptively split, since the split should follow whatever shape that task settles on. Same note as T-0119.
- 2026-09-09T01:00:00Z moved to review/. Reviewer must not be agent/claude-opus-5 (`ops/queue-check`).
