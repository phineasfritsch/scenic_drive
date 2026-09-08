#!/usr/bin/env bash
# TWO DECISIONS, MADE ONCE, HERE: where an ops/* script finds the repo, and which python it runs.
# Sourced, never executed:   source "$(dirname "${BASH_SOURCE[0]}")/lib/boot.sh" || exit 2
#
# ---------------------------------------------------------------------------------------------------
# 1. THE REPO ROOT COMES FROM THIS FILE'S OWN PATH, NEVER FROM THE CALLER.
#
# Every wrapper used to say `git rev-parse --show-toplevel`, which answers "the repo the CALLER is
# standing in". Run this repo's ops/check-pins from inside any other git repository and it executed
# THAT repository's ops/lib/pins.py (T-0077). Measured, from a four-line synthetic module:
#     PINS ok=99 skipped=0 pending=0 expired=0 failed=0 tier=linux   EXIT=0
#     QUEUE OK (999 tasks)                                           EXIT=0
#     SANE OK                                                        EXIT=0
# with nothing in this repo modified. Every guard in pins.py - the population floors, REQUIRED,
# REQUIRED_RAN, the strict argv parser, the run floor - was bypassed at once by choosing a directory.
# The `cd`-family wrappers (ops/test, ops/sane, ops/agent-preflight, ops/deploy, ops/prod-read) had the
# same defect through a different door: they cd'd to the caller's toplevel and then read ITS pins/floor_*.txt
# and ran ITS ops/lib/*.py. T-0055 fixed the first eight on a branch that never reached main.
#
# ${BASH_SOURCE[0]} is this file, so the root is a property of where the SCRIPT lives. Symlinks are
# resolved (`cd -P` for every directory component, a loop for the final one) because a symlink planted in
# a hostile tree is the adjacent form of the same attack: it makes BASH_SOURCE point at the attacker.
#
# 2. THE INTERPRETER IS CHOSEN BY CAPABILITY, NOT BY NAME - AND `PYTHON=` IS A CONVENIENCE, NOT A GUARD.
#
# `${PYTHON:-$(command -v python3 || command -v python)}` picks by NAME. `python3` wins whenever it exists,
# even when it is the wrong installation. On the box this was written on the two names are different
# products:
#     python3 -> AppData\Local\Python\pythoncore-3.14-64\python.exe   3.14.5    pytest: False
#     python  -> AppData\Local\Programs\Python\Python310\python.exe   3.10.11   pytest: True
# so ops/test ran an interpreter with no pytest, wrote no report, and stopped with
# "FAIL: services/etl exists but pytest produced no report" - blaming the ETL tier for the interpreter
# (T-0076). scenic_python asks each candidate what it CAN DO and takes the first that can do it.
#
# On PYTHON=, in writing, so it is not decided by omission in eleven files: it is honoured, it is a real
# local need (a venv, a pyenv shim, an explicit python3.12), and it is NOT a security boundary. T-0072 added
# a probe to ops/check-pins to refuse `PYTHON=true`; a four-line script that echoes the probe token defeated
# it in one try, and it always will - a probe asks the thing under test to describe itself, and the token is
# printed in the script the adversary is reading. So this file does not pretend. What the probe is FOR is the
# accident: a missing python, a python2, a python without the modules this script needs. Those it catches,
# and it names the interpreter, its real sys.executable and its version when it refuses, because a path and a
# version would have ended T-0076 in seconds. Anyone who can set PYTHON can also edit this file; the defence
# against a hostile operator is the reviewer and the pre-commit hook, not a shell test.
# When PYTHON is set it is the ONLY candidate: falling back silently would ignore the venv you asked for.
# ---------------------------------------------------------------------------------------------------
set -uo pipefail

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

# A sanity assert, not a boundary: it catches a moved/renamed ops/lib, not an adversary who can plant files.
for _m in ops/lib/pins.py ops/lib/queue.py pins/PINS.yaml CLAUDE.md; do
  if [[ ! -f "$SCENIC_ROOT/$_m" ]]; then
    echo "${0##*/}: ${SCENIC_ROOT:-<unresolved>} is not the scenic_drive root (no $_m)" >&2
    echo "  The root is derived from ops/lib/boot.sh's own path, never from the caller's git toplevel." >&2
    return 2 2>/dev/null || exit 2
  fi
done
unset _m

scenic_cd_root() { cd "$SCENIC_ROOT" || { echo "${0##*/}: cannot enter $SCENIC_ROOT" >&2; exit 2; }; }

# --- 1b. git must answer about THIS repo, not about the environment ----------------------------------
# Deriving the root from BASH_SOURCE fixes the working directory and NOTHING ELSE. Every ops/* script and
# every pin assertion then shells out to git, and git picks its repository and its config from the
# ENVIRONMENT before it picks them from the working directory. Measured against the already-fixed ops/sane,
# standing in this repo, with one untracked Sources/ScenicKit/StrayAdversary.swift planted:
#     bash ops/sane                                                    -> SANE FAIL exit=2
#     GIT_DIR=<fake>/.git GIT_WORK_TREE=<fake> bash ops/sane           -> SANE OK   exit=0
#     GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf \
#       GIT_CONFIG_VALUE_0=true bash ops/sane                          -> autocrlf FAIL true
# Two environment variables moved a fixed checker's answer onto a different tree, and a third rewrote the
# config it read. That is T-0077's defect again through a different door, so it is shut in the same place:
# an ops/* script talks to the repo it lives in, whatever the caller's environment says.
# GIT_CONFIG_KEY_<n>/GIT_CONFIG_VALUE_<n> are read ONLY when GIT_CONFIG_COUNT says how many exist -
# measured: `GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=true git config --get core.autocrlf` still
# prints `false` - so clearing the count is enough, and the pairs are cleared too rather than relying on it.
_scenic_n="${GIT_CONFIG_COUNT:-0}"
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_NAMESPACE \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_CEILING_DIRECTORIES GIT_DISCOVERY_ACROSS_FILESYSTEM \
      GIT_PREFIX GIT_CONFIG GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM GIT_CONFIG_NOSYSTEM GIT_CONFIG_COUNT
if [[ "$_scenic_n" =~ ^[0-9]+$ ]]; then
  _scenic_i=0
  while [[ "$_scenic_i" -lt "$_scenic_n" && "$_scenic_i" -lt 1024 ]]; do
    unset "GIT_CONFIG_KEY_$_scenic_i" "GIT_CONFIG_VALUE_$_scenic_i"; _scenic_i=$((_scenic_i + 1))
  done
  unset _scenic_i
fi
unset _scenic_n
# No ops/* script is invoked from .githooks (grepped), so nothing here depends on the GIT_DIR/GIT_INDEX_FILE
# that git exports to a hook. If that ever changes, the hook must pass the paths, not the environment.

# --- 2. interpreter ----------------------------------------------------------------------------------
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

# scenic_python [module ...]  -> sets SCENIC_PY / SCENIC_PY_EXE / SCENIC_PY_VERSION, or returns 2 loudly.
# Written to survive `set -e` (ops/deploy and ops/prod-read run with it): no bare failing command anywhere.
scenic_python() {
  local want=("$@") cand=() c out tag exe ver miss why=()
  SCENIC_PY=""; SCENIC_PY_EXE=""; SCENIC_PY_VERSION=""   # never leave a stale answer behind on failure
  if [[ -n "${PYTHON:-}" ]]; then cand=("$PYTHON"); SCENIC_PY_SOURCE="PYTHON="
  else cand=(python3 python py) ; SCENIC_PY_SOURCE="PATH"
  fi
  for c in "${cand[@]}"; do
    if [[ "$c" == "py" ]] && ! command -v py >/dev/null 2>&1; then continue; fi
    out="$("$c" -c "$_SCENIC_PROBE" ${want[@]+"${want[@]}"} 2>/dev/null | tr -d '\r' | grep '^SCENICPY|' | head -1 || true)"
    if [[ -z "$out" ]]; then why+=("$c: not a usable python3 (probe produced no answer)"); continue; fi
    IFS='|' read -r tag exe ver miss <<<"$out" || true
    if [[ "$(printf '%s\n%s\n' "$SCENIC_PY_MIN" "$ver" | sort -V | head -1)" != "$SCENIC_PY_MIN" ]]; then
      why+=("$c -> $exe is $ver, below the $SCENIC_PY_MIN this repo needs"); continue
    fi
    if [[ "$miss" != "-" ]]; then why+=("$c -> $exe ($ver) has no ${miss//,/, }"); continue; fi
    SCENIC_PY="$c"; SCENIC_PY_EXE="$exe"; SCENIC_PY_VERSION="$ver"
    # Not a boundary - an audit line. PYTHON= cannot be made safe (see the header), but a run that used a
    # non-default interpreter should not look identical in the transcript to one that did not. This costs
    # nothing on the normal path, where PYTHON is unset and nothing is printed.
    if [[ "$SCENIC_PY_SOURCE" == "PYTHON=" ]]; then
      echo "${0##*/}: note: PYTHON=$c -> $exe ($ver), not the PATH default" >&2
    fi
    return 0
  done
  { echo "${0##*/}: no usable python."
    if [[ ${#want[@]} -gt 0 ]]; then echo "  needs: python >= $SCENIC_PY_MIN with ${want[*]}"
    else                             echo "  needs: python >= $SCENIC_PY_MIN (standard library only)"; fi
    echo "  PYTHON=${PYTHON:-<unset>}   candidates tried, in order:"
    if [[ ${#why[@]} -gt 0 ]]; then printf '    %s\n' "${why[@]}"
    else                            echo "    (none - no python on PATH at all)"; fi
    if [[ -n "${PYTHON:-}" ]]; then echo "  PYTHON is set, so it is the ONLY candidate - unset it to search PATH."; fi
    echo "  Refusing to run: a wrapper that cannot say which interpreter it used cannot be believed."
  } >&2
  return 2
}

# "path (x.y.z)" - for the failure message of anything that shells out to $SCENIC_PY. T-0076: whatever
# fails must name the interpreter it used and its version, or the next agent debugs the wrong subsystem.
scenic_py_id() { printf '%s (%s, via %s)' "${SCENIC_PY_EXE:-?}" "${SCENIC_PY_VERSION:-?}" "${SCENIC_PY_SOURCE:-?}"; }
