"""The fetcher must never leave an unverified file where a later stage could read it, and must never report
success for something it did not actually verify. These tests run against a local HTTP server - no network.
"""
import hashlib
import http.server
import threading
from pathlib import Path

import pytest

from etl import fetch
from etl import manifest as mf

PAYLOAD = b"scenic drive test payload\n" * 100
GOOD_SHA = hashlib.sha256(PAYLOAD).hexdigest()
GOOD_MD5 = hashlib.md5(PAYLOAD).hexdigest()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/file.bin":
            body = PAYLOAD
        elif self.path == "/file.bin.md5":
            body = f"{GOOD_MD5}  file.bin\n".encode()
        elif self.path == "/wrong.bin.md5":
            body = f"{'0' * 32}  file.bin\n".encode()
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        self.do_GET()

    def log_message(self, *a):
        pass


@pytest.fixture(scope="module")
def server():
    srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def sha_entry(url, digest):
    return mf.Input(name="file.bin", url=url, verify="sha256", license="CC0-1.0", purpose="test", sha256=digest)


def md5_entry(url, checksum_url):
    return mf.Input(name="file.bin", url=url, verify="upstream-md5", license="CC0-1.0", purpose="test",
                    checksum_url=checksum_url)


class TestVerification:
    def test_a_matching_sha256_verifies(self, server, tmp_path):
        dest = tmp_path / "file.bin"
        fetch.download(f"{server}/file.bin", dest, quiet=True)
        assert fetch.verify(sha_entry(f"{server}/file.bin", GOOD_SHA), dest) is None

    def test_a_wrong_sha256_is_reported_not_swallowed(self, server, tmp_path):
        dest = tmp_path / "file.bin"
        fetch.download(f"{server}/file.bin", dest, quiet=True)
        why = fetch.verify(sha_entry(f"{server}/file.bin", "b" * 64), dest)
        assert why and "sha256 mismatch" in why

    def test_upstream_md5_verifies_against_the_publishers_sidecar(self, server, tmp_path):
        dest = tmp_path / "file.bin"
        fetch.download(f"{server}/file.bin", dest, quiet=True)
        assert fetch.verify(md5_entry(f"{server}/file.bin", f"{server}/file.bin.md5"), dest) is None

    def test_upstream_md5_mismatch_is_reported(self, server, tmp_path):
        dest = tmp_path / "file.bin"
        fetch.download(f"{server}/file.bin", dest, quiet=True)
        why = fetch.verify(md5_entry(f"{server}/file.bin", f"{server}/wrong.bin.md5"), dest)
        assert why and "md5 mismatch" in why


class TestDownload:
    def test_a_partial_download_never_lands_at_the_final_path(self, server, tmp_path, monkeypatch):
        """If the transfer dies mid-stream, the destination must not exist - a truncated file that later stages
        happily read is exactly how a corrupt corpus gets built and reported as a success."""
        dest = tmp_path / "file.bin"
        real_urlopen = fetch.urllib.request.urlopen

        class Boom(Exception):
            pass

        class HalfReader:
            def __init__(self, inner):
                self._inner = inner
                self.headers = inner.headers
                self._served = 0

            def read(self, n):
                if self._served >= 200:
                    raise Boom("connection reset")
                self._served += n
                return self._inner.read(n)

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(req, **kw):
            return HalfReader(real_urlopen(req, **kw))

        monkeypatch.setattr(fetch.urllib.request, "urlopen", fake_urlopen)
        with pytest.raises(Boom):
            fetch.download(f"{server}/file.bin", dest, quiet=True)
        assert not dest.exists(), "a failed download left a file at the destination path"


class TestMainFlow:
    def _manifest(self, tmp_path, url, digest):
        p = tmp_path / "manifest.yaml"
        p.write_text(f"- name: file.bin\n  url: {url}\n  verify: sha256\n  license: CC0-1.0\n"
                     f"  purpose: test\n  sha256: {digest}\n", encoding="utf-8")
        return p

    def test_a_bad_digest_deletes_the_file_and_exits_nonzero(self, server, tmp_path, monkeypatch):
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        m = self._manifest(tmp_path, f"{server}/file.bin", "c" * 64)
        rc = fetch.main(["--manifest", str(m)])
        assert rc == 1
        assert not (tmp_path / "file.bin").exists(), "an unverified file was left on disk"

    def test_a_good_digest_succeeds_and_keeps_the_file(self, server, tmp_path, monkeypatch):
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        m = self._manifest(tmp_path, f"{server}/file.bin", GOOD_SHA)
        assert fetch.main(["--manifest", str(m)]) == 0
        assert (tmp_path / "file.bin").exists()

    def test_an_invalid_manifest_stops_before_any_download(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        m = tmp_path / "manifest.yaml"
        m.write_text("- name: x.bin\n  url: https://e.org/x\n  verify: sha256\n  purpose: p\n", encoding="utf-8")
        assert fetch.main(["--manifest", str(m)]) == 2
        assert not (tmp_path / "x.bin").exists()

    def test_dry_run_downloads_nothing(self, server, tmp_path, monkeypatch):
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        m = self._manifest(tmp_path, f"{server}/file.bin", GOOD_SHA)
        assert fetch.main(["--manifest", str(m), "--dry-run"]) == 0
        assert not (tmp_path / "file.bin").exists()
