# Make a temp directory whose path the interpreter on PATH can actually open. Source this; do not run it.
#
#   source "$(dirname "${BASH_SOURCE[0]}")/tmpdir.sh"
#   TMP="$(portable_mktemp_d)"
#
# WHY THIS EXISTS. `mktemp -d` in git-bash returns an MSYS path, `/tmp/tmp.XXXXXX`. The interpreter on PATH
# on this checkout is a WINDOWS python, which reads a leading `/` as a relative path and looks for
# `C:\tmp\tmp.XXXXXX`. Three checks failed that way, every time, on the machine this project is driven from:
#
#   check-lock-lifecycle   FAIL: review accepted a task that was not claimed (rc=2):
#                          can't open file 'C:\tmp\tmp.ASM3sx3tVQ\ops\lib\queue.py'
#   check-brief-required   can't open file 'C:\tmp\tmp.LBnyMFYgea\ops\lib\queue.py'
#   check-failure-naming   junit_count: cannot read /tmp/tmp.fH9vq5U3Uo/per-case.xml
#
# They are green in Linux CI, so the failure reads as "environmental" and gets stepped over - which is how
# a real failure in one of them would also be stepped over. Two of the three guard the queue protocol.
#
# `cygpath -w` is the translation and it exists only under MSYS/Cygwin. On Linux and WSL there is no
# `cygpath`, the POSIX path is already the right one, and this is a no-op.
#
# A HELPER RATHER THAN THREE INLINE COPIES, deliberately: the next check to be written will copy whichever
# neighbour its author happens to open, and one shared function is the only version of this that stays
# fixed. `ops/check-tests` has the same translation inline for its own directory; that is a different
# question (locating the script, not making a temp dir) and is documented there.

portable_mktemp_d() {
  local d
  d="$(mktemp -d)" || return 1
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$d"
  else
    printf '%s\n' "$d"
  fi
}

# The POSIX form of the same directory, for `rm -rf` and other shell-side use: `rm -rf "$(cygpath -w ...)"`
# works in practice but the backslashes are an escaping hazard in a trap, and a trap that fails to fire
# leaves a temp tree behind on every run.
portable_posix_path() {
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -u "$1"
  else
    printf '%s\n' "$1"
  fi
}
