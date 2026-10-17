"""The mutation population for T-0218's class ceiling on the device: Sources/ScenicKit/Scoring/SegmentScoreCeiling.swift.
The driver is segmentceiling.py and the runner segmentceiling_run.py.

## What each entry holds

  * the CEILING APPLIED - entries 1, 2 and 13 (dropped, max for min, a ceiling an epsilon high);
  * a REFUSAL STAYS A REFUSAL - entries 3-4 (the ceiling or zero in place of nil);
  * the TABLE IS THE ETL's - entries 5-8 (a value moved, a class dropped, the service zero raised, a class the
    ETL does not cap added), killed by the table read out of assemble.py by identifier and by the bound table;
  * the LOOKUP IS EXACT, as Python's `dict.get` is - entries 9-10 (lowercased, trimmed), killed by the
    near-miss class strings of the bound table;
  * the CEILING IS UNCONDITIONAL - entries 11, 12 and 14 (conditioned on the byway tier, the surface or the
    score's magnitude: T-0207 R3's two survivors on the ETL side, restated for the device).

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

CEILING = ROOT / "Sources" / "ScenicKit" / "Scoring" / "SegmentScoreCeiling.swift"
SUBJECTS = (CEILING,)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "ScenicKitTests" / "SegmentScoreCeilingTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "SegmentScoreContractTests.swift")

APPLY = "return min(formula, ceiling)"
REFUSE = "guard let formula = SegmentScore.score(for: t) else { return nil }"
LOOKUP = "guard let ceiling = byClass[t.highway] else { return formula }"
RESIDENTIAL = '"residential": 0.6499'
LIVING = '"living_street": 0.6499, '
SERVICE = '"service": 0.0]'

TABLE = "the ceiling table is assemble.CLASS_SCORE_CEILING, parsed by identifier"
BOUND = "every class x bound x tier x surface is min(formula, the ETL ceiling), exactly"
REFUSED = "refused terms stay refused on every ceiling class, never the ceiling"
POST = "every fixture row's shown score is the router's post-ceiling number within 1e-6"

MUTATIONS = [
    # 1-2. The ceiling applied at all, and the right way round.
    ("the ceiling dropped: the formula shown uncapped", CEILING, APPLY, "return formula", [BOUND, POST]),
    ("max for min: every capped class shown at least at its ceiling", CEILING, APPLY,
     "return max(formula, ceiling)", [BOUND, POST]),
    # 3-4. A refusal is never turned into a number.
    ("a refused way shown at its class ceiling", CEILING, REFUSE,
     "guard let formula = SegmentScore.score(for: t) else { return byClass[t.highway] }", [REFUSED]),
    ("a refused way shown as zero", CEILING, REFUSE,
     "guard let formula = SegmentScore.score(for: t) else { return 0 }", [REFUSED]),
    # 5-8. The table is the ETL's, value for value and key for key.
    ("residential raised to 0.65, which the quantiser sends to the band of 7", CEILING, RESIDENTIAL,
     '"residential": 0.65', [TABLE, BOUND]),
    ("living_street dropped from the table", CEILING, LIVING, "", [TABLE, BOUND]),
    ("service raised from 0.0 to 0.6499", CEILING, SERVICE, '"service": 0.6499]', [TABLE, BOUND, POST]),
    ("unclassified capped on the device, which the ETL does not cap", CEILING, SERVICE,
     '"service": 0.0, "unclassified": 0.6499]', [TABLE, BOUND]),
    # 9-10. The lookup is exact.
    ("the class lowercased before the lookup", CEILING, LOOKUP,
     "guard let ceiling = byClass[t.highway.lowercased()] else { return formula }", [BOUND]),
    ("the class trimmed before the lookup", CEILING, LOOKUP,
     "guard let ceiling = byClass[t.highway.trimmingCharacters(in: .whitespaces)] else { return formula }",
     [BOUND]),
    # 11-12, 14. The ceiling conditioned on an input the score reads.
    ("the ceiling skipped on a byway", CEILING, LOOKUP,
     "guard let ceiling = byClass[t.highway], t.bywayTier == .none else { return formula }", [BOUND]),
    ("the ceiling skipped on an unsurveyed way", CEILING, LOOKUP,
     "guard let ceiling = byClass[t.highway], t.surface != nil else { return formula }", [BOUND]),
    # 13.
    ("the ceiling an epsilon high", CEILING, APPLY, "return min(formula, ceiling + 0.0001)", [BOUND]),
    ("the ceiling applied only below 0.75, so a perfect residential way shows 1.0", CEILING, LOOKUP,
     "guard let ceiling = byClass[t.highway], formula < 0.75 else { return formula }", [BOUND]),
]

# `(name, path, old, new, witness)`: anything but MISSED fails the run.
EQUIVALENT = [
    ("min written as a conditional", CEILING, APPLY, "return formula > ceiling ? ceiling : formula",
     "`formula` is never NaN - SegmentScore.score(for:) refuses every non-finite or out-of-range input and "
     "returns products of pow() over [0, 1] and positive literals - and `ceiling` is a table literal, so for "
     "two non-NaN doubles min(a, b) and (a > b ? b : a) return the same value, equality included."),
    ("min's arguments swapped", CEILING, APPLY, "return min(ceiling, formula)",
     "Swift.min over two non-NaN doubles is symmetric in VALUE; the one asymmetry, -0.0 against 0.0, needs a "
     "negative zero, and `formula` is a product of non-negative factors (pow of [0, 1], the 0 literal for a "
     "dull class, positive multipliers), which IEEE 754 makes +0.0."),
]

# Literal floors: the real counts. Adding a mutation means editing this number in the same diff.
MIN_MUTATIONS = 14
MIN_EQUIVALENT = 2
MIN_TEST_FILES = 2
