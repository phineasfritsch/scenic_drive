"""Regression tests for reviewer-9's critical finding.

`verify()` fetches the publisher's checksum sidecar over the network for `upstream-md5` entries. When that
fetch raised, the exception escaped `main()`, skipping the delete-on-failure branch and leaving a fully
downloaded, UNVERIFIED file on disk. For the real Geofabrik entry that is a 1.2 GB .pbf stranded by a hiccup
on a 60-byte sidecar - and later stages would have read it happily.

The rule these tests defend: unverifiable is a FAILURE, not an exception.
"""
import hashlib
import http.server
import threading

import pytest

from etl import fetch
from etl import manifest as mf

PAYLOAD = b"regression payload\n" * 50
GOOD_MD5 = hashlib.md5(PAYLOAD).hexdigest()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/file.bin":
            body = PAYLOAD
        elif self.path == "/good.md5":
            body = f"{GOOD_MD5}  file.bin\n".encode()
        elif self.path == "/garbage.md5":
            body = b"<!doctype html><html>404 not found</html>\n"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


@pytest.fixture(scope="module")
def server():
    srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def md5_entry(server, checksum_path):
    return mf.Input(name="file.bin", url=f"{server}/file.bin", verify="upstream-md5",
                    license="CC0-1.0", purpose="test", checksum_url=f"{server}{checksum_path}")


class TestVerifyNeverRaises:
    def test_a_404_sidecar_is_a_failure_not_an_exception(self, server, tmp_path):
        dest = tmp_path / "file.bin"
        fetch.download(f"{server}/file.bin", dest, quiet=True)
        why = fetch.verify(md5_entry(server, "/missing.md5"), dest)
        assert why is not None and "could not verify" in why

    def test_an_unreachable_sidecar_host_is_a_failure(self, server, tmp_path):
        dest = tmp_path / "file.bin"
        fetch.download(f"{server}/file.bin", dest, quiet=True)
        entry = mf.Input(name="file.bin", url=f"{server}/file.bin", verify="upstream-md5", license="CC0-1.0",
                         purpose="test", checksum_url="http://127.0.0.1:9/nope.md5")
        why = fetch.verify(entry, dest)
        assert why is not None and "could not verify" in why

    def test_a_garbage_sidecar_is_a_mismatch_not_a_crash(self, server, tmp_path):
        dest = tmp_path / "file.bin"
        fetch.download(f"{server}/file.bin", dest, quiet=True)
        why = fetch.verify(md5_entry(server, "/garbage.md5"), dest)
        assert why is not None

    def test_a_good_sidecar_still_verifies(self, server, tmp_path):
        dest = tmp_path / "file.bin"
        fetch.download(f"{server}/file.bin", dest, quiet=True)
        assert fetch.verify(md5_entry(server, "/good.md5"), dest) is None


class TestNothingUnverifiedSurvives:
    def _manifest(self, tmp_path, server, checksum_path):
        p = tmp_path / "manifest.yaml"
        p.write_text(f"- name: file.bin\n  url: {server}/file.bin\n  verify: upstream-md5\n"
                     f"  checksum_url: {server}{checksum_path}\n  license: CC0-1.0\n  purpose: test\n",
                     encoding="utf-8")
        return p

    def test_a_sidecar_failure_deletes_the_downloaded_file(self, server, tmp_path, monkeypatch):
        """THE regression: this used to leave the file on disk and raise a traceback."""
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        m = self._manifest(tmp_path, server, "/missing.md5")
        rc = fetch.main(["--manifest", str(m)])
        assert rc == 1, "a sidecar failure must be a controlled non-zero exit, not a traceback"
        assert not (tmp_path / "file.bin").exists(), "an UNVERIFIED file was left on disk"

    def test_a_good_sidecar_keeps_the_file(self, server, tmp_path, monkeypatch):
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        m = self._manifest(tmp_path, server, "/good.md5")
        assert fetch.main(["--manifest", str(m)]) == 0
        assert (tmp_path / "file.bin").exists()


class TestDigestIsNotCoercedToInt:
    """reviewer-9's second finding: `_scalar` turned any all-digit string into an int, so a sha256 of 64 zeros
    became int 0 - falsy - and validation reported 'needs a pinned sha256' instead of naming the real problem."""

    def test_an_all_digit_digest_stays_a_string(self):
        text = ("- name: x.bin\n  url: https://e.org/x\n  verify: sha256\n  license: CC0-1.0\n"
                "  purpose: p\n  sha256: " + "0" * 64 + "\n")
        entry = mf.parse(text)[0]
        assert isinstance(entry.sha256, str)
        assert entry.validate() == [], "a valid all-digit digest must pass, not be mistaken for a missing one"

    def test_bytes_is_still_an_int(self):
        text = ("- name: x.bin\n  url: https://e.org/x\n  verify: sha256\n  license: CC0-1.0\n"
                "  purpose: p\n  sha256: " + "a" * 64 + "\n  bytes: 1234\n")
        assert mf.parse(text)[0].bytes == 1234

    def test_a_short_all_digit_digest_is_reported_as_malformed(self):
        text = ("- name: x.bin\n  url: https://e.org/x\n  verify: sha256\n  license: CC0-1.0\n"
                "  purpose: p\n  sha256: 12345\n")
        problems = mf.parse(text)[0].validate()
        assert any("64 lowercase hex" in p for p in problems), problems
