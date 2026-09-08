#!/usr/bin/env bash
# THREE DECISIONS, MADE ONCE, HERE: where an ops/* script finds the repo, WHAT ENVIRONMENT IT RUNS IN
# (part 2, which lives in ops/lib/seal.sh - sourced from here, and the only reason this file is split),
# and which python it runs.   Sourced, never executed:
#     source "$(dirname "${BASH_SOURCE[0]}")/lib/boot.sh" || exit 2
# Set SCENIC_TOOLCHAIN=1 before sourcing if the script must reach swift/node/npx/docker (see seal.sh).
#
# ---------------------------------------------------------------------------------------------------
# 1. THE REPO ROOT COMES FROM THIS FILE'S OWN PATH, NEVER FROM THE CALLER.
#
# Every wrapper used to say `git rev-parse --show-toplevel`, which answers "the repo the CALLER is
# standing in". Run this repo's ops/check-pins from inside any other git repository and it executed
# THAT repository's ops/lib/pins.py (T-0077). Measured, from a four-line synthetic module:
#     PINS ok=99 skipped=0 pending=0 expired=0 failed=0 tier=linux   EXIT=0
#     QUEUE OK (999 tasks)                                           EXIT=0
# ${BASH_SOURCE[0]} is this file, so the root is a property of where the SCRIPT lives. Symlinks are
# resolved (a symlink planted in a hostile tree makes BASH_SOURCE point at the attacker) and every `cd`
# is `cd -P` on an absolute operand, because a relative one searches $CDPATH first (T-0076).
#
# 2. THE ENVIRONMENT IS AN ALLOWLIST - ops/lib/seal.sh, sourced below once the root is known. It is the
# longer half of this file's argument and carries its own measurements: three routes that defeated the
# old fifteen-name unset list with no source edit, two more nobody had named, the `env -i` re-exec that
# replaces them, and the three routes that are still open with the commands that survive them (T-0086).
#
# 3. THE INTERPRETER IS CHOSEN BY CAPABILITY, NOT BY NAME - AND `PYTHON=` IS A CONVENIENCE, NOT A GUARD.
#
# `${PYTHON:-$(command -v python3 || command -v python)}` picks by NAME. `python3` wins whenever it
# exists, even when it is the wrong installation. On the box this was written on the two names are
# different products:
#     python3 -> AppData\Local\Python\pythoncore-3.14-64\python.exe   3.14.5    pytest: False
#     python  -> AppData\Local\Programs\Python\Python310\python.exe   3.10.11   pytest: True
# so ops/test ran an interpreter with no pytest, wrote no report, and stopped with "FAIL: services/etl
# exists but pytest produced no report" - blaming the ETL tier for the interpreter (T-0076).
# scenic_python asks each candidate what it CAN DO and takes the first that can do it.
#
# On PYTHON=, in writing, so it is not decided by omission in eleven files: it is honoured, it is a real
# local need (a venv, a pyenv shim, an explicit python3.12), and it is NOT a security boundary. T-0072
# added a probe to ops/check-pins to refuse `PYTHON=true`; a four-line script that echoes the probe
# token defeated it in one try, and it always will - a probe asks the thing under test to describe
# itself, and the token is printed in the script the adversary is reading. So this file does not
# pretend. What the probe is FOR is the accident: a missing python, a python2, a python without the
# modules this script needs. Those it catches, and it names the interpreter, its real sys.executable and
# its version when it refuses, because a path and a version would have ended T-0076 in seconds. Anyone
# who can set PYTHON can also edit this file; the defence against a hostile operator is the reviewer and
# the pre-commit hook, not a shell test. When PYTHON is set it is the ONLY candidate: falling back
# silently would ignore the venv you asked for. seal.sh (b) records what that leaves open, measured.
# ---------------------------------------------------------------------------------------------------
set -uo pipefail

# --- 0. the entry shell must be clean ----------------------------------------------------------------
# A positive assertion, not a denylist: NO shell function is defined when boot.sh is sourced (every
# wrapper sources it before defining anything), and BASH_ENV/ENV are unset. An exported function arrives
# as BASH_FUNC_git%% and needs no source edit; measured pre-fix, `env "BASH_FUNC_git%%=() {...}" bash
# ops/sane` printed SANE OK over a planted stray .swift. This test can itself be blinded - `declare` can
# be an exported function too, see seal.sh (c) - which is why the sealed pass re-checks the one thing
# that matters, $0, in an environment where no function survives.
if [[ -n "$(declare -F)" || -n "${BASH_ENV:-}" || -n "${ENV:-}" ]]; then
  echo "${0##*/}: refusing: the calling shell is not clean (BASH_ENV/ENV set, or a shell function is" >&2
  echo "  already defined - an exported BASH_FUNC_* can replace git, grep or exec before this line)." >&2
  echo "  Run it from a shell that defines none: env -u BASH_ENV -u ENV bash ${0##*/}" >&2
  return 2 2>/dev/null || exit 2
fi

# --- 1. root -----------------------------------------------------------------------------------------
_scenic_resolve() {                      # print the physical path of $1, following symlinks
  local p="$1" d
  while [[ -L "$p" ]]; do
    d="$(cd -P "$(dirname "$p")" 2>/dev/null && pwd)" || return 1
    p="$(readlink "$p")"
    [[ "$p" != /* && "$p" != [A-Za-z]:* ]] && p="$d/$p"
  done
  d="$(cd -P "$(dirname "$p")" 2>/dev/null && pwd)" || return 1
  printf '%s/%s\n' "$d" "$(basename "$p")"
}

SCENIC_ROOT="$(cd -P "$(dirname "$(_scenic_resolve "${BASH_SOURCE[0]}")")/../.." 2>/dev/null && pwd)"

# A sanity assert, not a boundary: it catches a moved/renamed ops/lib, not an adversary who can plant
# files. ops/lib/seal.sh is on the list because this file is useless without it and must not run on.
for _m in ops/lib/seal.sh ops/lib/pins.py ops/lib/queue.py pins/PINS.yaml CLAUDE.md; do
  if [[ ! -f "$SCENIC_ROOT/$_m" ]]; then
    echo "${0##*/}: ${SCENIC_ROOT:-<unresolved>} is not the scenic_drive root (no $_m)" >&2
    echo "  The root is derived from ops/lib/boot.sh's own path, never from the caller's git toplevel." >&2
    return 2 2>/dev/null || exit 2
  fi
done
unset _m

scenic_cd_root() { cd "$SCENIC_ROOT" || { echo "${0##*/}: cannot enter $SCENIC_ROOT" >&2; exit 2; }; }

# --- 2. the environment ------------------------------------------------------------------------------
# Everything past this line runs in an environment built from seal.sh's constants, or does not run.
# seal.sh re-execs $0 through `env -i` on the unsealed pass, so this source either returns having
# verified a sealed environment, or refuses. It needs SCENIC_ROOT and _scenic_resolve, hence the order.
source "$SCENIC_ROOT/ops/lib/seal.sh" || { return 2 2>/dev/null || exit 2; }

# --- 3. interpreter ----------------------------------------------------------------------------------
SCENIC_PY=""; SCENIC_PY_EXE=""; SCENIC_PY_VERSION=""; SCENIC_PY_SOURCE=""
SCENIC_PY_MIN="3.9"

# Prints exactly:  SCENICPY|<sys.executable>|<x.y.z>|<missing,modules or ->
# Pipe-separated, not space-separated: sys.executable is routinely "C:\Program Files\Python312\python.exe",
# and splitting that on spaces would report the version as "Files\Python312\python.exe".
_SCENIC_PROBE='
import sys
try:
    import importlib.util as u
except Exception:
    sys.exit(9)
miss = [m for m in sys.argv[1:] if u.find_spec(m) is None]
v = ".".join(str(n) for n in sys.version_info[:3])
print("SCENICPY|%s|%s|%s" % (sys.executable, v, ",".join(miss) or "-"))
'

# scenic_python [module ...] -> sets SCENIC_PY (an ABSOLUTE path) / SCENIC_PY_EXE / SCENIC_PY_VERSION,
# or returns 2 loudly. Candidates are resolved out of SCENIC_HOST_PATH - the caller's PATH, forwarded
# through the seal for exactly this - because python lives in a user directory on this box and in no
# trusted one. That the caller can AIM the interpreter is seal.sh (b) and part 3 above, unchanged and
# still open; what it can no longer do is INJECT into a legitimate one.
# Written to survive `set -e` (ops/deploy and ops/prod-read run with it): no bare failing command anywhere.
scenic_python() {
  local want=("$@") cand=() c abs pdir out tag exe ver miss why=()
  SCENIC_PY=""; SCENIC_PY_EXE=""; SCENIC_PY_VERSION=""   # never leave a stale answer behind on failure
  if [[ -n "${PYTHON:-}" ]]; then cand=("$PYTHON"); SCENIC_PY_SOURCE="PYTHON="
  else cand=(python3 python py) ; SCENIC_PY_SOURCE="PATH"
  fi
  for c in "${cand[@]}"; do
    if [[ "$c" == /* || "$c" == [A-Za-z]:* || "$c" == */* ]]; then abs="$c"
    else abs="$(_scenic_which "$c" "${SCENIC_HOST_PATH:-}:$PATH" || true)"; fi
    if [[ -z "$abs" ]]; then [[ "$c" == "py" ]] || why+=("$c: not found on the caller's PATH"); continue; fi
    out="$("$abs" -c "$_SCENIC_PROBE" ${want[@]+"${want[@]}"} 2>/dev/null | tr -d '\r' | grep '^SCENICPY|' | head -1 || true)"
    if [[ -z "$out" ]]; then why+=("$c -> $abs: not a usable python3 (probe produced no answer)"); continue; fi
    IFS='|' read -r tag exe ver miss <<<"$out" || true
    if [[ "$(printf '%s\n%s\n' "$SCENIC_PY_MIN" "$ver" | sort -V | head -1)" != "$SCENIC_PY_MIN" ]]; then
      why+=("$c -> $exe is $ver, below the $SCENIC_PY_MIN this repo needs"); continue
    fi
    if [[ "$miss" != "-" ]]; then why+=("$c -> $exe ($ver) has no ${miss//,/, }"); continue; fi
    SCENIC_PY="$abs"; SCENIC_PY_EXE="$exe"; SCENIC_PY_VERSION="$ver"
    # An audit line, never a boundary. It names the path THIS FILE executed, not the sys.executable the
    # probe reported, because a shim writes the second and cannot write the first. Printed whenever the
    # caller chose the interpreter - PYTHON=, or a directory outside _SCENIC_TRUSTED - so the one input
    # seal.sh (b) leaves open is in the transcript instead of silent. Trusted python (CI) stays quiet.
    pdir="$(dirname "$abs")"
    if [[ "$SCENIC_PY_SOURCE" == "PYTHON=" ]] || ! _scenic_in_list "$pdir" "$_SCENIC_TRUSTED"; then
      echo "${0##*/}: interpreter $abs ($ver, via $SCENIC_PY_SOURCE) - caller-supplied, not authenticated" >&2
    fi
    return 0
  done
  { echo "${0##*/}: no usable python."
    if [[ ${#want[@]} -gt 0 ]]; then echo "  needs: python >= $SCENIC_PY_MIN with ${want[*]}"
    else                             echo "  needs: python >= $SCENIC_PY_MIN (standard library only)"; fi
    echo "  PYTHON=${PYTHON:-<unset>}   candidates tried, in order:"
    if [[ ${#why[@]} -gt 0 ]]; then printf '    %s\n' "${why[@]}"
    else                            echo "    (none - no python on the caller's PATH at all)"; fi
    if [[ -n "${PYTHON:-}" ]]; then echo "  PYTHON is set, so it is the ONLY candidate - unset it to search PATH."; fi
    echo "  Refusing to run: a wrapper that cannot say which interpreter it used cannot be believed."
  } >&2
  return 2
}

# "path (x.y.z)" - for the failure message of anything that shells out to $SCENIC_PY. T-0076: whatever
# fails must name the interpreter it used and its version, or the next agent debugs the wrong subsystem.
scenic_py_id() { printf '%s (%s, via %s)' "${SCENIC_PY_EXE:-?}" "${SCENIC_PY_VERSION:-?}" "${SCENIC_PY_SOURCE:-?}"; }
