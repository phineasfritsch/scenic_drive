"""The check this task exists for: raw fixture -> `normalise.normalise_region` -> `score.score`, every row.

  RED: every expected rank in `fixtures/way_records_fixture.json` comes from `naive_rank` inside
       `fixtures/generate_way_records.py` - a pairwise count of ways below and ways equal, which imports
       nothing from `etl`. `normalise.percentile_ranks` gets there by one pass over a sorted order. The two
       have to produce the same number for every way and every ranked term, exactly.

Then the end-to-end properties: no row refused, every score in [0,1], the zero-class rows exactly 0.0, and
no scorable row on 0.0 - that last one is ruling R2's stated consequence and the reason the estimator never
returns a bare 0.0.

The fixture is synthetic and says so in its own `note` field. That is the trade: the landcover and terrain
fixtures are measured because the thing under test is a measurement, and this one is arithmetic over a
population, which needs ties, both ends of every threshold and all four zero classes in one file.
"""
from __future__ import annotations

import importlib.util
import json
import math
import pathlib

import pytest

from etl import byways, normalise, score, way_record as wr

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "way_records_fixture.json"
GENERATOR = pathlib.Path(__file__).resolve().parent / "fixtures" / "generate_way_records.py"


def _generator():
    """The generator module, loaded by path: `tests/fixtures` is data, not an importable package."""
    spec = importlib.util.spec_from_file_location("generate_way_records", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load() -> dict:
    if not FIXTURE.exists():
        raise AssertionError("fixture missing: %s - run python %s"
                             % (FIXTURE, GENERATOR.relative_to(FIXTURE.parents[3])))
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


DOC = _load()
WAYS = DOC["ways"]


def _metres(value) -> float:
    """The fixture spells infinity as a string, because JSON has no literal for it."""
    return math.inf if value == "Infinity" else float(value)


def _record(row: dict) -> wr.WayRecord:
    mapping = dict(row["record"])
    mapping["meters_to_nearest_motorway"] = _metres(mapping["meters_to_nearest_motorway"])
    return wr.WayRecord.from_mapping(mapping)


RAW_REGION = [_record(row) for row in WAYS]
NORMALISED_REGION = normalise.normalise_region(RAW_REGION)
BY_WAY_ID = {record.way_id: record for record in NORMALISED_REGION}


class TestTheFixtureItself:
    def test_the_committed_bytes_are_what_the_generator_produces(self):
        """A hand-edited fixture is a failing test rather than a silent one, and re-running leaves no diff."""
        module = _generator()
        assert module.render(module.build()) == FIXTURE.read_bytes()

    def test_it_is_the_population_it_claims(self):
        assert DOC["wayCount"] == len(WAYS), "wayCount %s but %d ways" % (DOC["wayCount"], len(WAYS))
        assert DOC["populationCount"] + DOC["excludedCount"] == len(WAYS)
        ids = [row["record"]["way_id"] for row in WAYS]
        assert len(set(ids)) == len(ids), "duplicate way_id - a failure could not be named"
        assert len(WAYS) >= 200, "a rank over fewer ways than this is not a region: %d" % len(WAYS)

    def test_it_records_that_it_is_synthetic_and_who_computed_its_expectations(self):
        assert "Synthetic" in DOC["note"], DOC["note"]
        assert "naive_rank" in DOC["oracle"] and "etl/" in DOC["oracle"], DOC["oracle"]

    def test_its_term_lists_are_the_ones_the_record_declares(self):
        assert tuple(DOC["rankedTerms"]) == wr.RANKED_TERMS
        assert tuple(DOC["mappedTerms"]) == wr.MAPPED_TERMS

    def test_it_covers_the_properties_the_ranker_turns_on(self):
        """Coverage asserted, not assumed: a regenerated fixture that lost its ties would pass the rest."""
        classes = {row["record"]["highway"] for row in WAYS}
        assert byways.SCENIC_ZERO_CLASSES <= classes, sorted(byways.SCENIC_ZERO_CLASSES - classes)
        population = [row for row in WAYS if row["expected_ranks"] is not None]
        assert len(population) == DOC["populationCount"]
        for term in wr.RANKED_TERMS:
            values = [row["record"][term] for row in population]
            assert len(values) - len(set(values)) >= 2, "%s has no tie group to rank" % term
        assert any(row["record"]["tunnel_meters"] > 300.0 for row in WAYS)
        assert any(row["record"]["tunnel_meters"] == 300.0 for row in WAYS)
        assert any(_metres(row["record"]["meters_to_nearest_motorway"]) < 150.0 for row in WAYS)
        assert any(_metres(row["record"]["meters_to_nearest_motorway"]) == 150.0 for row in WAYS)
        assert any(row["record"]["surface"] is None
                   and row["record"]["highway"] in score.UNSURVEYED_CLASSES for row in WAYS)
        assert any(row["record"]["byway_status"] == byways.DESIGNATED for row in WAYS)
        assert any(row["record"]["byway_status"] == byways.ELIGIBLE for row in WAYS)
        assert any(row["record"]["points_of_interest"] is not None for row in WAYS)
        assert any(row["record"]["points_of_interest"] is None for row in WAYS)


class TestTheRanksAgreeWithTheOracle:
    def test_every_expected_rank_is_the_rank_the_normaliser_computes(self):
        """Exactly, not within a tolerance: both evaluate `(below + 0.5*equal)/n` on integer counts, so
        agreement is bit-for-bit and a tolerance would only hide a real change of estimator."""
        failures = []
        checked = 0
        for row in WAYS:
            if row["expected_ranks"] is None:
                continue
            record = BY_WAY_ID[row["record"]["way_id"]]
            for term, expected in row["expected_ranks"].items():
                checked += 1
                got = getattr(record, term)
                if got != expected:
                    failures.append("%s %s: got %r, oracle %r" % (row["id"], term, got, expected))
        assert not failures, "%d of %d ranks disagree with the oracle\n%s" % (
            len(failures), checked, "\n".join(failures[:20]))
        assert checked == DOC["populationCount"] * len(wr.RANKED_TERMS)

    def test_every_row_comes_out_in_the_state_the_fixture_expects(self):
        wrong = [(row["id"], BY_WAY_ID[row["record"]["way_id"]].terms_state, row["expected_state"])
                 for row in WAYS
                 if BY_WAY_ID[row["record"]["way_id"]].terms_state != row["expected_state"]]
        assert not wrong, wrong

    def test_an_excluded_row_holds_no_rank(self):
        excluded = [record for record in NORMALISED_REGION if record.terms_state == wr.EXCLUDED]
        assert len(excluded) == DOC["excludedCount"] > 0
        for record in excluded:
            for term in wr.RANKED_TERMS:
                assert getattr(record, term) == wr.EXCLUDED_RANK, (record.way_id, term)


class TestTheWholePathScores:
    def test_no_row_is_refused_and_every_score_is_in_zero_to_one(self):
        failures = []
        for record in NORMALISED_REGION:
            value = score.score(**record.score_kwargs())
            if value is None or not (0.0 <= value <= 1.0):
                failures.append("way %d (%s): %r" % (record.way_id, record.highway, value))
        assert not failures, "%d of %d rows\n%s" % (len(failures), len(NORMALISED_REGION),
                                                    "\n".join(failures[:20]))

    def test_every_zero_class_row_scores_exactly_zero(self):
        """plan:83 and CLAUDE.md: penalised, never gated. Exactly 0.0, not almost."""
        rows = [record for record in NORMALISED_REGION if record.highway in byways.SCENIC_ZERO_CLASSES]
        assert len(rows) == DOC["excludedCount"]
        for record in rows:
            assert score.score(**record.score_kwargs()) == 0.0, (record.way_id, record.highway)

    def test_no_scorable_row_scores_zero(self):
        """Ruling R2's consequence: a rank is never exactly 0 or 1, so only a zero CLASS reaches 0.0."""
        zeroed = [record.way_id for record in NORMALISED_REGION
                  if record.terms_state == wr.NORMALISED and score.score(**record.score_kwargs()) == 0.0]
        assert zeroed == [], zeroed

    def test_no_raw_row_can_be_scored_through_the_record(self):
        """The guard that actually protects the corpus: the state, not a range check. Rulings R3 and R4."""
        for record in RAW_REGION:
            with pytest.raises(ValueError):
                record.score_kwargs()

    def test_and_the_scorer_alone_would_not_have_caught_them(self):
        """MEASURED on this fixture, and why the guard above is the state rather than a range check:
        raw producer units are mostly outside 0..1 and answer None (score.py:131), but the row sitting at
        the region's floor - curvature 0.0, elevation_gain 0.0, relief 0.0, sinuosity 1.0, furniture 0.0 -
        is inside 0..1 and answers a perfectly plausible number that is NOT the score its normalised
        record gets. A scorer can only refuse units it can see."""
        answered = {}
        for record in RAW_REGION:
            terms = {name: getattr(record, name) for name in score.UNIT_TERMS
                     if name not in wr.DEFERRED_TERMS}
            value = score.score(highway=record.highway, points_of_interest=0.0,
                                surface=record.surface, byway_status=record.byway_status,
                                tunnel_meters=record.tunnel_meters,
                                meters_to_nearest_motorway=record.meters_to_nearest_motorway, **terms)
            if value is not None:
                answered[record.way_id] = value
        assert answered, "no raw row scored at all - this fixture no longer makes the point"
        for way_id, value in sorted(answered.items()):
            record = BY_WAY_ID[way_id]
            assert record.terms_state == wr.NORMALISED, (
                "way %d is a zero class, where both answers are 0.0 and the point is lost" % way_id)
            assert value != score.score(**record.score_kwargs()), (way_id, value)

    def test_the_busier_roadside_scores_lower(self):
        """Ruling R5: the record carries the furniture RANK and score.py keeps the (1 - furniture)
        inversion. Two inversions would cancel, and this pair - alike but for the rate - is what sees it."""
        pair = [record for record in NORMALISED_REGION
                if record.highway == "secondary" and record.way_id in {
                    row["record"]["way_id"] for row in WAYS if row["record"]["curvature"] == 900.0}]
        assert len(pair) == 2, [record.way_id for record in pair]
        quiet, busy = sorted(pair, key=lambda record: record.furniture)
        assert quiet.furniture < busy.furniture
        assert score.score(**quiet.score_kwargs()) > score.score(**busy.score_kwargs())

    @pytest.mark.parametrize("term", wr.RANKED_TERMS)
    def test_more_of_a_ranked_term_is_never_worth_less_than_less_of_it(self, term):
        """The rank is monotone in the producer's number, which is the only property the score's weights
        can rely on: whatever the producer's units are, the ordering survives normalisation."""
        pairs = sorted((row["record"][term], row["expected_ranks"][term]) for row in WAYS
                       if row["expected_ranks"] is not None)
        for (value_a, rank_a), (value_b, rank_b) in zip(pairs, pairs[1:]):
            assert rank_a <= rank_b, (term, value_a, rank_a, value_b, rank_b)
            if value_a == value_b:
                assert rank_a == rank_b, (term, value_a, rank_a, rank_b)
