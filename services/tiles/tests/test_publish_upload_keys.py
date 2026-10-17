"""`ops/publish-tiles` uploads every file under the SAME prefix as the archive, at exactly the keys the styles name.

rv1 B2 (T-0196): the asset PUT URL lost `$PREFIX` and 23 tests stayed green, because nothing ever ran the script
past its gates. This runs the shipping script, copied into a fresh git tree under tmp_path in which EVERY gate
holds - credentials, prod.lock, a check_pmtiles-valid archive and its sidecar, the committed styles, a glyph and
sprite tree whose digest is the pin's - with `curl` and `docker` stubbed first on PATH, recording their argv.
The set of upload URLs is then compared WHOLE with one recomputed here: `<endpoint>/<bucket>/<prefix>/` + each
small JSON's basename + each publish-list entry with spaces as %20; and the archive's own key is read off the
docker uploader's argv. Nothing here reaches the network: the only `curl` and `docker` the script can find are
the stubs, and the credentials are fixture strings.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
TILES = ROOT / "services" / "tiles"
sys.path.insert(0, str(TILES))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from basemap_assets import LICENCE, committed_styles, required_files, tree_digest  # noqa: E402
from make_styles import ASSETS_BASE  # noqa: E402
from test_pmtiles_budget import LA_BBOX, good_metadata, write_pmtiles  # noqa: E402

SCRIPT = ROOT / "ops" / "publish-tiles"
ACCOUNT, BUCKET, PREFIX = "acct0196", "bucket0196", "tiles/v1"
CREDENTIALS = {"CLOUDFLARE_ACCOUNT_ID": ACCOUNT, "R2_ACCESS_KEY_ID": "key0196",
               "R2_SECRET_ACCESS_KEY": "secret0196", "R2_BUCKET": BUCKET}
STUB = "#!/usr/bin/env bash\n{ printf '%s' \"${0##*/}\"; for a in \"$@\"; do printf '\\t%s' \"$a\"; done; " \
       "printf '\\n'; } >> \"$STUB_LOG\"\n"


def copy(rel: str, tree: Path) -> None:
    (tree / rel).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / rel, tree / rel)


def gated_tree(tree: Path) -> list[str]:
    """A tree in which every gate of the script holds. Returns the publish list the assets were built from."""
    subprocess.run([shutil.which("git"), "init", "-q", str(tree)], check=True, capture_output=True)
    for rel in ("ops/publish-tiles", "services/tiles/check_pmtiles.py", "services/tiles/basemap_assets.py",
                "services/tiles/make_styles.py", "services/tiles/styles/scenic-light.json",
                "services/tiles/styles/scenic-dark.json", "services/etl/regions/la/region.json"):
        copy(rel, tree)
    (tree / "queue" / "LOCKS").mkdir(parents=True)
    (tree / "queue" / "LOCKS" / "prod.lock").write_text("held\n", encoding="utf-8")
    work = tree / "services" / "tiles" / "work"
    work.mkdir(parents=True)
    built_at = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    archive = write_pmtiles(work / "la.pmtiles", LA_BBOX, good_metadata(built_at=built_at))
    sidecar = {"region": "la", "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}
    (work / "la.pmtiles.json").write_text(json.dumps(sidecar), encoding="utf-8")
    publish_list = required_files(committed_styles(), ASSETS_BASE) + [LICENCE]
    for rel in publish_list:
        (work / rel).parent.mkdir(parents=True, exist_ok=True)
        (work / rel).write_bytes(b"{}" if rel.endswith(".json") else rel.encode("utf-8"))
    pin = json.loads((TILES / "basemap_assets.json").read_text(encoding="utf-8"))
    pin["tree_sha256"] = tree_digest(work)[0]
    (tree / "services" / "tiles" / "basemap_assets.json").write_text(json.dumps(pin), encoding="utf-8")
    return publish_list


def run_publish(tree: Path, tmp: Path) -> tuple[subprocess.CompletedProcess, list[list[str]]]:
    bash = shutil.which("bash")
    if bash is None or shutil.which("git") is None:
        pytest.fail("no bash or git on PATH: ops/publish-tiles cannot be exercised, so it is not verified")
    stubs = tmp / "stubs"
    stubs.mkdir()
    for name in ("curl", "docker"):
        (stubs / name).write_bytes(STUB.encode("utf-8"))
        (stubs / name).chmod(0o755)
    log = tmp / "argv.log"
    log.write_bytes(b"")
    # The same recorder also as an EXPORTED bash function: bash resolves a function before PATH, so the script's
    # ~515 PUTs append in-process instead of spawning ~515 shells (minutes on a loaded Windows box). The PATH
    # stub stays behind it: a bash that does not import the function still reaches a recorder, never curl.
    env = {**os.environ, **CREDENTIALS, "STUB_LOG": log.as_posix(), "PYTHON": Path(sys.executable).as_posix(),
           "PATH": str(stubs) + os.pathsep + os.environ.get("PATH", ""),
           "BASH_FUNC_curl%%": "() { { printf '%s' curl; for a in \"$@\"; do printf '\\t%s' \"$a\"; done; "
                               "printf '\\n'; } >> \"$STUB_LOG\"; }"}
    completed = subprocess.run([bash, "ops/publish-tiles"], cwd=tree, env=env, capture_output=True,
                               text=True, timeout=1500)
    calls = [line.rstrip("\r").split("\t") for line in log.read_text(encoding="utf-8").splitlines() if line]
    return completed, calls


def test_every_upload_lands_under_the_prefix_at_the_key_the_styles_name(tmp_path: Path) -> None:
    tree = tmp_path / "t"
    publish_list = gated_tree(tree)
    completed, calls = run_publish(tree, tmp_path)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stdout.strip().splitlines()[-1].startswith(f"PUBLISHED {PREFIX}/la.pmtiles sha256=")

    endpoint = f"https://{ACCOUNT}.r2.cloudflarestorage.com"
    base = f"{endpoint}/{BUCKET}/{PREFIX}/"
    expected = {base + name for name in ("la.pmtiles.json", "scenic-light.json", "scenic-dark.json")}
    expected |= {base + rel.replace(" ", "%20") for rel in publish_list}
    curl_urls = [call[-1] for call in calls if call[0] == "curl"]
    assert len(curl_urls) == len(expected), "an upload went up twice or not at all"
    assert set(curl_urls) == expected

    docker = [call for call in calls if call[0] == "docker"]
    assert len(docker) == 1
    upload = docker[0][docker[0].index("upload"):]
    assert upload == ["upload", "/w/la.pmtiles", f"{PREFIX}/la.pmtiles",
                      f"--bucket=s3://{BUCKET}?endpoint={endpoint}&region=auto&s3ForcePathStyle=true"]
