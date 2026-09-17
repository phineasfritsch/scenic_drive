#!/usr/bin/env python3
"""The pre-commit secret scan must refuse a staged secret at EVERY size, not only small ones.

Found by following a flake (T-0140). P-SAFE-05 failed 1 run in 3 on one box because it piped swift test into grep -q
under `pipefail`, which races: grep exits at its first match, the producer gets SIGPIPE, the pipeline reports 141.
The hook's CRLF and secret scans piped git show of the staged blob into grep -q under the same `pipefail` - and there
the race is not a flake but a FAIL-OPEN with a threshold. Measured with the shipped hook, a file carrying an
sk. token on line 1:

      1 KB  refused        64 KB  refused
    256 KB  COMMITTED, exit 0, nothing printed
   1024 KB  COMMITTED     4096 KB  COMMITTED

Any file over the pipe buffer beat the gate CLAUDE.md says "greps for them". Nothing else in this
repository would have noticed: the hook has no fixture of its own beyond the merge cases, none of which
stages a large file.

Five sizes, straddling the buffer, each on a throwaway repo with the real hook installed. Every size must be
REFUSED and must say why. `--hook <path>` points the cases at another hook - that is how this is run red
against `git show <pre-fix sha>:.githooks/pre-commit`.
"""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOOK = ROOT / ".githooks" / "pre-commit"
for _i, _a in enumerate(sys.argv):
    if _a == "--hook" and _i + 1 < len(sys.argv):
        HOOK = pathlib.Path(sys.argv[_i + 1]).resolve()

# Kilobytes. 1 and 64 refused before the fix; 256 is the first size that committed. Both sides of the
# threshold are here so a "fix" that merely moves the threshold is seen.
SIZES_KB = (1, 64, 256, 1024, 4096)
MIN_SIZES = 5
# Assembled at run time, never written as one literal: this file is itself staged through the hook it
# tests, and the hook refused the first version of it - correctly - for carrying the token it plants.
SECRET = "sk." + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4"
MUST_SAY = "secret-looking content in leak.txt"


def git(repo, *args):
    p = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout + p.stderr


def build(tmp: pathlib.Path) -> pathlib.Path:
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "probe@example.invalid")
    git(repo, "config", "user.name", "probe")
    git(repo, "config", "commit.gpgsign", "false")
    hooks = repo / ".githooks"
    hooks.mkdir()
    shutil.copy(HOOK, hooks / "pre-commit")
    os.chmod(hooks / "pre-commit", 0o755)
    git(repo, "config", "core.hooksPath", ".githooks")
    return repo


def main() -> int:
    if not HOOK.is_file():
        sys.stdout.write("SECRET-SCAN FAIL: %s not found\n" % HOOK)
        return 2
    if len(SIZES_KB) != MIN_SIZES:
        sys.stdout.write("SECRET-SCAN REFUSING: %d sizes defined, MIN_SIZES says %d\n" % (len(SIZES_KB), MIN_SIZES))
        return 2
    ok = True
    for kb in SIZES_KB:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="secret-scan-"))
        try:
            repo = build(tmp)
            filler = "filler line of ordinary text\n"
            body = SECRET + "\n" + filler * (kb * 1024 // len(filler))
            (repo / "leak.txt").write_text(body, encoding="utf-8", newline="\n")
            git(repo, "add", "leak.txt")
            # The premise must hold or the case tested nothing: the secret is really in the staged blob.
            _, blob = git(repo, "show", ":leak.txt")
            if SECRET not in blob:
                ok = False
                sys.stdout.write("SETUP   %5d KB  the secret is not in the staged blob\n" % kb)
                continue
            code, out = git(repo, "commit", "-m", "leak")
            if code == 0:
                ok = False
                sys.stdout.write("FAIL    %5d KB  COMMITTED (exit 0) - the secret scan failed open\n" % kb)
            elif MUST_SAY not in out:
                ok = False
                sys.stdout.write("FAIL    %5d KB  refused, but not for the secret; expected %r\n" % (kb, MUST_SAY))
                for line in out.strip().splitlines()[:3]:
                    sys.stdout.write("            %s\n" % line)
            else:
                sys.stdout.write("ok      %5d KB  refused: %s\n" % (kb, MUST_SAY))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    sys.stdout.write("\nSECRET-SCAN %s (%d sizes)\n" % ("OK" if ok else "FAIL", len(SIZES_KB)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
