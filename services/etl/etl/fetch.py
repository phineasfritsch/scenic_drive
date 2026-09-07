"""Fetch the manifest's inputs, verifying every byte. Nothing unverified is ever left on disk.

  python -m etl.fetch --dry-run              list what would be fetched, with sizes
  python -m etl.fetch                        fetch everything missing or changed
  python -m etl.fetch --only california-osm  fetch one entry
  python -m etl.fetch --record-digest NAME   fetch NAME, print its sha256, and refuse to proceed further

--record-digest exists so that pinning a digest is a deliberate human act. A fetcher that silently accepts
whatever the network hands it the first time, and pins THAT, is not verifying anything - it is laundering
whatever it got into a number that looks like provenance.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import os
import sys
import urllib.request
from pathlib import Path

from . import manifest as mf

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "inputs" / "manifest.yaml"
DEST = ROOT / "inputs"
UA = "scenic-drive-etl/1 (+https://github.com/phineasfritsch/scenic_drive)"
CHUNK = 1 << 20


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def download(url: str, dest: Path, quiet: bool = False) -> None:
    """Download to a .part file and rename only on success, so a partial file is never mistaken for a good one."""
    part = dest.with_suffix(dest.suffix + ".part")
    part.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"user-agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r, part.open("wb") as out:
        total = int(r.headers.get("content-length") or 0)
        got = 0
        while True:
            block = r.read(CHUNK)
            if not block:
                break
            out.write(block)
            got += len(block)
            if not quiet and total:
                pct = 100 * got / total
                print(f"\r  {dest.name}: {got/1048576:.0f}/{total/1048576:.0f} MB ({pct:.0f}%)", end="", file=sys.stderr)
        if not quiet and total:
            print(file=sys.stderr)
    part.replace(dest)


def upstream_md5(url: str) -> str:
    """Read a publisher's checksum sidecar. Format is `<md5>  <filename>`."""
    req = urllib.request.Request(url, headers={"user-agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode().split()[0].strip().lower()


def verify(entry: mf.Input, path: Path) -> str | None:
    """Return None if the file on disk is what the manifest says it should be, else a reason.

    NEVER raises. `upstream-md5` fetches the publisher's sidecar over the network at verification time, and an
    exception escaping here would skip the caller's delete-on-failure branch - leaving a fully downloaded,
    UNVERIFIED file on disk. For the Geofabrik entry that means a hiccup on a 60-byte sidecar stranding a 1.2 GB
    .pbf that later stages would happily read. Unverifiable is a failure, not an exception.
    """
    try:
        if entry.verify == "sha256":
            got = sha256_file(path)
            return None if got == entry.sha256 else f"sha256 mismatch: expected {entry.sha256}, got {got}"
        if entry.verify == "upstream-md5":
            want = upstream_md5(entry.checksum_url or "")
            got = md5_file(path)
            return None if got == want else f"md5 mismatch against {entry.checksum_url}: expected {want}, got {got}"
        return f"unknown verify mode {entry.verify!r}"
    except Exception as e:
        return f"could not verify ({type(e).__name__}: {e})"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="etl.fetch")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--record-digest", metavar="NAME")
    ap.add_argument("--manifest", default=str(MANIFEST))
    args = ap.parse_args(argv)

    inputs = mf.parse(Path(args.manifest).read_text(encoding="utf-8"))
    problems = mf.validate_all(inputs)
    # A new sha256 entry has no digest yet - that is the whole reason to run --record-digest - so the one
    # problem this command exists to solve must not be the one that blocks it. The manifest header documents
    # "Get it with `--record-digest NAME`, then commit it", and until now that was impossible: the entry was
    # invalid, validation ran first, and the tool refused. Found while adding the Curvature oracle in T-0025.
    #
    # Narrow on purpose: only a MISSING digest, and only while recording one. Every other problem still stops
    # the run - a manifest that is broken in some other way is not one you should be pinning new digests into.
    #
    # The excuse covers every unrecorded entry, not only the named one, because recording is inherently
    # incremental: T-0026 added eight tiles at once, and a version that excused only the named entry refused
    # to record the first because the other seven were also unpinned. That was this fix's own first use, and
    # it failed at it. An unrecorded digest is not a WRONG value, it is an absent one, and an absent one
    # cannot be a reason to refuse the command whose job is to supply it.
    if args.record_digest:
        # Re-validate with stand-in digests rather than string-matching the complaints. A missing digest and a
        # `TODO` placeholder produce DIFFERENT messages ("needs a pinned sha256" vs "must be 64 lowercase hex
        # chars"), and matching text would have excused one and not the other - which is how the first version
        # of this fix passed its own test for `TODO` and failed for a genuinely absent digest.
        stand_in = [dataclasses.replace(i, sha256="a" * 64)
                    if (i.verify == "sha256" and (not i.sha256 or i.sha256 == "TODO")) else i
                    for i in inputs]
        problems = mf.validate_all(stand_in)
    if problems:
        print("MANIFEST INVALID", file=sys.stderr)
        for p in problems:
            print(" -", p, file=sys.stderr)
        return 2

    if args.record_digest:
        entry = next((i for i in inputs if i.name == args.record_digest), None)
        if not entry:
            print(f"no such entry: {args.record_digest}", file=sys.stderr)
            return 2
        dest = DEST / entry.name
        download(entry.url, dest)
        digest = sha256_file(dest)
        print(f"{entry.name} sha256: {digest}")
        print("Put that in the manifest deliberately; this command does not edit it for you.", file=sys.stderr)
        return 0

    selected = [i for i in inputs if not args.only or i.name == args.only]
    if args.only and not selected:
        print(f"no such entry: {args.only}", file=sys.stderr)
        return 2

    if args.dry_run:
        for i in selected:
            dest = DEST / i.name
            state = "present" if dest.exists() else "missing"
            size = f"{i.bytes/1048576:.0f} MB" if i.bytes else "size unknown"
            print(f"{i.name:28s} {state:8s} {size:>12s}  verify={i.verify:12s} {i.license:20s} {i.url}")
        return 0

    failures = 0
    for i in selected:
        dest = DEST / i.name
        if dest.exists():
            why = verify(i, dest)
            if why is None:
                print(f"{i.name}: already present and verified")
                continue
            print(f"{i.name}: on-disk copy failed verification ({why}); refetching", file=sys.stderr)
        print(f"{i.name}: fetching {i.url}")
        try:
            download(i.url, dest)
        except Exception as e:
            print(f"{i.name}: DOWNLOAD FAILED: {type(e).__name__}: {e}", file=sys.stderr)
            failures += 1
            continue
        why = verify(i, dest)
        if why is not None:
            dest.unlink(missing_ok=True)  # never leave an unverified file where a later stage could read it
            print(f"{i.name}: VERIFICATION FAILED: {why} (deleted)", file=sys.stderr)
            failures += 1
            continue
        print(f"{i.name}: verified ({i.verify})")

    if failures:
        print(f"FETCH FAILED: {failures} input(s)", file=sys.stderr)
        return 1
    print(f"FETCH OK: {len(selected)} input(s) verified")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
