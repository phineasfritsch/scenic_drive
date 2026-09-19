"""The mutation population for ops/mutate/geometry.py: what to break in the ETL geometry terms, which
CLASS of wrong implementation it stands for, and the named tests that must go red for it.

Split out of the runner exactly as budget_mutations.py is split out of budget.py: the runner is the
protocol, this file is the evidence it runs over, and geometry_arms.py holds the arm asserted the other
way round. The paths live here because both of those import them and importing them back out of the runner
would be a cycle.

WHY A CLASS FIELD, which budget_mutations.py does not have. PR #94 went FOUR review rounds on one shape -
"the fixture's geometry population is degenerate on axis X, so a mutant restricted to a subset of the
segment-pair matrix survives with nothing red" - refiled each round with a new X: single segment, then
collinear, then interior-interior, and a fifth axis (a banded window) recorded in the PASS entry rather
than bought as a round. Counting entries would not have stopped any of those rounds: each round's
population was complete by its own count and empty on the next axis. So the floor here is three-sided - a
literal count, a literal list of CLASSES every one of which must be populated, and a non-empty `killers` list
on every entry - and `REQUIRED_CLASSES` is the reviewer's must-enumerate list as much as the fixer's brief.

Each entry is `(class, label, rel, old, new, killers)`. `old` must appear EXACTLY ONCE in the pristine file
or the run refuses: a stale anchor is never silently a pass. **Anchor on code, never on a comment**
(CLAUDE.md) - comments get stripped and a mutation anchored on one dies quietly. `killers` names the tests
that must go red; a mutation caught by some other test is reported as a failure, because that other test is
not the check the label claims exists. A parametrised killer is named WITHOUT its `[case]` suffix and the
runner matches every parametrisation of it. An EMPTY `killers` list is refused by the floor, by name, before
any pytest runs: 0 named red of 0 named is the guard `len(red) != len(killers)` satisfied vacuously, and a
mutation nobody is required to catch is not a measurement (rv1-pr107 on PR #107).
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
ETL = ROOT / "services" / "etl"

# Relative to the COPY the runner builds; `services/etl` itself is never written.
PROX = "etl/proximity.py"
SINU = "etl/sinuosity.py"
SNAP = "etl/snap.py"

# The suites every run executes. Not the whole ETL suite: these are the files that are the CHECK on the
# three subjects, and a mutation killed by, say, test_score_contract.py would be killed by a neighbour
# tripping over the same edit rather than by the check its label claims exists.
TEST_FILES = ["tests/test_sinuosity.py", "tests/test_proximity.py", "tests/test_proximity_bends.py",
              "tests/test_proximity_interior.py", "tests/test_proximity_banded.py", "tests/test_snap.py"]

# The SIX classes, each with the review round that bought it. Every one of them must be populated or the
# run refuses NAMING the class - see `population_ok` in the runner.
REQUIRED_CLASSES = (
    "segment-subset",        # rounds 1-2: a subset of one line's segments (first only, last only, all-but-last)
    "chord-for-path",        # round 2: a polyline replaced by its first-to-last chord
    "candidate-order",       # the ties: which candidate wins, and whether the radius is inclusive
    "interior-interior",     # round 3: the pair cell interior to BOTH polylines, and the retracted ruling
    "earth-model",           # the projection constant, and the tag normalisation before the allowlist
    "banded-subset",         # round 4 (rv4-pr94's PASS entry): |i - j| <= 1, a monotone sweep's window
)

# --- anchors, each shared by more than one mutation or long enough to be worth naming ------------------

# The whole of `line_distance_m`'s answer: the double comprehension over the segment-pair MATRIX. Four
# mutations rewrite it and one equivalent entry reorders its arguments.
PAIR_LOOP = ("    return min(segment_distance_m(a, b, c, d)\n"
             "               for a, b in zip(line, line[1:])\n"
             "               for c, d in zip(other, other[1:]))")

# The indexed form both matrix-subset mutants are written in. `n, m` are the segment counts.
INDEXED = ("    n, m = len(line) - 1, len(other) - 1\n"
           "    return min(segment_distance_m(line[i], line[i + 1], other[j], other[j + 1])\n"
           "               for i in range(n)\n"
           "               for j in range(m)%s)")

# The one line of `meters_to_nearest_motorway` that combines the candidates.
NEAREST = "        nearest = min(nearest, line_distance_m(coords, motorway))"

MUTATIONS = [
    # --- segment subset: a subset of ONE line's segments ------------------------------------------------
    ("segment-subset", "line_distance_m walks only the WAY's first segment", PROX, PAIR_LOOP,
     PAIR_LOOP.replace("for a, b in zip(line, line[1:])", "for a, b in [(line[0], line[1])]"),
     ["test_the_nearest_approach_may_be_on_a_later_segment_of_the_way",
      "test_the_way_may_bend_toward_the_motorway_between_its_end_nodes"]),

    ("segment-subset", "line_distance_m walks only the WAY's last segment", PROX, PAIR_LOOP,
     PAIR_LOOP.replace("for a, b in zip(line, line[1:])", "for a, b in [(line[-2], line[-1])]"),
     ["test_the_way_may_bend_toward_the_motorway_between_its_end_nodes"]),

    ("segment-subset", "snap.length_m drops the way's LAST segment (every-but-last)", SNAP,
     "    return sum(distance_on_earth(a[0], a[1], b[0], b[1]) for a, b in zip(line, line[1:]))",
     "    return sum(distance_on_earth(a[0], a[1], b[0], b[1]) for a, b in zip(line, line[1:-1]))",
     ["test_a_multi_segment_tunnel_is_measured_end_to_end", "test_the_sinuosity_matches_the_fixture"]),

    # --- chord for path: the polyline replaced by the straight line between its ends ---------------------
    ("chord-for-path", "tunnel_meters measures the bore's chord, not its path", PROX,
     "    return length_m(coords) if is_tunnel(tags) else 0.0",
     "    return length_m([coords[0], coords[-1]]) if is_tunnel(tags) else 0.0",
     # NOT `test_a_multi_segment_tunnel_is_measured_end_to_end`, and the first run of this harness is why:
     # that test's bore is one of the three COLLINEAR_BY_DESIGN geometries, drawn on a single meridian, so
     # its path and its chord are the same number and it stayed green under this mutant. A killer named
     # here that does not go red is a FAILURE (see `wrong_killer`), which is how the claim was corrected.
     ["test_the_bore_measures_its_path_and_not_its_chord",
      "test_a_bent_bore_crosses_the_threshold_only_along_its_path"]),

    ("chord-for-path", "the CANDIDATE motorway is reduced to its chord before it is measured", PROX,
     NEAREST, "        nearest = min(nearest, line_distance_m(coords, [motorway[0], motorway[-1]]))",
     ["test_the_metres_to_the_nearest_motorway_match_the_fixture"]),

    ("chord-for-path", "way_sinuosity's NUMERATOR becomes the chord, so every way reads 1.0", SINU,
     "    return length_m(coords) / gap", "    return length_m([coords[0], coords[-1]]) / gap",
     ["test_the_sinuosity_matches_the_fixture",
      "test_the_term_is_raw_and_unbounded_not_a_0_to_1_score"]),

    # --- candidate order and ties -----------------------------------------------------------------------
    ("candidate-order", "the LAST candidate wins instead of the nearest one", PROX, NEAREST,
     "        nearest = line_distance_m(coords, motorway)",
     ["test_the_candidate_order_cannot_change_the_answer"]),

    ("candidate-order", "the reporting radius becomes exclusive - a tie at the radius reads inf", PROX,
     "    return nearest if nearest <= radius_m else math.inf",
     "    return nearest if nearest < radius_m else math.inf",
     ["test_the_radius_is_inclusive"]),

    # --- interior-interior: the pair cell interior to BOTH polylines (review round 3) -------------------
    ("interior-interior", "drop the pairs interior to BOTH lines - round 3's retracted 'equivalent'", PROX,
     PAIR_LOOP, INDEXED % " if i in (0, n - 1) or j in (0, m - 1)",
     ["test_the_nearest_approach_may_need_a_segment_interior_to_both_polylines",
      "test_the_pairs_that_touch_an_end_segment_all_read_past_the_proximity_threshold"]),

    # --- earth model and normalisation ------------------------------------------------------------------
    ("earth-model", "metres per degree of latitude becomes the equatorial 111234.7", SNAP,
     "    ky = 110540.0", "    ky = 111234.7",
     ["test_the_way_may_bend_toward_the_motorway_between_its_end_nodes",
      "test_the_nearest_approach_may_need_a_segment_interior_to_both_polylines"]),

    ("earth-model", "is_tunnel consults the allowlist without stripping or lowercasing", PROX,
     "    return value.strip().lower() in TUNNEL_VALUES", "    return value in TUNNEL_VALUES",
     ["test_the_tunnel_metres_match_the_fixture", "test_is_tunnel_agrees_with_the_metres"]),

    # --- banded subset: the window a monotone sweep would have (rv4-pr94) -------------------------------
    ("banded-subset", "keep only the segment pairs with abs(i - j) <= 1 - rv4-pr94's sixth class", PROX,
     PAIR_LOOP, INDEXED % " if abs(i - j) <= 1",
     ["test_the_minimum_can_sit_far_off_the_diagonal_of_the_segment_pair_matrix",
      "test_the_banded_window_answers_inf_where_the_whole_matrix_answers_99_metres"]),
]

# A LITERAL, never `len(MUTATIONS)`: a floor computed from the list it guards moves down with the list and
# refuses nothing, which is this repository's signature defect wearing the clothes of a fix. It is the EXACT
# length, so deleting ONE entry refuses - a floor of 8 against 12 would let a third of the population be
# trimmed and still print a clean sheet, which is what MIN_MUTATIONS = 22 against 34 did in budget.py until
# the third review of PR #73 said a floor that does not refuse what it documents is not a floor.
MIN_MUTATIONS = 12
