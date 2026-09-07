"""Fetch the manifest's inputs, verifying every byte. Nothing unverified is ever left on disk.

  python -m etl.fetch --dry-run              list what would be fetched, with sizes
  python -m etl.fetch                        fetch everything missing or changed
  python -m etl.fetch --only california-osm  fetch one entry
  python -m etl.fetch --record-digest NAME   fetch NAME, print its sha256, and refuse to proceed further

--record-digest exists so that pinning a digest is a deliberate human act. A fetcher that silently accepts
whatever the network hands it the first time, and pins THAT, is not verifying anything - it is laundering
whatever it got into a number that looks like provenance.

That promise used to hold only for an entry with no digest yet. Run against an ALREADY-pinned entry whose
upstream file had changed, it printed the new digest and said nothing about the old one, and the operator
pasted it in - the pin laundering the change instead of catching it. It now refuses (exit 3), prints both
digests and both sizes, and leaves the pinned file on disk untouched. Re-pinning deliberately means setting
the entry's sha256 back to TODO in the manifest first: two edits, both visible in a diff.
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
    # Narrow on purpose: only the named entry, only a placeholder digest. Every other problem, and every other
    # entry's problems, still stop the run - a manifest that is broken elsewhere is not a manifest you should
    # be pinning new digests into.
    if args.record_digest:
        target = next((i for i in inputs if i.name == args.record_digest), None)
        if target is not None and (not target.sha256 or target.sha256 == "TODO"):
            # Re-validate with a stand-in digest rather than string-matching the complaint. A missing digest
            # and a placeholder produce DIFFERENT messages ("needs a pinned sha256" vs "must be 64 lowercase
            # hex chars"), and matching text would have excused one and not the other - which is how the first
            # version of this fix passed its own test for `TODO` and failed for a genuinely absent digest.
            # Every other problem, on this entry and every other, survives untouched.
            stand_in = [dataclasses.replace(i, sha256="a" * 64) if i is target else i for i in inputs]
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
        pinned = (entry.sha256 or "").strip().lower()
        already_pinned = bool(pinned) and pinned != "todo"

        # Download BESIDE the pinned file, never onto it. This used to write straight to `dest`, which meant
        # the known-good, digest-verified bytes were replaced by unverified new ones before anything compared
        # them - so any refusal after that point had already destroyed the thing it was refusing to give up.
        staged = dest.with_suffix(dest.suffix + ".recording") if already_pinned else dest
        download(entry.url, staged)
        digest = sha256_file(staged)

        if already_pinned and digest != pinned:
            # THE REASON THIS COMMAND EXISTS, applied to the case it used to skip. For a NEW entry, printing
            # whatever the network returned is the point. For an entry that is ALREADY pinned, printing it
            # with no mention of the old digest is how a pin quietly becomes a rubber stamp: the operator
            # pastes the new number in and nobody ever looks at what changed. T-0025 pinned the Curvature
            # oracle precisely so that "if they regenerate it the fetch fails and a human re-pins it having
            # looked at what changed" - this is the part that makes them look.
            old_size = dest.stat().st_size if dest.exists() else None
            print(f"UPSTREAM CHANGED: {entry.name} does not match its pinned digest", file=sys.stderr)
            print(f"  pinned : {pinned}"
                  + (f"  ({old_size} bytes on disk)" if old_size is not None else "  (not on disk)"),
                  file=sys.stderr)
            print(f"  fetched: {digest}  ({staged.stat().st_size} bytes)", file=sys.stderr)
            print(f"  url    : {entry.url}", file=sys.stderr)
            print("", file=sys.stderr)
            print("Refusing to hand you a replacement digest for a file that is already pinned. If this "
                  "change is one you have looked at and accept, set this entry's sha256 to TODO in the "
                  "manifest and run this again - two deliberate edits, both visible in a diff, which is a "
                  "stronger record than a --force flag nobody sees in review.", file=sys.stderr)
            print(f"The fetched bytes are at {staged.name}; the pinned file is untouched.", file=sys.stderr)
            return 3

        if already_pinned:
            # Matches. Re-running must be safe and must not look like a change - an operator checking whether
            # upstream moved should get a clear "it did not", not a digest they then wonder about.
            staged.replace(dest)
            print(f"{entry.name} still matches its pinned sha256: {digest}")
            print("Nothing to record.", file=sys.stderr)
            return 0

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
