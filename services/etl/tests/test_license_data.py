"""LICENSE-DATA against the manifest, in both directions.

The failure this file exists for is B1 of the T-0027 sign-off review, and the shape of it is worth keeping
in view: the shipped attribution file was wrong in BOTH directions at the same time. It credited USFS Tree
Canopy Cover and MRLC NLCD impervious under US public domain - two layers MRLC's Requester Pays bucket
refuses to serve and which nothing in this tree is derived from - and it said nothing at all about ESA
WorldCover, the CC-BY-4.0 raster every land-cover term is actually computed from. A licence file that names
data we do not use and omits data we do is not a documentation problem; shipping a derived work without the
credit its licence requires is the one class of mistake that can end a project rather than cost a day.

Two directions, two checks:

  every attribution-requiring entry -> its credit, verbatim, in LICENSE-DATA   (the omission half)
  every dataset LICENSE-DATA LISTS  -> an entry in the manifest that provides it   (the false-claim half)

The second is anchored on the list lines - the "- " bullets under the section headings, which are the file's
claims of provenance - and not on prose. The paragraph under the WorldCover heading names USFS and MRLC on
purpose, to say that nothing here comes from them; a check that could not tell that sentence from a credit
would push the record towards saying less, which is the opposite of what it is for.

`etl.manifest.ATTRIBUTION_LICENSES` is the named set. A licence in neither it nor NO_ATTRIBUTION_REQUIRED is
treated as requiring credit, so widening KNOWN_LICENSES by one line cannot quietly widen what may ship
uncredited.
"""
from pathlib import Path

import pytest

from etl import manifest as mf

REPO = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).resolve().parents[1] / "inputs" / "manifest.yaml"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "landcover_fixture.json"


def inputs():
    return mf.parse(MANIFEST.read_text(encoding="utf-8"))


def license_data() -> str:
    return (REPO / "LICENSE-DATA").read_text(encoding="utf-8")


def needs_credit(item) -> bool:
    return bool(item.license) and item.license not in mf.NO_ATTRIBUTION_REQUIRED


class TestEveryAttributionLicenceCarriesItsCredit:
    def test_the_repository_root_really_is_the_one_with_license_data(self):
        assert (REPO / "LICENSE-DATA").is_file(), REPO
        assert (REPO / "CLAUDE.md").is_file(), REPO

    def test_every_entry_that_needs_credit_names_the_credit_it_needs(self):
        missing = [i.name for i in inputs() if needs_credit(i) and not i.attribution]
        assert missing == [], f"manifest entries under an attribution licence with no attribution: {missing}"

    def test_every_such_credit_appears_verbatim_in_license_data(self):
        text = license_data()
        missing = sorted({i.attribution for i in inputs()
                          if needs_credit(i) and i.attribution and i.attribution not in text})
        assert missing == [], f"LICENSE-DATA does not carry, verbatim: {missing}"

    def test_the_worldcover_credit_is_the_string_the_fixture_records(self):
        """The fixture's `licence` field is where the correct wording has sat since the raster was first
        sampled - `CC-BY-4.0 - (c) ESA WorldCover project 2021 / Contains modified Copernicus Sentinel
        data`. It was in the tree the whole time this task shipped without it; the manifest and
        LICENSE-DATA now carry the same words rather than a second paraphrase of them."""
        import json
        recorded = json.loads(FIXTURE.read_text(encoding="utf-8"))["licence"]
        worldcover = [i for i in inputs() if i.name.startswith("worldcover-")]
        assert len(worldcover) == 3, [i.name for i in worldcover]
        for item in worldcover:
            assert item.license == "CC-BY-4.0"
            assert item.attribution in recorded, (item.name, item.attribution, recorded)
            assert item.attribution in license_data()

    def test_a_licence_nobody_classified_is_reported_rather_than_waved_through(self):
        """Fails closed, on a synthetic entry rather than on the real manifest."""
        fake = mf.Input(name="x", url="https://example.com/x", verify="sha256", license="CC-BY-SA-4.0",
                        purpose="p")
        assert mf.unattributed([fake], license_data()) == ["CC-BY-SA-4.0"]


class TestLicenseDataListsOnlyWhatWeUse:
    """The false-claim half. A credit for data we do not have is a claim about provenance, and it was the
    more dangerous half of B1: it read as evidence that the USFS/MRLC layers had been obtained."""

    ABANDONED = ("USFS", "MRLC", "NLCD", "Tree Canopy")

    def listed_sources(self) -> list[str]:
        return [ln.strip()[2:].strip() for ln in license_data().splitlines() if ln.strip().startswith("- ")]

    def test_the_file_still_has_sources_to_check(self):
        assert len(self.listed_sources()) >= 5, self.listed_sources()

    @pytest.mark.parametrize("name", ABANDONED)
    def test_no_listed_source_names_a_dataset_no_manifest_entry_provides(self, name):
        """MRLC's S3 refuses all anonymous access (403, Requester Pays) and nothing in the tree is derived
        from it. While no manifest entry provides it, LICENSE-DATA must not list it as a source of ours."""
        provided = [i.name for i in inputs() if name.lower() in (i.name + " " + i.url).lower()]
        assert provided == [], f"a manifest entry now provides {name}; this test is the one that is stale"
        offending = [s for s in self.listed_sources() if name.lower() in s.lower()]
        assert offending == [], f"LICENSE-DATA lists {name} as a source: {offending}"

    def test_worldcover_is_listed_under_its_own_heading_and_not_under_public_domain(self):
        """The heading is the claim about which licence applies. CC-BY-4.0 data filed under 17 U.S.C. 105
        is the original defect restated."""
        text = license_data()
        assert "ESA WorldCover" in text
        head, _, tail = text.partition("## United States government data")
        assert "ESA WorldCover" in head, "WorldCover must be credited above the public-domain section"
        assert "WorldCover" not in tail, "WorldCover is not a United States government work"
