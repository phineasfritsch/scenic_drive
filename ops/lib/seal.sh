#!/usr/bin/env bash
# THE ENVIRONMENT AN ops/* SCRIPT RUNS IN. Sourced by ops/lib/boot.sh once the root is known, never on
# its own: it needs _scenic_resolve and SCENIC_ROOT from part 1 of boot.sh. Split out of boot.sh at that
# seam for the 300-line cap (T-0086); boot.sh remains the only file a wrapper sources.
#
# ---------------------------------------------------------------------------------------------------
# THE ENVIRONMENT IS AN ALLOWLIST, ENFORCED BY RE-EXEC, NOT BY UNSETTING NAMES.
#
# boot.sh used to unset fifteen GIT_* names so that "an ops/* script talks to the repo it lives in,
# whatever the caller's environment says". A round-three adversary defeated that sentence three times
# with no edit to any tracked file, each time with a name that was not on the list. Measured with one
# untracked Sources/ScenicKit/StrayAdversary.swift planted; the honest answer is SANE FAIL exit=2:
#
#   GIT_CONFIG_PARAMETERS="'core.excludesFile=<windows-form path>'" bash ops/sane -> SANE OK exit=0
#     The one GIT_CONFIG_* name the unset list missed, the immediate neighbour of the GIT_CONFIG_COUNT
#     /KEY_0 pair it did clear, and the mechanism `git -c` itself uses. (git silently ignores the msys
#     /c/... form of that path; the Windows form is required to reproduce.)
#   PYTHONPATH=<dir with a 12-line sitecustomize.py> bash ops/check-pins, and bash ops/queue-check
#     -> PINS ok=99 skipped=0 pending=0 expired=0 failed=0 tier=linux   EXIT=0
#        QUEUE OK (999 tasks)                                           EXIT=0
#     Zero pins loaded, zero assertions run: `site` imports sitecustomize from sys.path at startup, and
#     sys.path is what the caller writes. Those two strings are verbatim the ones boot.sh's own header
#     cites as the measured proof of the ORIGINAL T-0077 defect. The list unset fifteen GIT_* names and
#     zero PYTHON* ones.
#   PATH=<dir with a 15-line script named git>:$PATH bash ops/sane -> SANE OK, stray still on disk.
#     Every checker and every pin assertion resolved `git` from the caller. Nothing touched PATH.
#
# A denylist of variable names is the same losing game as a denylist of SQL keywords: the next
# adversary brings the next name. Two nobody had listed, found while writing this fix and measured the
# same way on the same tree:
#
#   HOME=<dir holding a .gitconfig that sets core.excludesFile> bash ops/sane -> SANE OK exit=0.
#     No GIT_* name at all. (XDG_CONFIG_HOME was tried identically, with and without a ~/.gitconfig
#     present, and did NOT reproduce on this box. Recorded as measured: an unverified claim in a file
#     like this one is worse than no claim.)
#   PYTHONUSERBASE=<dir with Python314/site-packages/usercustomize.py> bash ops/check-pins -> the same
#     two false-green strings. Neither GIT nor PYTHONPATH appears in the name.
#
# SO THE LIST IS AN ALLOWLIST AND IT IS ENFORCED BY RE-EXEC. The first thing an ops/* script does is
# re-exec ITSELF through `env -i` with an environment built from the constants below. Anything not
# named is gone, INCLUDING names invented after this task - that property is the entire point and the
# only one worth claiming. The sealed pass then VERIFIES its own environment against those same
# constants and RE-DERIVES every value it uses, so a hand-set SCENIC_SEALED=1 buys nothing but what
# (b) below concedes. Measured: under `env -i PATH=<trusted> SCENIC_SEALED=1 ...`, each of
# GIT_CONFIG_GLOBAL=<an evil .gitconfig>, SCENIC_GIT=<the git shim>, PATH=<the git shim>:<trusted> and
# HOME=<the evil home> gave SANE FAIL exit=2, with an interpreter reachable so the checks really ran.
#
# WHEN THE ENVIRONMENT IS HOSTILE THIS FILE REFUSES: exit 2, naming the variables. That is the
# decision, in writing - refusing is cheap, and a checker that runs in an environment it cannot
# describe cannot be believed. `git` is then resolved to an ABSOLUTE path (a sanitized PATH is still a
# PATH) and GIT_CONFIG_GLOBAL is pinned to /dev/null, so no HOME-shaped name reaches git's config.
# Measured inside the seal with a git shim, a grep shim, an evil HOME and GIT_CONFIG_PARAMETERS all set
# by the caller, a pin assertion (pins.py runs them through `bash -c`) still saw git=/mingw64/bin/git,
# grep=/usr/bin/grep, core.excludesFile=<none>, core.autocrlf=false, 17 environment variables in total.
#
# WHAT IS STILL OPEN, in writing, each with the command that survives it:
# (a) a tool that exists only in the caller's PATH - swift, node, npx, docker - is still found there for
#     SCENIC_TOOLCHAIN=1 scripts. It is appended AFTER the trusted directories, so a shim can only win
#     for a name no trusted directory provides; git, grep and the interpreter are not such names. That
#     a shimmed `swift` can still write a junit report is why the test floors are committed files.
# (b) THE INTERPRETER. No python lives in any trusted directory on this box, so it is resolved out of
#     SCENIC_HOST_PATH - the caller's PATH, forwarded for exactly this and nothing else. NOT CLOSED:
#         PATH=<dir with a shim named python3>:$PATH bash ops/queue-check     -> QUEUE OK (999 tasks)
#         env -i PATH=<trusted> SCENIC_SEALED=1 SCENIC_HOST_PATH=<that dir> bash ops/queue-check -> same
#     This is the position boot.sh part 3 already states, not a new one: aiming the interpreter is
#     exactly what PYTHON= does, and a probe cannot tell a shim from a python because it asks the thing
#     under test to describe itself. What the seal DOES remove is INJECTION into a legitimate
#     interpreter - PYTHONPATH, PYTHONSTARTUP, PYTHONUSERBASE and APPDATA/usercustomize are all gone.
#     scenic_python prints the absolute path it actually executed whenever that path is outside the
#     trusted directories, so a shimmed interpreter is named in the transcript instead of being silent.
# (c) THE ENTRY SHELL. An exported function (BASH_FUNC_git%%) or BASH_ENV is refused on sight by part 0
#     of boot.sh, and the seal removes both from every child - which is what actually matters, because
#     pins.py runs its assertions through `bash -c`. But part 0 is written IN the shell it is judging,
#     and `declare` can itself be an exported function. Measured against the first draft of this fix:
#         env "BASH_FUNC_declare%%=() { :; }" "BASH_FUNC_cd%%=<lies outside ops/lib>" bash ops/sane
#             -> SANE OK exit=0 with the stray on disk: the seal re-exec'd the ADVERSARY's script.
#     A $0 re-check in the SEALED pass does not catch that - the adversary's script never sources this
#     file - so the re-exec target is validated in the UNSEALED pass instead, against SCENIC_ROOT, with
#     nothing but keywords and parameter expansion. Both that and its neighbour now refuse, exit 2:
#         ...same command as above                                          -> refusing: the re-exec
#         env "BASH_FUNC_declare%%=..." "BASH_FUNC_basename%%=<returns queue-check>" bash ops/sane
#             -> refusing: target resolved to <root>/ops/queue-check, which is not <root>/ops/sane.
#             Worth its own line: that one re-aims a checker at a DIFFERENT REAL wrapper, so it would
#             have printed QUEUE OK and exited 0 without any adversary-written file existing at all.
#     The sealed pass keeps its own $0 check, which is what refuses an out-of-tree script that sources
#     boot.sh directly. What remains is unreachable from a bash script at all - bash imports SHELLOPTS
#     before line 1 of anything:
#         env SHELLOPTS=noexec bash ops/sane      -> no output whatsoever, EXIT=0
#     Nothing in this file executes, so nothing in it can object. The decision, in writing: every ops/*
#     wrapper prints at least one line on every run, so a caller that gets EMPTY output and exit 0 has
#     been lied to and must treat it as a failure. That is a property of the caller, not of this file.
# ---------------------------------------------------------------------------------------------------

# THE ONLY VARIABLES THAT SURVIVE. Add a name here, with a reason, or it does not exist inside ops/*.
# SCENIC_GIT is here because an already-sealed ops/* script may run another one (P-PROC-01's assertion
# is `bash ops/queue-check`); it is exported for pins.py's subprocesses and RE-DERIVED, never read back.
_SCENIC_SET='PATH LANG LC_ALL TERM PYTHONNOUSERSITE GIT_CONFIG_GLOBAL SCENIC_SEALED SCENIC_HOST_PATH SCENIC_GIT'
# forwarded when present, because a real local need reads them (each documented at its use site):
_SCENIC_KEEP='HOME TMPDIR TMP TEMP PYTHON API_URL SCENIC_RO_TOKEN SKIP_IOS IOS_DESTINATION DEPLOY_UNLOCKED CI'
# forwarded ON TOP of those only for SCENIC_TOOLCHAIN=1 scripts: swift, node/npx and docker on Windows
# do not start without them. APPDATA is here, and is why PYTHONNOUSERSITE=1 is in _SCENIC_SET, not
# optional: APPDATA alone reaches site.USER_SITE and usercustomize.py.
_SCENIC_TOOLENV='APPDATA LOCALAPPDATA USERPROFILE PROGRAMDATA ALLUSERSPROFILE PROGRAMFILES PROGRAMW6432
 SYSTEMDRIVE COMSPEC PATHEXT NUMBER_OF_PROCESSORS PROCESSOR_ARCHITECTURE OS USERNAME HOMEDRIVE HOMEPATH
 DEVELOPER_DIR SDKROOT'
# set by bash/msys itself inside the sealed child, so they are expected there and are not forwarded.
# SHELLOPTS and BASHOPTS are deliberately NOT here: if bash ever exports one, the seal must refuse.
_SCENIC_SHELL_SET='PWD OLDPWD SHLVL _ MSYSTEM SYSTEMROOT WINDIR'
# git is never resolved through PATH. First existing entry wins.
_SCENIC_GIT_CAND='/mingw64/bin/git /usr/bin/git /usr/local/bin/git /bin/git /opt/homebrew/bin/git'
_SCENIC_TRUSTED='/usr/local/bin /usr/local/sbin /usr/bin /usr/sbin /bin /sbin /mingw64/bin /opt/homebrew/bin'

_scenic_in_list() { local n="$1" w; for w in $2; do [[ "$w" == "$n" ]] && return 0; done; return 1; }

_scenic_which() {                        # _scenic_which <name> <PATH-shaped list> -> absolute path
  local n="$1" d; local IFS=:
  for d in $2; do
    [[ -n "$d" ]] || continue
    [[ -x "$d/$n" && ! -d "$d/$n" ]] && { printf '%s\n' "$d/$n"; return 0; }
    [[ -x "$d/$n.exe" ]] && { printf '%s\n' "$d/$n.exe"; return 0; }
  done
  return 1
}

SCENIC_GIT=""
for _c in $_SCENIC_GIT_CAND; do [[ -x "$_c" ]] && { SCENIC_GIT="$_c"; break; }; done
unset _c
if [[ -z "$SCENIC_GIT" ]]; then
  echo "${0##*/}: no git at any of: $_SCENIC_GIT_CAND" >&2
  echo "  git is resolved by absolute path, never through PATH: a script named git earlier on the" >&2
  echo "  caller's PATH filtered 'git status' and turned SANE FAIL into SANE OK (T-0086)." >&2
  return 2 2>/dev/null || exit 2
fi

# MSYS rewrites ANY environment value that looks like a POSIX path list into Windows form when it hands
# it to a native program - measured, by value, not by name - so SCENIC_HOST_PATH comes back as
# `C:\a;C:\b` in a nested wrapper (ops/check-pins -> python -> `bash ops/queue-check` for P-PROC-01) and
# nothing splits on ':' any more. Convert it back, or the nested wrapper reports "no usable python".
if [[ "${SCENIC_HOST_PATH:-}" == *';'* && -x /usr/bin/cygpath ]]; then
  SCENIC_HOST_PATH="$(/usr/bin/cygpath -u -p "$SCENIC_HOST_PATH" 2>/dev/null || printf '%s' "$SCENIC_HOST_PATH")"
fi

# PATH is REBUILT, never inherited: trusted system directories, git's own directory first.
SCENIC_PATH="$(dirname "$SCENIC_GIT")"
for _d in $_SCENIC_TRUSTED; do [[ -d "$_d" && ":$SCENIC_PATH:" != *":$_d:"* ]] && SCENIC_PATH="$SCENIC_PATH:$_d"; done
unset _d
[[ "${SCENIC_TOOLCHAIN:-0}" == "1" ]] && SCENIC_PATH="$SCENIC_PATH:${SCENIC_HOST_PATH:-${PATH:-}}"

if [[ "${SCENIC_SEALED:-}" != "1" ]]; then
  # ---- unsealed: build the sealed environment and re-exec. No measurement happens before this. ------
  _s="$0"; [[ "$_s" != /* && "$_s" != [A-Za-z]:* ]] && _s="$PWD/$_s"
  _s="$(_scenic_resolve "$_s" 2>/dev/null || printf '%s\n' "$_s")"
  if [[ ! -r "$_s" ]]; then
    echo "${0##*/}: refusing: cannot locate the script to re-exec ($0)." >&2
    echo "  ops/lib/boot.sh is sourced by an ops/* script, not by an interactive shell." >&2
    return 2 2>/dev/null || exit 2
  fi
  # $_s was computed with dirname, cd, pwd, printf and basename - every one of which the caller can
  # replace with an exported function, and part 0 of boot.sh cannot see it because `declare` is
  # replaceable too. So the target is checked against SCENIC_ROOT, which is either honest or already
  # refused by boot.sh's marker assert, using ONLY shell keywords and parameter expansion: there is no
  # command on these two lines to shadow. The basename must match too, or a lying `basename` re-aims
  # `bash ops/sane` at a different real wrapper - ops/queue-check prints QUEUE OK and exits 0.
  if [[ "$_s" != "$SCENIC_ROOT"/ops/* || "${_s##*/}" != "${0##*/}" ]]; then
    echo "${0##*/}: refusing: the re-exec target resolved to" >&2
    echo "    $_s" >&2
    echo "  which is not $SCENIC_ROOT/ops/${0##*/}. A caller that can define shell functions can make" >&2
    echo "  this pass compute the wrong \$0: a shadowed 'declare' blinds the clean-shell test in" >&2
    echo "  boot.sh part 0, and a shadowed 'cd' then moves the target (T-0086)." >&2
    return 2 2>/dev/null || exit 2
  fi
  _env=/usr/bin/env; [[ -x "$_env" ]] || _env=/bin/env
  _kv=(PATH="$SCENIC_PATH" SCENIC_HOST_PATH="${PATH:-}" SCENIC_SEALED=1 LANG=C LC_ALL=C TERM=dumb
       PYTHONNOUSERSITE=1 GIT_CONFIG_GLOBAL=/dev/null)
  _names="$_SCENIC_KEEP"
  [[ "${SCENIC_TOOLCHAIN:-0}" == "1" ]] && _names="$_names $_SCENIC_TOOLENV"
  for _n in $_names; do
    [[ "$_n" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    [[ -n "${!_n+x}" ]] && _kv+=("$_n=${!_n}")
  done
  exec "$_env" -i "${_kv[@]}" "${BASH:-/bin/bash}" "$_s" ${@+"$@"}
  echo "${0##*/}: refusing: could not re-exec through $_env -i (is exec shadowed?)" >&2
  exit 2
fi

# ---- sealed: verify. The marker is not trusted; the environment is checked against the constants. ---
_bad=""
for _n in $(compgen -e); do
  _scenic_in_list "$_n" "$_SCENIC_SET $_SCENIC_KEEP $_SCENIC_TOOLENV $_SCENIC_SHELL_SET" || _bad="$_bad $_n"
done
if [[ -n "$_bad" ]]; then
  echo "${0##*/}: refusing: variable(s) outside the ops/lib/seal.sh allowlist survived the seal:$_bad" >&2
  echo "  ops/* runs in an environment built from a fixed list, not in the caller's. Nothing is unset" >&2
  echo "  by name; anything not named is absent. SCENIC_SEALED=1 is not a way in - this check is what" >&2
  echo "  gates the run, and it does not consult the marker." >&2
  return 2 2>/dev/null || exit 2
fi
unset _bad _n

# The seal re-execs $0, and the unsealed pass computed $0 with helpers the caller can replace - see (c).
# Here there are no functions (env -i dropped every BASH_FUNC_*) and SCENIC_ROOT is derived from
# boot.sh's own path, so the target is re-checked against it: a wrapper of THIS repo, or nothing.
_self="$0"; [[ "$_self" != /* && "$_self" != [A-Za-z]:* ]] && _self="$PWD/$_self"
_self="$(_scenic_resolve "$_self" 2>/dev/null || printf '%s\n' "$_self")"
case "$_self" in
  "$SCENIC_ROOT"/ops/*) ;;
  *) echo "${0##*/}: refusing: $_self is not an ops/* script of $SCENIC_ROOT." >&2
     echo "  The seal re-execs \$0 through env -i. A caller that can define shell functions can make" >&2
     echo "  the unsealed pass compute the wrong \$0: a shadowed 'declare' blinds boot.sh part 0, and" >&2
     echo "  a shadowed 'cd' then moves the target. This pass has no functions, so it re-checks." >&2
     return 2 2>/dev/null || exit 2 ;;
esac
unset _self

export PATH="$SCENIC_PATH" GIT_CONFIG_GLOBAL=/dev/null PYTHONNOUSERSITE=1 SCENIC_GIT
# PATH, SCENIC_GIT and GIT_CONFIG_GLOBAL are all re-derived above from the constants and never read back
# from the environment: a forged SCENIC_SEALED=1 carrying SCENIC_GIT=<shim> or GIT_CONFIG_GLOBAL=<file>
# gets neither (measured, above). They are exported so pins.py's `bash -c` assertions and queue.py's
# subprocesses inherit the same repo-only git.

# Every `git` in an ops/* script is this: the absolute binary, with the global config pinned off, so
# neither PATH nor HOME nor XDG_CONFIG_HOME nor a name nobody has thought of can reach it. Not exported:
# an exported function is BASH_FUNC_git%%, which is exactly the attack the seal exists to remove.
git() { command "$SCENIC_GIT" "$@"; }
