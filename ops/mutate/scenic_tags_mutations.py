"""The mutation POPULATION for ops/mutate/scenic_tags.py: what to break in `tagwriter` and `scenecheck`.

Split out of the runner exactly as `geometry_mutations.py` is split out of `geometry.py` and
`budget_mutations.py` out of `budget.py`: the runner is the protocol - what a verdict is and what refuses -
and this file is the evidence it runs over. The split happened when T-0204's second round took the runner
to the 300-line cap; the boundary is meaning, not a line number. The paths live HERE because the runner
imports them back out, and importing them the other way would be a cycle.

Each entry is `(name, file, old, new)`. `old` must appear VERBATIM in the pristine file or the run reports
SKIP and FAILS - a stale anchor is a harness that has gone quietly blind. **Anchor on code, never on a
comment** (CLAUDE.md): comments get stripped and a mutation anchored on one dies without a sound.

T-0204 R5 adds the seven at the bottom of MUTATIONS: the unit score - the number this task's whole
predicate is read on, and the number that had no contract at all until the oracle grew one.

T-0207 adds `assemble.py` as a THIRD subject and nine mutations, floor 35 -> 44. R1 puts the class ceiling
there - the number that decides what `tagwriter` then writes for a residential, living_street or service
way - and R2 makes the integer and the unit one number in `tags_for_row`. A module that computes a number
ships a population, and the number the tags carry is now computed in two files, so both are subjects.

T-0207 R3 adds four more, floor 44 -> 48: the ceiling CONDITIONED ON AN INPUT. The pre-review mutant pass
ran two of them unwritten and both SURVIVED - `and value < 0.75` and `and record.byway_status is None` - so
the class is now shipped whole, one mutation per input `scored_row` can read (the score's magnitude, the
byway status, a term, the surface), rather than one spelling at a time (PR #101's precedent).
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
ETL = ROOT / "services" / "etl"
TAGWRITER = ETL / "etl" / "tagwriter.py"
SCENECHECK = ETL / "etl" / "scenecheck.py"
ASSEMBLE = ETL / "etl" / "assemble.py"
TAGWRITER_TESTS = ETL / "tests" / "test_tagwriter.py"
SCENECHECK_TESTS = ETL / "tests" / "test_scenecheck.py"
SCENECHECK_UNIT_TESTS = ETL / "tests" / "test_scenecheck_unit.py"
CLASS_CAP_TESTS = ETL / "tests" / "test_class_cap.py"
ASSEMBLE_TESTS = ETL / "tests" / "test_assemble.py"
ASSEMBLE_WIRING_TESTS = ETL / "tests" / "test_assemble_wiring.py"
COUNTS_TESTS = ETL / "tests" / "test_counts.py"
EMPTIED = (TAGWRITER_TESTS, SCENECHECK_TESTS, SCENECHECK_UNIT_TESTS, CLASS_CAP_TESTS, ASSEMBLE_TESTS,
           ASSEMBLE_WIRING_TESTS, COUNTS_TESTS)
SUBJECTS = (TAGWRITER, SCENECHECK, ASSEMBLE)

# Anchors reused by more than one mutation, verbatim from the subjects.
QUANTISE = "    scaled = math.floor(number * SCORE_SCALE + 0.5)"
CLAMP = "    return max(SCORE_MIN, min(SCORE_MAX, scaled))"
NOT_A_ROAD = "    if not tags.get(HIGHWAY):\n        counts[\"not_a_road\"] += 1\n        return"
GATE_TAG = "    if row.get(\"gate_reason\"):\n        out[KEY_GATE] = row[\"gate_reason\"]"
NULL_ROW = "        if row.get(\"score\") is None:"
FLAGS_JOIN = "        out[KEY_FLAGS] = FLAG_SEPARATOR.join(flags)"
WRITE_LOOP = ("    with osmxml.Writer(out) as writer:\n"
              "        for elem in osmxml.iter_top_level(source):\n"
              "            if elem.tag == osmxml.WAY:\n"
              "                _tag_way(elem, scored, refused, counts, seen)\n"
              "            writer.write(elem)")
MISSING = "    missing = sorted((set(scored) | set(refused)) - seen)"
NEITHER = "    raise ValueError(\"way %d carries highway=%s and is in neither the scored table nor the "
CHECK_NOT_A_ROAD = "    if not tags.get(HIGHWAY):\n        return (NOT_A_ROAD, None)"
CHECK_REFUSED = "        return (REFUSED, None) if refused else (NULL_SCORE, None)"
CHECK_GATED = "        elif kind == SCORED and detail > 0 and is_gated(tags):"
# T-0204 R1: the read-back oracle's own contract - the range, the ranking's source of truth, and the
# parse that used to raise.
CHECK_RANGE = "    if not tagwriter.SCORE_MIN <= value <= tagwriter.SCORE_MAX:"
TOP_KIND = ("        kind, detail = classify(way_id, tags)\n"
            "        if kind != SCORED:\n"
            "            continue")
INTEGER_OR_NONE = "    return int(text) if digits.isascii() and digits.isdigit() else None"
IS_GATED = "    return tags.get(HIGHWAY) in ZERO_CLASSES or gate_reason(tags) is not None"
REFUSES = ("    return found[\"null_score\"] > 0 or found[\"gated_scored\"] > 0"
           " or found[\"malformed\"] > 0")
SORT = "    rows.sort(key=lambda r: (-r[\"scenic_score\"], -r[\"scenic_score_unit\"], r[\"way_id\"]))"
MIDDLE = "    return coords[len(coords) // 2]"
# T-0204 R5: the unit score's five rules, in `classify` and `unit_or_none`.
UNIT_TAG = "    raw_unit = tags.get(tagwriter.KEY_UNIT)"
UNIT_RANGE = "    if not UNIT_MIN <= unit <= UNIT_MAX:"
UNIT_QUANTISES = "    if tagwriter.quantise(unit) != value:"
UNIT_PARSE = "    try:\n        number = float(text)\n    except ValueError:\n        return None"
UNIT_NAN = "    return None if number != number else number"
UNIT_ASCII = "    if not text.isascii():\n        return None"
# T-0207 R2: the two tags are ONE number. The unit string is made first and the integer is quantised from
# what it carries, so `scenecheck`'s `quantise(unit) == score` clause holds by construction.
ONE_NUMBER = ("    unit = fixed(row[\"score\"])\n"
              "    out = {KEY_SCORE: str(quantise(float(unit))), KEY_UNIT: unit}")
# T-0207 R1: the class ceiling, in the assembly beside the safety gate - the plan's anti-rat-run clause
# only demotes a RESIDENTIAL way scoring BELOW 7, so a capped class must never reach 7.
CEILING_TABLE = "CLASS_SCORE_CEILING = {\"residential\": 0.6499, \"living_street\": 0.6499, \"service\": 0.0}"
CEILING_LOOKUP = "    ceiling = CLASS_SCORE_CEILING.get(record.highway)"
CEILING_MIN = "        value = min(value, ceiling)"
# T-0207 R3: the guard the ceiling is applied under. The pre-review mutant pass found that it can be
# CONDITIONED ON AN INPUT with nothing going red, so the four inputs `scored_row` can read on its way here -
# the score's magnitude, the byway status, a term and the surface - are one mutation class of their own.
CEILING_GUARD = "    if ceiling is not None and value is not None:"

MUTATIONS = [
    # --- the quantisation, ruling R1 of T-0168 -------------------------------------------------------
    ("truncate instead of rounding half up", TAGWRITER, QUANTISE,
     "    scaled = math.floor(number * SCORE_SCALE)"),
    ("round half to even, which is what `round` does", TAGWRITER, QUANTISE,
     "    scaled = round(number * SCORE_SCALE)"),
    ("round half DOWN", TAGWRITER, QUANTISE,
     "    scaled = math.ceil(number * SCORE_SCALE - 0.5)"),
    ("scale to 0..100, past the four bits the router holds", TAGWRITER, "SCORE_SCALE = 10",
     "SCORE_SCALE = 100"),
    ("stop at 9, so a perfect road cannot say so", TAGWRITER, "SCORE_MAX = 10", "SCORE_MAX = 9"),
    ("drop the clamp, so a term bug upstream becomes a value the router cannot hold", TAGWRITER, CLAMP,
     "    return scaled"),
    ("write the terms at two decimals instead of four", TAGWRITER, "TERM_PRECISION = 4",
     "TERM_PRECISION = 2"),

    # --- what lands on a way, rulings R1 and R2 ------------------------------------------------------
    ("stop naming the gate that fired", TAGWRITER, GATE_TAG, "    if False:\n        pass"),
    ("write a refused row as a silent 0 - the exact defect R2 forbids", TAGWRITER, NULL_ROW,
     "        if False:"),
    ("tag a park as if it were a road", TAGWRITER, NOT_A_ROAD, "    if not tags.get(HIGHWAY):\n"
     "        counts[\"not_a_road\"] += 1"),
    ("let the population shrink between two stages", TAGWRITER, MISSING, "    missing = []"),
    ("let a road the table never saw through untagged", TAGWRITER, NEITHER,
     "    return\n    raise ValueError(\"way %d carries highway=%s and is in neither the scored table nor the "),
    ("count a gated way as ungated in the write line", TAGWRITER,
     "        if row.get(\"gate_reason\"):\n            counts[\"gated\"] += 1",
     "        if False:\n            counts[\"gated\"] += 1"),

    # --- the order of the shipped bytes, ruling R3 (P-DATA-01) ---------------------------------------
    # Both are invisible to two writes inside ONE interpreter: one hash seed makes the pair agree with each
    # other and disagree with the next process. The P-DATA-01 test writes its second file in a child.
    ("emit the ways in hash order instead of input order", TAGWRITER, WRITE_LOOP,
     "    held = []\n"
     "    with osmxml.Writer(out) as writer:\n"
     "        for elem in osmxml.iter_top_level(source):\n"
     "            if elem.tag == osmxml.WAY:\n"
     "                _tag_way(elem, scored, refused, counts, seen)\n"
     "                held.append(__import__(\"copy\").deepcopy(elem))\n"
     "                continue\n"
     "            writer.write(elem)\n"
     "        for elem in sorted(held, key=lambda way: hash(way.get(\"id\"))):\n"
     "            writer.write(elem)"),
    ("join the flags out of a set, which has no order", TAGWRITER, FLAGS_JOIN,
     "        out[KEY_FLAGS] = FLAG_SEPARATOR.join(set(flags))"),

    # --- check 4's two clauses -----------------------------------------------------------------------
    ("only object to a gated way scoring above 5", SCENECHECK, CHECK_GATED,
     "        elif kind == SCORED and detail > 5 and is_gated(tags):"),
    # The clause is `> 0`. Every gated fixture carried 3 or 7, so `> 1` passed 26 tests: a shipped PBF with
    # a motorway at 1 printed gated_scored=0 and exited 0.
    ("only object to a gated way scoring above 1", SCENECHECK, CHECK_GATED,
     "        elif kind == SCORED and detail > 1 and is_gated(tags):"),
    ("forget that motorway and trunk are a clause of their own", SCENECHECK, IS_GATED,
     "    return gate_reason(tags) is not None"),
    ("forget the safety gates, keeping only the zero classes", SCENECHECK, IS_GATED,
     "    return tags.get(HIGHWAY) in ZERO_CLASSES"),
    ("count a refused way as a hole in the scores", SCENECHECK, CHECK_REFUSED,
     "        return (NULL_SCORE, None)"),
    ("mistake the name tag for the highway tag when deciding what a road is", SCENECHECK,
     CHECK_NOT_A_ROAD,
     "    if not tags.get(NAME):\n        return (NOT_A_ROAD, None)"),
    ("refuse on the first clause only", SCENECHECK, REFUSES, "    return found[\"null_score\"] > 0"),

    # --- T-0204 R1: the third clause, and the two halves that must give one answer -------------------
    # Each was demonstrated red on a hand-built read-back file before the hardening existed.
    ("accept a score outside the 0..10 the router can hold - a tertiary at 42 ranks #1", SCENECHECK,
     CHECK_RANGE, "    if False:"),
    ("let the ranking decide for itself instead of asking classify - the two halves drift apart",
     SCENECHECK, TOP_KIND,
     "        raw = tags.get(tagwriter.KEY_SCORE)\n"
     "        if raw is None:\n"
     "            continue\n"
     "        detail = int(raw)"),
    ("let a non-integer score raise instead of naming the way - a crash is not a refusal", SCENECHECK,
     INTEGER_OR_NONE, "    return int(text)"),
    ("report the failure with a zero exit code", SCENECHECK, "REFUSAL_EXIT = 4", "REFUSAL_EXIT = 0"),
    ("rank the ways from worst to best", SCENECHECK, SORT,
     "    rows.sort(key=lambda r: (r[\"scenic_score\"], r[\"scenic_score_unit\"], r[\"way_id\"]))"),
    ("give the human the way's first node instead of its middle one", SCENECHECK, MIDDLE,
     "    return coords[0]"),

    # --- T-0204 R5: the UNIT, which is the number the window predicate is read on --------------------
    ("fall back to the integer when the unit is absent - the ranking used to, silently", SCENECHECK,
     UNIT_TAG, "    raw_unit = tags.get(tagwriter.KEY_UNIT, \"%.4f\" % (value / 10.0))"),
    ("accept a unit outside 0..1 - a unit score that is not a unit", SCENECHECK, UNIT_RANGE,
     "    if False:"),
    ("stop requiring the unit to quantise to the integer beside it - two tags, two scores", SCENECHECK,
     UNIT_QUANTISES, "    if False:"),
    ("restate the quantisation here instead of calling the writer's own", SCENECHECK, UNIT_QUANTISES,
     "    if int(unit * 10 + 0.5) != value:"),
    ("let a non-numeric unit raise instead of naming the way", SCENECHECK, UNIT_PARSE,
     "    number = float(text)"),
    ("accept a non-ASCII digit in the unit - `float(\"\\u0660.\\u0665\")` is 0.5 to Python", SCENECHECK,
     UNIT_ASCII, "    if False:\n        return None"),
    ("accept a non-ASCII digit in the integer - `int(\"\\u0667\")` is 7 to Python", SCENECHECK,
     INTEGER_OR_NONE, "    return int(text) if digits.isdigit() else None"),

    # --- T-0207 R2: one number, written twice ---------------------------------------------------------
    ("quantise the UNROUNDED score beside a unit rounded to four decimals - the shipped defect, 17 of "
     "46,436 real ways", TAGWRITER, ONE_NUMBER,
     "    unit = fixed(row[\"score\"])\n"
     "    out = {KEY_SCORE: str(quantise(row[\"score\"])), KEY_UNIT: unit}"),
    ("re-derive the unit from the integer, so the tag no longer carries the score", TAGWRITER, ONE_NUMBER,
     "    unit = fixed(row[\"score\"])\n"
     "    out = {KEY_SCORE: str(quantise(float(unit))), KEY_UNIT: fixed(quantise(float(unit)) / 10.0)}"),

    # --- T-0207 R1: the class ceiling ------------------------------------------------------------------
    ("drop the ceiling, so a Bel Air cul-de-sac is a 7 again and the rat-run clause never fires",
     ASSEMBLE, CEILING_MIN, "        value = max(value, 0.0)"),
    ("raise the ceiling BY one step of the tag's precision, onto the band itself", ASSEMBLE, CEILING_TABLE,
     "CLASS_SCORE_CEILING = {\"residential\": 0.65, \"living_street\": 0.65, \"service\": 0.0}"),
    ("cap a service way instead of zeroing it - 559 fire roads and parking aisles keep a 6", ASSEMBLE,
     CEILING_TABLE,
     "CLASS_SCORE_CEILING = {\"residential\": 0.6499, \"living_street\": 0.6499, \"service\": 0.6499}"),
    ("forget residential, which is the class the plan's clause names", ASSEMBLE, CEILING_TABLE,
     "CLASS_SCORE_CEILING = {\"living_street\": 0.6499, \"service\": 0.0}"),
    ("forget living_street, the class no real row exercises", ASSEMBLE, CEILING_TABLE,
     "CLASS_SCORE_CEILING = {\"residential\": 0.6499, \"service\": 0.0}"),
    ("cap unclassified too, which deletes Franklin Canyon Drive from the top ten", ASSEMBLE, CEILING_TABLE,
     "CLASS_SCORE_CEILING = {\"residential\": 0.6499, \"living_street\": 0.6499, \"service\": 0.0,\n"
     "                       \"unclassified\": 0.6499}"),
    ("read the ceiling off the gate reason instead of the class, so it never finds one", ASSEMBLE,
     CEILING_LOOKUP, "    ceiling = CLASS_SCORE_CEILING.get(reason)"),

    # --- T-0207 R3: the ceiling CONDITIONED ON AN INPUT. The two the pre-review pass found survived, and
    # the other two inputs of the same class. Each demotes some rows and lets others through, which is why a
    # fixture of five ways all at 0.72, no byway and one surface could not see any of them.
    ("demote only the sevens - a residential at raw 1.0 ships 10 (pre-review survivor M2)", ASSEMBLE,
     CEILING_GUARD, "    if ceiling is not None and value is not None and value < 0.75:"),
    ("no ceiling on a way that matched a byway - a residential stub in Topanga ships 10 (survivor M5)",
     ASSEMBLE, CEILING_GUARD,
     "    if ceiling is not None and value is not None and record.byway_status is None:"),
    ("condition the ceiling on a TERM, so a cul-de-sac under full canopy keeps its 7", ASSEMBLE,
     CEILING_GUARD, "    if ceiling is not None and value is not None and record.canopy < 0.9:"),
    ("condition the ceiling on the SURFACE, so every asphalt rat-run escapes it", ASSEMBLE, CEILING_GUARD,
     "    if ceiling is not None and value is not None and record.surface != \"asphalt\":"),
]

# Cannot change behaviour, so anything but MISSED is a FAILURE. Each has a witness in its name.
EQUIVALENT = [
    ("clamp the other way round - min(MAX, max(MIN, x)) is max(MIN, min(MAX, x)) for MIN < MAX", TAGWRITER,
     CLAMP, "    return min(SCORE_MAX, max(SCORE_MIN, scaled))"),
    ("format with `format` instead of the % operator - same digits for every float", TAGWRITER,
     "    return \"%.*f\" % (TERM_PRECISION, float(value))",
     "    return format(float(value), \".%df\" % TERM_PRECISION)"),
    # WITNESS: `classify` asks the range next, and every comparison against NaN is False, so
    # `not UNIT_MIN <= nan <= UNIT_MAX` is True and a NaN unit is malformed either way. The guard is kept
    # so `unit_or_none` never hands a NaN to a FUTURE caller that does not check a range first; it cannot
    # change what this module answers today, so a catch here would be a test with an opinion about how the
    # function is written.
    ("let a NaN unit through the parse - the range clause rejects it anyway, every comparison being False",
     SCENECHECK, UNIT_NAN, "    return number"),
]

# Asserted the other way round: each must still go MISSED, and a gap that CLOSES fails the run so it gets
# promoted into MUTATIONS. Empty is a claim, not an omission.
KNOWN_MISSED = []

MIN_MUTATIONS = 48
