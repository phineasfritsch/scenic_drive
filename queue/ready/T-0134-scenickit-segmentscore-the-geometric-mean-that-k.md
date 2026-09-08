---
id: T-0134
title: "ScenicKit SegmentScore: the geometric mean that keeps a curvy industrial road apart from a straight redwood one"
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/Scoring/, Tests/ScenicKitTests/, ops/mutate/]
pins_affected: []
reviewer: null
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
