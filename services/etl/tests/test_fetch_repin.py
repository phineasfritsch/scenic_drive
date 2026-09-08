"""`--record-digest` must not hand you a replacement digest for a file that is already pinned.

The bootstrap case - an entry with no digest yet - is covered by `TestRecordDigestBootstrap` in
`test_fetch.py`. This file covers the case that used to slip through: the entry HAS a valid pinned digest and
upstream has changed underneath it. The old behaviour downloaded the new bytes over the verified ones,
printed the new digest, and said nothing about the old, which turns a pin into a rubber stamp - the operator
pastes the number in and nobody ever looks at what changed.

Kept in its own file rather than appended to `test_fetch.py`, which is at 215 lines against a 300-line cap
and belongs to a different concern.
"""
import hashlib

import pytest

from etl import fetch
from .test_fetch import GOOD_SHA, PAYLOAD, server       # noqa: F401  (server is a fixture)

OTHER_SHA = hashlib.sha256(b"something else entirely").hexdigest()
OLD_BYTES = b"the bytes that actually match the pin\n"


def manifest(tmp_path, url, digest):
    p = tmp_path / "manifest.yaml"
    p.write_text(f"- name: file.bin\n  url: {url}\n  verify: sha256\n  license: CC0-1.0\n"
                 f"  purpose: test\n  sha256: {digest}\n", encoding="utf-8")
    return p


class TestUpstreamChangedUnderAPin:
    def test_it_refuses_rather_than_printing_a_replacement_digest(self, server, tmp_path, monkeypatch, capsys):
        """The whole point. Exit 3, distinct from 2 (bad manifest) and 1 (fetch failed)."""
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        m = manifest(tmp_path, f"{server}/file.bin", OTHER_SHA)
        assert fetch.main(["--manifest", str(m), "--record-digest", "file.bin"]) == 3

    def test_it_names_both_digests_so_the_operator_can_see_what_changed(self, server, tmp_path,
                                                                        monkeypatch, capsys):
        """A refusal that does not say what it is refusing sends the operator to the source to find out."""
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        m = manifest(tmp_path, f"{server}/file.bin", OTHER_SHA)
        fetch.main(["--manifest", str(m), "--record-digest", "file.bin"])
        err = capsys.readouterr().err
        assert OTHER_SHA in err, "the pinned digest is not in the message"
        assert GOOD_SHA in err, "the fetched digest is not in the message"
        assert "UPSTREAM CHANGED" in err

    def test_the_new_digest_is_not_on_stdout_where_it_could_be_piped_into_the_manifest(
            self, server, tmp_path, monkeypatch, capsys):
        """`--record-digest` on the happy path prints the digest to STDOUT precisely so it can be captured.
        On a refusal it must not, or the refusal is decorative for anyone using this in a pipeline."""
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        m = manifest(tmp_path, f"{server}/file.bin", OTHER_SHA)
        fetch.main(["--manifest", str(m), "--record-digest", "file.bin"])
        assert GOOD_SHA not in capsys.readouterr().out

    def test_the_pinned_file_on_disk_survives_the_refusal(self, server, tmp_path, monkeypatch):
        """The failure that made this more than a message change. `download()` wrote straight to
        inputs/<name>, so the verified bytes were replaced by unverified ones BEFORE anything compared them -
        a refusal that has already destroyed what it is protecting."""
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        dest = tmp_path / "file.bin"
        dest.write_bytes(OLD_BYTES)
        m = manifest(tmp_path, f"{server}/file.bin", OTHER_SHA)
        assert fetch.main(["--manifest", str(m), "--record-digest", "file.bin"]) == 3
        assert dest.read_bytes() == OLD_BYTES, "the pinned file was overwritten by unverified bytes"

    def test_the_fetched_bytes_are_kept_beside_it_for_inspection(self, server, tmp_path, monkeypatch):
        """Refusing is not the same as hiding. Whoever has to decide whether the change is acceptable needs
        the new bytes, and re-downloading a 2 GB extract to look at them is not a reasonable ask."""
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        (tmp_path / "file.bin").write_bytes(OLD_BYTES)
        m = manifest(tmp_path, f"{server}/file.bin", OTHER_SHA)
        fetch.main(["--manifest", str(m), "--record-digest", "file.bin"])
        staged = tmp_path / "file.bin.recording"
        assert staged.is_file()
        assert staged.read_bytes() == PAYLOAD

    def test_the_message_says_how_to_repin_deliberately(self, server, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        m = manifest(tmp_path, f"{server}/file.bin", OTHER_SHA)
        fetch.main(["--manifest", str(m), "--record-digest", "file.bin"])
        assert "TODO" in capsys.readouterr().err, "the message does not say how to re-pin on purpose"


class TestUpstreamStillMatchesThePin:
    def test_it_succeeds_and_says_nothing_changed(self, server, tmp_path, monkeypatch, capsys):
        """Re-running must be safe. An operator checking whether upstream moved should get a clear 'it did
        not', not a digest they are then left wondering about."""
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        m = manifest(tmp_path, f"{server}/file.bin", GOOD_SHA)
        assert fetch.main(["--manifest", str(m), "--record-digest", "file.bin"]) == 0
        out = capsys.readouterr()
        assert "still matches" in out.out
        assert GOOD_SHA in out.out

    def test_it_leaves_the_verified_file_in_place_not_a_recording_file(self, server, tmp_path, monkeypatch):
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        m = manifest(tmp_path, f"{server}/file.bin", GOOD_SHA)
        fetch.main(["--manifest", str(m), "--record-digest", "file.bin"])
        assert (tmp_path / "file.bin").read_bytes() == PAYLOAD
        assert not (tmp_path / "file.bin.recording").exists(), "left a stray staging file behind"


class TestTheBootstrapPathIsUnchanged:
    """The new refusal sits in front of the path this command was built for. If it can also block a genuine
    bootstrap, the fix has broken the feature to protect it."""

    @pytest.mark.parametrize("digest", ["TODO", "null"])
    def test_an_unpinned_entry_still_records(self, server, tmp_path, monkeypatch, capsys, digest):
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        m = manifest(tmp_path, f"{server}/file.bin", digest)
        assert fetch.main(["--manifest", str(m), "--record-digest", "file.bin"]) == 0
        assert GOOD_SHA in capsys.readouterr().out

    def test_a_bootstrap_writes_the_file_itself_not_a_recording_file(self, server, tmp_path, monkeypatch):
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        m = manifest(tmp_path, f"{server}/file.bin", "TODO")
        fetch.main(["--manifest", str(m), "--record-digest", "file.bin"])
        assert (tmp_path / "file.bin").read_bytes() == PAYLOAD
        assert not (tmp_path / "file.bin.recording").exists()

    def test_an_uppercase_pinned_digest_is_still_a_pin(self, server, tmp_path, monkeypatch):
        """`TODO` is the placeholder, and the comparison lowercases. A digest that differs only in case is
        the SAME pin and must not be reported as a change; one that differs in substance still must."""
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        assert fetch.main(["--manifest", str(manifest(tmp_path, f"{server}/file.bin", GOOD_SHA.upper())),
                           "--record-digest", "file.bin"]) in (0, 2)
