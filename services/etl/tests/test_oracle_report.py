"""The fixture's provenance, and coverage for `etl/oracle_report.py`.

Two round-5 findings from agent/reviewer-34 live here.

**The fixture claimed a provenance it did not have.** `oracle_select.build` wrote `source_sha256` as a
hardcoded literal, and the only test on it asserted the field was truthy. A KMZ holding 900 of 3318
collections rebuilt the fixture end to end - exit 0, 400 ways written, the whole suite green - and the
resulting file still claimed digest `3bdf4d14...` while having been built from `e891ba11...`. The digest is
now computed from the file that was read, and tied here to the manifest's pin. That pin is the deliberate
part of this task: an oracle that silently follows upstream is not an oracle.

**`oracle_report.py` had no test importing it at all**, and carried its own `TOLERANCE = 0.02`. Swept to 0.5
it printed `fixture 400/400 = 100.000%` with the suite green - a second copy of a threshold being a second
answer to the question the threshold exists to settle.
"""
from __future__ import annotations

import json
from pathlib import Path

from etl import oracle
from etl import oracle_report

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "curvature_oracle.json"
MANIFEST = Path(__file__).resolve().parents[1] / "inputs" / "manifest.yaml"


def load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class TestTheFixtureRecordsRealProvenance:
    def test_the_fixture_was_built_from_the_pinned_oracle(self):
        """The guard the whole round-5 blocker turns on.

        Needs only the committed manifest and the committed fixture - no 2.5 MB KMZ - so it runs everywhere
        the suite does. Rebuild from any other file and `build()` records that file's digest, and this fails.
        """
        pinned = oracle.pinned_digest("vermont-curvature.kmz", MANIFEST)
        assert pinned, "the manifest pins no sha256 for vermont-curvature.kmz"
        assert load()["source_sha256"] == pinned, (
            "the fixture was built from a KMZ that is not the pinned oracle")

    def test_the_digest_is_a_real_sha256_and_not_a_placeholder(self):
        d = load()["source_sha256"]
        assert len(d) == 64 and all(c in "0123456789abcdef" for c in d)

    def test_the_manifest_reader_finds_the_right_entry(self):
        """It walks a flat YAML list by hand, so the failure to guard against is silently returning some
        OTHER entry's digest - which would make the test above pass against the wrong file."""
        assert oracle.pinned_digest("vermont-osm.pbf", MANIFEST) != \
            oracle.pinned_digest("vermont-curvature.kmz", MANIFEST)
        assert oracle.pinned_digest("no-such-input.bin", MANIFEST) is None


class TestTheReportModuleIsCovered:
    def test_the_tolerance_is_not_a_second_copy(self):
        assert oracle_report.TOLERANCE is oracle.ORACLE_TOLERANCE

    def test_the_report_agrees_with_the_suite_on_the_committed_fixture(self):
        """Ties the reported number to the assertion the suite makes, so the two cannot drift apart.

        Not a fixed percentage: the pass RATE is platform-dependent by ~1 point (see test_curvature.py's
        MIN_AGREEMENT note), so asserting 94.75% here would go red on the other libm for a reason that has
        nothing to do with the report.
        """
        doc = load()
        r = oracle_report.agreement(doc["ways"])
        assert r["n"] == len(doc["ways"])
        errs = []
        for way in doc["ways"]:
            from etl import curvature as cv
            got = cv.way_curvature([tuple(c) for c in way["coords"]], way["way_id"])
            errs.append(abs(got - way["oracle_curvature"]) / way["oracle_curvature"])
        assert r["agree"] == sum(1 for e in errs if e <= oracle.ORACLE_TOLERANCE)
        assert r["share"] == r["agree"] / r["n"]

    def test_a_report_over_no_ways_is_not_a_zero_percent_agreement(self):
        """`0/0 = 0.000%` reads like a measurement and is the absence of one. `main` refuses it; this pins
        the shape the refusal keys on."""
        r = oracle_report.agreement([])
        assert r["n"] == 0 and r["agree"] == 0

    def test_the_report_names_the_platform_it_ran_on(self):
        """The entire round-3 blocker was a number quoted without its platform."""
        p = oracle_report.this_platform()
        assert p and any(ch.isdigit() for ch in p), "no interpreter version in the platform string"
