---
id: T-0098
title: the seal is sourced from a path the caller can move, so three closed routes reopen
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/boot.sh, ops/lib/seal.sh]
pins_affected: []
reviewer: null
depends_on: [T-0086]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**An independent verifier defeated three of the seven routes [[T-0086]] marked CLOSED, and two of them are
the same structural defect: the seal is loaded from a path computed with tools the caller controls.**

Verdict `holds=false`, measured against the committed fix (`git diff HEAD --stat` empty throughout) with one
untracked `Sources/ScenicKit/StrayAdversary.swift` planted and the honest answer `SANE FAIL exit=2`
established first.

**1. The structural one — `SCENIC_ROOT` is computed before anything is trusted, using untrusted helpers.**
`ops/lib/boot.sh` lines 65-76 resolve `dirname`, `basename` and `readlink` through the **caller's** `PATH` to
compute `SCENIC_ROOT`, and line 95 then does `source "$SCENIC_ROOT/ops/lib/seal.sh"`. So a seven-line shim
named `dirname` that lies only for `*/boot.sh` moves `SCENIC_ROOT` to an attacker tree carrying the five
marker files, and **boot.sh sources the adversary's `seal.sh`**. No `env -i`, no allowlist, no re-exec and no
re-exec-target check ever runs.

    PATH=<shim dir>:$PATH bash ops/sane     ->  SANE OK   EXIT=0   (with the stray import on disk)
    same shim:                                  PINS ok=99 skipped=0 pending=0 expired=0 failed=0  EXIT=0
    same shim:                                  QUEUE OK (999 tasks)  EXIT=0

Those last two strings are, verbatim, the ones `boot.sh`'s own header cites as the measured proof of the
T-0077 defect it exists to close. T-0086 made `git` absolute; the neighbouring names in the same family are
still resolved from the caller.

**2. The same defect through a different door.** The fixer blinded `declare`, shadowed `cd`, and closed the
entry-shell route by validating the re-exec TARGET against `SCENIC_ROOT`. But `SCENIC_ROOT` is computed by
the same shadowable helpers, and line 95 sources `seal.sh` **before that validation exists**:

    env BASH_FUNC_declare%%='() { :; }' \
        BASH_FUNC_dirname%%='() { case $1 in */boot.sh) echo <fake>/ops/lib;; *) /usr/bin/dirname "$@";; esac; }' \
        bash ops/sane                    ->  SANE OK   EXIT=0

Same landing point as route 1 by a completely different mechanism. **The validation is downstream of the
value it validates against** — which is the general shape, and the thing to fix.

**3. `HOME` defeats the git seal one mechanism over, with a variable that is on the keep-list by design.**
`core.excludesFile` is not only a config key; it has a DEFAULT PATH derived from `$HOME`.
`GIT_CONFIG_GLOBAL=/dev/null` deletes the global config FILE and does not touch `$HOME/.config/git/ignore`,
which git reads when `core.excludesFile` is unset. `HOME` is forwarded through `env -i` deliberately.

    HOME=<dir with .config/git/ignore containing *.swift>  bash ops/sane  ->  SANE OK   EXIT=0
    HOME=<empty dir>                                        bash ops/sane  ->  SANE FAIL exit=2

The tight control is the second line: the ignore file is the only variable. It also survives the fixer's own
strongest test verbatim — `env -i PATH=<trusted> SCENIC_SEALED=1 SCENIC_HOST_PATH=<py> HOME=<evil>` — which
the T-0086 log records as `SANE FAIL exit=2`. Two sentences in `seal.sh` are therefore false as written:
*"so no HOME-shaped name reaches git's config"* and *"neither PATH nor HOME nor XDG_CONFIG_HOME nor a name
nobody has thought of can reach it"*.

**Do not fix these one at a time.** Routes 1 and 2 are one bug and route 3 is the same *class* — a guard
whose input is computed by the thing it guards against. The candidate fixes, in order of how much they close:

1. Resolve `SCENIC_ROOT` without any external command: bash's own `${BASH_SOURCE[0]}` with parameter
   expansion (`${p%/*}`) and `cd -P`/`pwd -P` builtins only. No `dirname`, no `basename`, no `readlink`,
   and no `$(...)` that runs a program off `PATH` before the seal is up.
2. Validate the seal BEFORE sourcing it, not after — its path must be under a root proven by construction,
   and the check must not depend on any value the caller supplied.
3. For `HOME`: either neutralise every git input derived from it (`GIT_CONFIG_GLOBAL`, `XDG_CONFIG_HOME`,
   and `core.excludesFile` set explicitly, not merely unset), or stop forwarding `HOME` and give the sealed
   child a scratch `HOME` the tool owns. Say which, and why, in the log.

**Two routes T-0086 already declares OPEN and this task inherits:** the interpreter is still resolved from
the caller's `PATH` (route 1, one mechanism over), and `SHELLOPTS=noexec` is imported by bash at startup,
before line 1 of any script.

**And a rule the verifier earned:** three rounds of this have now ended `holds=false`, each time on "the
neighbour one over" rather than on the route as named. Enumerating routes does not converge — the same
conclusion [[T-0080]] reached for pin assertions, and the same answer applies: the closure test must be
mechanical (inject, require red), not a list of names somebody thought of.

## Log
