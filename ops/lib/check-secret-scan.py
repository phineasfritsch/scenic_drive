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

Seven cases, each on a throwaway repo with the real hook installed:

  * five sizes straddling the buffer, a secret on line 1 - each must be REFUSED, and say it was the secret;
  * a CLEAN file of the largest size - must COMMIT. The negative control: without it, a hook that refuses
    everything passes every size WITH the secret reason (an empty alternative in the pattern does exactly
    that) and this check prints OK (agent/rv-pr87, NON-BLOCKING 5);
  * a staged blob whose object is DELETED from the store before the commit - must be REFUSED with the
    "cannot read the staged blob" reason. The hook's fail-CLOSED branch was claimed in four places and
    exercised by nothing: replacing it with `|| : > "$blob"` survived every fixture (NON-BLOCKING 4).

`--hook <path>` points the cases at another hook - that is how this is run red against
`git show <pre-fix sha>:.githooks/pre-commit`.
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
# EQUAL to the case count below, not a floor.
EXPECTED_CASES = 7
# Assembled at run time, never written as one literal: this file is itself staged through the hook it
# tests, and the hook refused the first version of it - correctly - for carrying the token it plants.
SECRET = "sk." + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4"
MUST_SAY = "secret-looking content in leak.txt"
UNREADABLE_SAYS = "cannot read the staged blob for leak.txt"


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


def stage(repo: pathlib.Path, kb: int, with_secret: bool) -> str:
    filler = "filler line of ordinary text\n"
    body = (SECRET + "\n" if with_secret else "") + filler * (kb * 1024 // len(filler))
    (repo / "leak.txt").write_text(body, encoding="utf-8", newline="\n")
    git(repo, "add", "leak.txt")
    _, blob = git(repo, "show", ":leak.txt")
    if (SECRET in blob) != with_secret:
        return "the staged blob does not match the premise"
    return ""


def case_secret(kb):
    def run(repo):
        why = stage(repo, kb, True)
        if why:
            return 99, why
        return git(repo, "commit", "-m", "leak")
    return "%5d KB secret on line 1   must REFUSE" % kb, run, False, MUST_SAY


def case_clean(repo):
    why = stage(repo, SIZES_KB[-1], False)
    if why:
        return 99, why
    return git(repo, "commit", "-m", "clean")


def case_unreadable(repo):
    why = stage(repo, 1, True)
    if why:
        return 99, why
    _, sha = git(repo, "rev-parse", ":leak.txt")
    sha = sha.strip()
    obj = repo / ".git" / "objects" / sha[:2] / sha[2:]
    if not obj.is_file():
        return 99, "the staged blob is not a loose object at %s" % obj
    # Loose objects are written read-only; on Windows that blocks unlink until the mode is changed.
    os.chmod(obj, 0o644)
    obj.unlink()
    rc, _ = git(repo, "show", ":leak.txt")
    if rc == 0:
        return 99, "git show still reads the blob after its object was deleted"
    return git(repo, "commit", "-m", "unreadable")


CASES = [case_secret(kb) for kb in SIZES_KB] + [
    ("%5d KB clean               must COMMIT" % SIZES_KB[-1], case_clean, True, None),
    ("staged blob object deleted   must REFUSE", case_unreadable, False, UNREADABLE_SAYS),
]


def main() -> int:
    if not HOOK.is_file():
        sys.stdout.write("SECRET-SCAN FAIL: %s not found\n" % HOOK)
        return 2
    if len(CASES) != EXPECTED_CASES:
        sys.stdout.write("SECRET-SCAN REFUSING: %d cases defined, EXPECTED_CASES says %d\n" % (len(CASES), EXPECTED_CASES))
        return 2
    ok = True
    for name, fn, must_commit, must_say in CASES:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="secret-scan-"))
        try:
            repo = build(tmp)
            code, out = fn(repo)
            if code == 99:
                ok = False
                sys.stdout.write("SETUP   %s  %s\n" % (name, out))
                continue
            committed = code == 0
            if committed != must_commit:
                ok = False
                sys.stdout.write("FAIL    %s  %s\n" % (name, "COMMITTED (exit 0) - failed open" if committed
                                                        else "refused (exit %d), expected a commit" % code))
                for line in out.strip().splitlines()[:3]:
                    sys.stdout.write("            %s\n" % line)
            elif must_say and must_say not in out:
                ok = False
                sys.stdout.write("FAIL    %s  refused, but not for the stated reason; expected %r\n" % (name, must_say))
                for line in out.strip().splitlines()[:3]:
                    sys.stdout.write("            %s\n" % line)
            else:
                sys.stdout.write("ok      %s  %s\n" % (name, "committed" if committed else "refused: " + must_say))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    sys.stdout.write("\nSECRET-SCAN %s (%d cases)\n" % ("OK" if ok else "FAIL", len(CASES)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
