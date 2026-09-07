"""The manifest validator is the gate that stops an unverifiable or unlicensed input entering the pipeline.
These tests exist to make it fail on the ways an agent would plausibly get it wrong.
"""
import subprocess
from pathlib import Path

import pytest

from etl import manifest as mf

REAL = Path(__file__).resolve().parents[1] / "inputs" / "manifest.yaml"


def entry(**kw):
    base = dict(name="thing.tif", url="https://example.org/thing.tif", verify="sha256",
                license="US-PD-17USC105", purpose="testing", sha256="a" * 64)
    base.update(kw)
    return mf.Input(**base)


class TestRealManifest:
    def test_the_committed_manifest_is_valid(self):
        inputs = mf.parse(REAL.read_text(encoding="utf-8"))
        assert mf.validate_all(inputs) == []

    def test_every_entry_names_the_task_that_consumes_it(self):
        for i in mf.parse(REAL.read_text(encoding="utf-8")):
            assert i.consumed_by, f"{i.name} has no consumed_by"

    def test_the_manifest_is_actually_tracked_by_git(self):
        """The three tests above passed locally and failed in CI: .gitignore had `services/etl/inputs/`, so
        the manifest existed on the author's disk and in no clone. A file the suite reads must be IN the repo -
        an ignore rule that swallows it turns every reader into a local-only pass.

        The repo root is asked of git, not computed as `parents[3]`. That arithmetic is right in a checkout
        and wrong everywhere else: run inside the ETL image, where only services/etl is mounted, it raised
        `IndexError: 3` from pathlib rather than saying anything about the manifest. Found by T-0038 running
        this suite in the container the pipeline actually uses.
        """
        rel = "services/etl/inputs/manifest.yaml"
        try:
            top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=Path(__file__).resolve().parent,
                                 capture_output=True, text=True)
        except FileNotFoundError as e:
            # No git binary at all - the ETL image does not ship one. Raised as FileNotFoundError, not a
            # non-zero return code, so it needs its own arm; without it the suite died with a traceback.
            pytest.skip(f"git is not installed here, cannot check tracking: {e}")
        if top.returncode != 0:
            # No work tree here, so "is it committed?" is not a question this process can answer. Skip
            # LOUDLY rather than inventing a verdict - and note that ops/test always runs in a checkout, so
            # this branch is never the one CI takes.
            pytest.skip(f"not inside a git work tree, cannot check tracking: {top.stderr.strip() or 'no git'}")
        root = top.stdout.strip()
        tracked = subprocess.run(["git", "-C", root, "ls-files", "--error-unmatch", rel],
                                 capture_output=True, text=True)
        assert tracked.returncode == 0, f"{rel} is not tracked by git: {tracked.stderr.strip()}"
        ignored = subprocess.run(["git", "-C", root, "check-ignore", "-q", rel],
                                 capture_output=True, text=True)
        assert ignored.returncode != 0, f"{rel} is tracked but ALSO matched by a .gitignore rule"

    def test_every_attribution_licence_it_uses_is_actually_attributed(self):
        """T-0027 added CC-BY-4.0 to KNOWN_LICENSES, downloaded ESA WorldCover under it, derived the score's
        land-cover terms from it, and wrote the attribution nowhere - LICENSE-DATA still credited the USFS
        and MRLC layers the task had abandoned. Found by agent/reviewer-32, not by anything here, because
        nothing here looked. The repo root is asked of git for the same reason as the test above."""
        try:
            top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                 cwd=Path(__file__).resolve().parent, capture_output=True, text=True)
        except FileNotFoundError as e:
            pytest.skip(f"git is not installed here, cannot find the repo root: {e}")
        if top.returncode != 0:
            pytest.skip(f"not inside a git work tree: {top.stderr.strip() or 'no git'}")
        path = Path(top.stdout.strip()) / "LICENSE-DATA"
        assert path.is_file(), "LICENSE-DATA does not exist"
        missing = mf.unattributed(mf.parse(REAL.read_text(encoding="utf-8")),
                                  path.read_text(encoding="utf-8"))
        assert missing == [], f"LICENSE-DATA does not attribute: {missing}"

    def test_osm_is_odbl_and_not_pinned_by_sha256(self):
        """Geofabrik rebuilds daily; a pinned digest would rot within 24h."""
        osm = next(i for i in mf.parse(REAL.read_text(encoding="utf-8")) if "osm" in i.name)
        assert osm.license == "ODbL-1.0"
        assert osm.verify == "upstream-md5"
        assert osm.checksum_url


class TestAttribution:
    def test_an_attribution_licence_with_no_credit_is_reported(self):
        assert mf.unattributed([entry(license="CC-BY-4.0")], "nothing here") == ["CC-BY-4.0"]

    def test_the_credit_can_be_spelled_either_way(self):
        for text in ("... under CC BY 4.0 ...", "... CC-BY-4.0 ..."):
            assert mf.unattributed([entry(license="CC-BY-4.0")], text) == []

    def test_a_public_domain_licence_needs_no_credit(self):
        assert mf.unattributed([entry(license="US-PD-17USC105")], "") == []

    def test_every_licence_that_needs_credit_is_one_we_have_reasoned_about(self):
        """A spelling table entry for a licence not in KNOWN_LICENSES is a rule that can never fire."""
        assert set(mf.ATTRIBUTION_LICENSES) <= set(mf.KNOWN_LICENSES)

    def test_it_reports_every_missing_licence_not_just_the_first(self):
        missing = mf.unattributed([entry(license="CC-BY-4.0"), entry(license="ODbL-1.0")], "")
        assert missing == ["CC-BY-4.0", "ODbL-1.0"]


class TestValidation:
    def test_accepts_a_well_formed_entry(self):
        assert entry().validate() == []

    def test_rejects_a_missing_licence(self):
        assert any("license is required" in p for p in entry(license="").validate())

    def test_rejects_an_unrecognised_licence(self):
        assert any("not in KNOWN_LICENSES" in p for p in entry(license="WhateverIFeelLike").validate())

    def test_rejects_sha256_mode_without_a_digest(self):
        assert any("needs a pinned sha256" in p for p in entry(sha256=None).validate())

    def test_rejects_a_malformed_digest(self):
        assert any("64 lowercase hex" in p for p in entry(sha256="NOTHEX").validate())

    def test_rejects_upstream_md5_without_a_checksum_url(self):
        assert any("needs checksum_url" in p for p in entry(verify="upstream-md5", sha256=None).validate())

    def test_rejects_an_unknown_verify_mode(self):
        assert any("verify must be one of" in p for p in entry(verify="trust-me").validate())

    def test_there_is_no_way_to_opt_out_of_verification(self):
        """An input we cannot verify is an input we do not take."""
        assert "none" not in mf.VERIFY_MODES
        assert any("verify must be one of" in p for p in entry(verify="none").validate())

    def test_rejects_plain_http_to_a_real_host(self):
        assert any("must be https" in p for p in entry(url="http://example.org/x").validate())

    def test_allows_plain_http_only_to_loopback(self):
        """The fetcher's own tests need a local server; nothing else gets the exception."""
        assert entry(url="http://127.0.0.1:8080/x").validate() == []
        assert entry(url="http://localhost:8080/x").validate() == []
        assert any("must be https" in p for p in entry(url="http://127.0.0.1.evil.com/x").validate())
        assert any("must be https" in p for p in entry(url="http://10.0.0.5/x").validate())

    def test_rejects_a_missing_purpose(self):
        assert any("purpose is required" in p for p in entry(purpose="").validate())


class TestParsing:
    def test_rejects_unknown_fields_rather_than_ignoring_them(self):
        """A typo'd field name must not silently become 'unverified'."""
        text = ("- name: x.tif\n  url: https://e.org/x\n  verify: sha256\n  license: CC0-1.0\n"
                "  purpose: p\n  sha256: " + "a" * 64 + "\n  licence: CC0-1.0\n")
        with pytest.raises(ValueError, match="unknown field"):
            mf.parse(text)

    def test_duplicate_names_are_a_problem(self):
        text = ""
        for _ in range(2):
            text += ("- name: x.tif\n  url: https://e.org/x\n  verify: sha256\n  license: CC0-1.0\n"
                     "  purpose: p\n  sha256: " + "a" * 64 + "\n")
        assert any("duplicate" in p for p in mf.validate_all(mf.parse(text)))

    def test_an_empty_manifest_is_invalid(self):
        """Never let an empty artefact read as 'everything verified'."""
        assert any("empty" in p for p in mf.validate_all([]))
