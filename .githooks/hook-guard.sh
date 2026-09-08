#!/usr/bin/env bash
# Provenance guard, sourced first thing by every hook in this directory.
#
# Two jobs, both of which exist because core.hooksPath is machine-local, untracked, shared by every worktree,
# and fails OPEN. When it holds an absolute path it names ONE checkout, so every worktree runs that
# checkout's hooks; when it is unset git looks in $GIT_DIR/hooks, which is empty here and so runs nothing.
# Either way the commit succeeds and prints nothing, which is indistinguishable from the hooks having
# passed. ops/lib/hookspath-state reads the configured value; this reads the observed one - the file that
# is actually executing - which is the fact that matters and the only one that cannot be stale.
#
#   1. PROVENANCE. Print one line naming the hook, the git blob id of the file that is running, and the
#      absolute directory it ran from:
#
#          HOOK pre-commit 1817aafa89e7 /c/Users/.../wt/T-0106/.githooks/pre-commit
#
#      A hook red/green transcript is only evidence if the hook that ran was the branch's, and until now
#      nothing in a transcript said which file ran. Now it does, and the claim is checkable after the fact:
#      `git hash-object .githooks/pre-commit` on the branch must equal the id in the transcript.
#
#   2. REFUSAL. If the running file is not this worktree's own .githooks/<hook>, refuse the commit and say
#      so. That is the moment it matters: at the top of a session the value can still change under you, and
#      on 2026-09-08 it did.
#
# Usage from a hook:
#     . "$(dirname "${BASH_SOURCE[0]:-$0}")/hook-guard.sh" || { echo "hook-guard.sh missing" >&2; exit 1; }
#     hook_guard <name> "${BASH_SOURCE[0]:-$0}" || exit 1
#
# Runnable directly for demonstration, which is how ops/lib/check-hook-guard asserts it still refuses:
#     bash .githooks/hook-guard.sh pre-commit /some/other/dir/pre-commit    # -> non-zero

hook_guard() {
  local name="${1:-}" self="${2:-}" dir top want id
  if [[ -z "$name" || -z "$self" ]]; then
    echo "hook-guard: called without a hook name and its own path - provenance cannot be established" >&2
    echo "hook-guard: refusing rather than passing a check that inspected nothing" >&2
    return 1
  fi

  # Both sides normalised the same way. `git rev-parse --show-toplevel` prints C:/... on this checkout while
  # `pwd -P` prints /c/..., so comparing one against the other marks a correct setup as wrong.
  dir="$(cd "$(dirname "$self")" 2>/dev/null && pwd -P || true)"
  top="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  want="$(cd "$top/.githooks" 2>/dev/null && pwd -P || true)"

  id="$(git hash-object "$self" 2>/dev/null || true)"
  printf 'HOOK %s %s %s\n' "$name" "${id:0:12}" "${dir:-UNRESOLVED}/$(basename "$self")" >&2

  if [[ -z "$dir" || -z "$top" || -z "$want" ]]; then
    echo "hook-guard: cannot resolve where this hook ran from (dir='$dir' top='$top' want='$want')." >&2
    echo "hook-guard: refusing the commit - an unverifiable hook is not a passing hook." >&2
    return 1
  fi

  if [[ "$dir" != "$want" ]]; then
    echo "hook-guard: REFUSING - the $name hook that git ran is" >&2
    echo "    $dir/$name" >&2
    echo "  but this worktree's hook is" >&2
    echo "    $want/$name" >&2
    echo "  configured core.hooksPath: '$(git config --get core.hooksPath 2>/dev/null || echo UNSET)'" >&2
    echo "  Your commits are being policed by that other file, on whatever branch its checkout has out, and" >&2
    echo "  a hook red/green demonstrated here by committing tests that copy and not yours." >&2
    echo "  A human fixes it once, in the .git/config every worktree shares:" >&2
    echo "      git config core.hooksPath .githooks" >&2
    echo "  (relative - git resolves it against each worktree's own top level). Then re-run: ops/sane" >&2
    return 1
  fi
  return 0
}

# Directly invoked rather than sourced: run the guard on the arguments and exit with its status.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  hook_guard "$@"
  exit $?
fi
