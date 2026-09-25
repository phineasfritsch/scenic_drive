"""The mutation POPULATION for ops/mutate/normalise.py: what to break in the region's ranking.

Split from the runner exactly as `scenic_tags_mutations.py` is split from `scenic_tags.py`: the runner is
the protocol - what a verdict is and what refuses - and this file is the evidence it runs over.

WHY THESE MODULES. `normalise.py` computes the rank every scored term is made of and sat in P-PROC-06's DEBT
list with no population at all. `region_reference.py` is T-0208's new module: it decides WHICH ways are in
the curve a rank is taken against, which is the same number one step earlier. `assemble.py` is mutated here
too - for the library line that passes the reference on and the CLI line that reads `--reference` - but is
declared in `scenic_tags.py`'s SUBJECT_MODULES, not in this one, so P-PROC-06 sees one declaration per module.
`waydoc.py` is mutated for its CLI line that reads `--motorways` (rv1-t0208 B2) and is declared by no
population: P-PROC-06 allowlists it as wiring, and it refuses an allowlist entry a population also declares.

Each entry is `(name, file, old, new)`. `old` must appear VERBATIM in the pristine file or the run reports
SKIP and FAILS. **Anchor on code, never on a comment** (CLAUDE.md): comments get stripped and a mutation
anchored on one dies without a sound. `ranks_against_sorted` and `ranks_against` share four lines character
for character, so the divisor mutation anchors on a five-line block that only the bisect form has - a
one-line anchor there would have silently mutated the linear function the fast one is measured against.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
ETL = ROOT / "services" / "etl"
NORMALISE = ETL / "etl" / "normalise.py"
REFERENCE = ETL / "etl" / "region_reference.py"
ASSEMBLE = ETL / "etl" / "assemble.py"
WAYDOC = ETL / "etl" / "waydoc.py"
NORMALISE_TESTS = ETL / "tests" / "test_normalise.py"
REFERENCE_TESTS = ETL / "tests" / "test_region_reference.py"
SEAM_TESTS = ETL / "tests" / "test_seam_one_score.py"
WAY_RECORD_TESTS = ETL / "tests" / "test_way_records_fixture.py"
MOTORWAY_TESTS = ETL / "tests" / "test_motorway_source.py"
EMPTIED = (NORMALISE_TESTS, REFERENCE_TESTS, SEAM_TESTS, WAY_RECORD_TESTS, MOTORWAY_TESTS)
SUBJECTS = (NORMALISE, REFERENCE, ASSEMBLE, WAYDOC)

# Anchors reused by more than one mutation, verbatim from the subjects.
CHOOSE_REFERENCE = "            ranks[term] = ranks_against_sorted(values, sorted(reference[term]))"
BELOW = "        below = bisect.bisect_left(reference, value)"
EQUAL = "        equal = bisect.bisect_right(reference, value) - below + 1"
# The only five lines that belong to the BISECT ranker and not to the linear one it must equal.
DIVISOR = ("    population = len(reference) + 1\n"
           "    out: dict = {}\n"
           "    for way_id in ranked_order(values):\n"
           "        value = values[way_id]\n"
           "        below = bisect.bisect_left(reference, value)")
DIVISOR_MUTANT = ("    population = len(reference)\n"
                  "    out: dict = {}\n"
                  "    for way_id in ranked_order(values):\n"
                  "        value = values[way_id]\n"
                  "        below = bisect.bisect_left(reference, value)")
ORDER = "    for way_id in ranked_order(values):\n        value = values[way_id]\n        below = bisect."
POPULATION = "    population = population_of(records)"
ANSWERING = "    return {term: {record.way_id: float(getattr(record, term)) for record in answering(term, population)}"
FIRST_WINS = "                out[term].setdefault(way_id, value)"
SORTED_TABLE = "    return {term: sorted(float(value) for value in (values.get(term) or {}).values())"
COUNTS = "    return {term: len(table[term]) for term in sorted(table)}"
CANONICAL = "    return json.dumps(table, sort_keys=True, separators=(\",\", \":\"))"
DUMP_REFUSES = ("    problems = reference_refusals(table)\n"
                "    if problems:\n"
                "        raise ValueError(\"reference refused: %s\" % \"; \".join(problems))\n"
                "    if path is not None:")
LOAD_REFUSES = ("    problems = reference_refusals(table)\n"
                "    if problems:\n"
                "        raise ValueError(\"reference refused: %s\" % \"; \".join(problems))\n"
                "    return {term: [float(value) for value in values] for term, values in table.items()}")
PASS_REFERENCE = "    normalised = normalise_region(records, reference)"
# The two CLI lines the region build's passes actually ran (rv1-t0208 B1, B2).
CLI_REFERENCE = ("    table = assemble(document, None if args.reference is None else "
                 "region_reference.load(args.reference))")
CLI_MOTORWAYS = "                     motorway_source=None if args.motorways is None else pathlib.Path(args.motorways))"

MUTATIONS = [
    # THE REFERENCE IGNORED - the defect this task exists to end, at each of the three layers that can drop
    # it: the normaliser, the library call that hands it on, and the CLI that reads it off the command line.
    ("rank against the clip's own population even when a reference was supplied", NORMALISE,
     CHOOSE_REFERENCE, "            ranks[term] = percentile_ranks(values)"),
    ("assemble drops the reference on the floor instead of handing it to the normaliser", ASSEMBLE,
     PASS_REFERENCE, "    normalised = normalise_region(records)"),
    ("python -m etl.assemble drops --reference, so every tile is ranked against itself again (rv1-t0208 B1)",
     ASSEMBLE, CLI_REFERENCE, "    table = assemble(document)"),
    ("python -m etl.assemble loads a reference that was never given, so one self-contained window cannot run",
     ASSEMBLE, CLI_REFERENCE, "    table = assemble(document, region_reference.load(args.reference))"),
    # THE REGION MOTORWAY SET (R1b) - the same defect one layer down, at the CLI the first pass ran.
    ("python -m etl.waydoc drops --motorways, so the clip's own motorways are measured to (rv1-t0208 B2)",
     WAYDOC, CLI_MOTORWAYS, "                     motorway_source=None)"),
    ("python -m etl.waydoc reads a motorway file that was never given, so a self-contained clip cannot run",
     WAYDOC, CLI_MOTORWAYS, "                     motorway_source=pathlib.Path(args.motorways))"),
    # THE SORTED REFERENCE. `bisect` over an unsorted list answers confidently and wrongly.
    ("bisect the reference in the order the caller sent it", NORMALISE,
     CHOOSE_REFERENCE, "            ranks[term] = ranks_against_sorted(values, list(reference[term]))"),
    # THE MID-RANK ARITHMETIC, which must equal `ranks_against` value for value.
    ("the divisor is len(reference), so the way is ranked out of a population it is in", NORMALISE,
     DIVISOR, DIVISOR_MUTANT),
    ("below counts the equal values too - bisect_right where bisect_left is the count strictly below",
     NORMALISE, BELOW, "        below = bisect.bisect_right(reference, value)"),
    ("the way is counted into the equal group TWICE", NORMALISE, EQUAL,
     "        equal = bisect.bisect_right(reference, value) - below + 2"),
    ("the way is not counted into the reference at all - 0.0 and 1.0 become reachable", NORMALISE, EQUAL,
     "        equal = bisect.bisect_right(reference, value) - below"),
    ("ties are broken differently from ranks_against - the tie group is not seen at all", NORMALISE, EQUAL,
     "        equal = 1"),
    ("the half in the mid-rank becomes a whole, which is the upper rank and not the average", NORMALISE,
     "        out[way_id] = (below + 0.5 * equal) / population\n    return out\n\n\ndef population_of",
     "        out[way_id] = (below + 1.0 * equal) / population\n    return out\n\n\ndef population_of"),
    # WHICH WAYS ARE IN THE CURVE (R2). Both rules, one mutation each.
    ("motorway and trunk join the curve they are supposed to be out of", REFERENCE,
     POPULATION, "    population = list(records)"),
    ("a way that declined to measure a term is put back into that term's curve", REFERENCE,
     ANSWERING,
     "    return {term: {record.way_id: float(getattr(record, term)) for record in population}"),
    ("every term's curve is read off the curvature field", REFERENCE, ANSWERING,
     "    return {term: {record.way_id: float(record.curvature) for record in answering(term, population)}"),
    # THE DEDUP KEY (R1).
    ("the last tile to document a way wins instead of the first", REFERENCE, FIRST_WINS,
     "                out[term][way_id] = value"),
    # THE TABLE, ITS ORDER, ITS SIZE AND ITS NAME.
    ("the reference table is written in way_id order instead of value order", REFERENCE, SORTED_TABLE,
     "    return {term: list(float(value) for value in (values.get(term) or {}).values())"),
    ("the count beside the digest counts the terms instead of each term's values", REFERENCE, COUNTS,
     "    return {term: len(table) for term in sorted(table)}"),
    ("the digest is taken over the dict's insertion order rather than a canonical one", REFERENCE,
     CANONICAL, "    return json.dumps(table, sort_keys=False, separators=(\",\", \":\"))"),
    # THE REFUSALS, at both ends of the file the two passes hand between them.
    ("write a reference that cannot be ranked against", REFERENCE, DUMP_REFUSES, "    if path is not None:"),
    ("read a reference that cannot be ranked against", REFERENCE, LOAD_REFUSES,
     "    return {term: [float(value) for value in values] for term, values in table.items()}"),
]

EQUIVALENT = [
    # WITNESS: in `ranks_against_sorted` every way's rank is a function of its OWN value and the reference
    # alone - no accumulator, no neighbour - and dict equality ignores insertion order, so iterating the
    # mapping instead of `ranked_order` returns the same dict. The same edit in `percentile_ranks` would be
    # caught, because THERE the order is the algorithm: `below` is a running count over `order`.
    ("rank in the mapping's own order instead of ranked_order - the bisect form has no accumulator",
     NORMALISE, ORDER, "    for way_id in values:\n        value = values[way_id]\n        below = bisect."),
    # WITNESS: `raw_values` coerces every value with `float()` before it can reach `table_of`, and `load`
    # coerces again on the way in, so the cast here is already a no-op on every path that ships. It is kept
    # so a future caller that hands in a Decimal or a numpy scalar cannot write one into the table.
    ("drop the float cast in table_of - raw_values and load have both already coerced", REFERENCE,
     SORTED_TABLE, "    return {term: sorted(value for value in (values.get(term) or {}).values())"),
]

# Asserted the other way round: each must still go MISSED, and a gap that CLOSES fails the run.
KNOWN_MISSED = []

MIN_MUTATIONS = 22
