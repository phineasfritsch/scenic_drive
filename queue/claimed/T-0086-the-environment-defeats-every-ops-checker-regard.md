---
id: T-0086
title: the environment defeats every ops checker regardless of how the root is derived
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T04:04:59Z
lease_expires_at: 2026-09-08T10:04:59Z
worktree: wt/T-0086
branch: task/T-0086
exclusive: []
touches: [ops/lib/boot.sh, ops/lib/seal.sh, ops/agent-preflight, ops/check-pins, ops/deploy, ops/test]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

[[T-0077]] moved every `ops/*` wrapper off `git rev-parse --show-toplevel` and onto `${BASH_SOURCE[0]}`, then
added `ops/lib/boot.sh`, which unsets fifteen `GIT_*` variables so "an ops/* script talks to the repo it lives
in, whatever the caller's environment says."

**A round-three adversary defeated that sentence three ways, with no source edit in any of them.**

**1. `GIT_CONFIG_PARAMETERS` — the one `GIT_CONFIG_*` name boot.sh does not unset**, and the mechanism
`git -c` itself uses. It is the immediate neighbour of the `GIT_CONFIG_COUNT` / `GIT_CONFIG_KEY_0` pair the fix
DID clear and cited as its reason for closing the route:

    GIT_CONFIG_PARAMETERS="'core.autocrlf=true'" bash ops/sane     -> reproduces the fix's own demo verbatim
    GIT_CONFIG_PARAMETERS="'core.excludesFile=...'" bash ops/sane  -> SANE FAIL exit 2  becomes  SANE OK exit 0
                                                                       with the stray .swift still on disk

**2. `PYTHONPATH`.** T-0076 replaced "pick the interpreter by NAME" with "pick it by CAPABILITY", measured with
`importlib.util.find_spec()` — which searches `sys.path`, which the caller writes with `PYTHONPATH`. The
decision moved from a name the caller controls to an import the caller controls. Worse, `site` imports
`sitecustomize` from `sys.path` at interpreter startup, so a twelve-line `sitecustomize.py` on `PYTHONPATH`
produced:

    PINS ok=99 skipped=0 pending=0 expired=0 failed=0 tier=linux    EXIT=0
    QUEUE OK (999 tasks)                                            EXIT=0

with zero pins loaded and zero assertions run. **Those are the exact two strings boot.sh's own header cites as
the measured proof of the original defect.** boot.sh unsets fifteen `GIT_*` variables and zero `PYTHON*` ones.

**3. `PATH`.** A fifteen-line shell script named `git`, earlier on `PATH`, passing everything through except
`git status` (and later `git ls-files`), from which it filters the evidence. Every `ops/*` checker and every
pin assertion resolves `git` from the caller. boot.sh never touches `PATH`.

**The shape is the finding, not the three names.** A denylist of environment variables is the same losing game
as a denylist of SQL keywords or a list of cannot-fail assertion texts, and this repository has now lost it
three times in three different files. Every fix so far has hardened the mechanism it was pointed at while the
caller kept a different lever.

- **Allowlist the environment instead.** Re-exec through `env -i` with an explicit, minimal set
  (`PATH`, `HOME`, `LANG`, `TMPDIR`, and whatever a specific script genuinely needs), rather than unsetting
  names somebody has to keep remembering. Anything not named is gone, including names invented after this task.
- **Resolve `git` and the interpreter by absolute path** once, at boot, and use those paths everywhere.
  A sanitized `PATH` is still a `PATH`.
- Decide what an ops script should do when the environment is hostile: refusing is defensible and cheap.
  Whatever it is, it must be a decision in the file, not an omission.
- The three demonstrations above are reproducible as written and belong in the log as the red run.
- **Do not close this by adding `GIT_CONFIG_PARAMETERS`, `PYTHONPATH` and `PATH` to the unset list.** That is
  the fourth round of the same mistake, and the next adversary will bring the fifth name.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the round-three adversarial verification of T-0077 and T-0076.
  Every command above was executed by an agent that did not write the fix, with no edit to any tracked source
  file.
- 2026-09-08T04:04:59Z claimed by agent/claude-opus-5; lease until 2026-09-08T10:04:59Z

### 2026-09-08 agent/claude-opus-5 — FIX, on task/T-0086

`touches:` widened to `[ops/lib/boot.sh, ops/lib/seal.sh, ops/agent-preflight, ops/check-pins, ops/deploy,
ops/test]`. The wrappers changed only to declare `SCENIC_TOOLCHAIN=1`; `ops/lib/seal.sh` is new.

**THE FIX.** `ops/lib/boot.sh` no longer unsets names. An `ops/*` script re-execs ITSELF through `env -i`
with an environment built from constant lists, so anything not named is gone including names invented after
this task. The sealed pass verifies its own environment against those same constants and RE-DERIVES every
value it uses, so a hand-set `SCENIC_SEALED=1` buys nothing. `git` is resolved to an absolute path and
`GIT_CONFIG_GLOBAL` is pinned to `/dev/null`. When the environment is hostile the file REFUSES, exit 2,
naming the variables — that decision is written into `ops/lib/seal.sh`, not left to omission.

Split at a real seam for the 300-line cap (hard rule 7, not an exemption): `ops/lib/seal.sh` (224 lines)
owns the environment, `ops/lib/boot.sh` (163) keeps the root and the interpreter and sources it. `boot.sh`
is still the only file a wrapper sources. `seal.sh` committed 100755; `P-OPS-01: 25 files, 15 required
present, all modes correct`.

All transcripts below are verbatim. RED runs are against HEAD before the fix; GREEN runs use the IDENTICAL
command against the committed fix. In every case one untracked `Sources/ScenicKit/StrayAdversary.swift` is
planted and the honest answer is `SANE FAIL exit=2`.

---

#### ROUTE 1 — `GIT_CONFIG_PARAMETERS` — CLOSED

RED:

    $ GIT_CONFIG_PARAMETERS="'core.excludesFile=C:/…/.artifacts/atk/excludes.txt'" bash ops/sane
    repo      ok     no stray .swift
    crlf      ok     none
    autocrlf  ok     false
    gitattrs  ok     eol=lf
    SANE OK
    EXIT=0                                    <- stray still on disk, `ls -l` in the same transcript

GREEN, identical command:

    repo      FAIL   untracked .swift is IN the build (buildable folders): ?? Sources/ScenicKit/StrayAdversary.swift
    SANE FAIL exit=2
    EXIT=2

The `core.autocrlf=true` form the old fix cited as its own demo: RED `autocrlf FAIL true` / `SANE FAIL
exit=2` for the wrong reason; GREEN `autocrlf ok false`.

NEIGHBOUR SELF-ATTACK (one mechanism over — reach git's config through a name the allowlist KEEPS, not a
`GIT_*` name at all). `HOME` is on `_SCENIC_KEEP`, and git reads `$HOME/.gitconfig`:

    $ HOME=<dir holding a .gitconfig with core.excludesFile> bash ops/sane
    RED:   SANE OK        EXIT=0          <- a route named nowhere in the brief; it works pre-fix
    GREEN: SANE FAIL exit=2  EXIT=2       <- GIT_CONFIG_GLOBAL=/dev/null overrides ~/.gitconfig

Then the forged seal, since `GIT_CONFIG_GLOBAL`, `SCENIC_GIT`, `PATH` and `HOME` are all ON the allowlist
and so cannot make the verification loop object. `env -i` supplies only allowlisted names, and an
interpreter is made reachable so the checks really run:

    $ env -i PATH=<trusted> SCENIC_SEALED=1 SCENIC_HOST_PATH=<py> GIT_CONFIG_GLOBAL=<evil>  bash ops/sane
    $ env -i PATH=<trusted> SCENIC_SEALED=1 SCENIC_HOST_PATH=<py> SCENIC_GIT=<git shim>     bash ops/sane
    $ env -i PATH=<git shim>:<trusted> SCENIC_SEALED=1 SCENIC_HOST_PATH=<py>                bash ops/sane
    $ env -i PATH=<trusted> SCENIC_SEALED=1 SCENIC_HOST_PATH=<py> HOME=<evil home>          bash ops/sane
    all four: SANE FAIL exit=2   EXIT=2      <- every one of those values is re-derived, never read back

`XDG_CONFIG_HOME` was tried the same way, with and without a `~/.gitconfig` present, and did NOT reproduce
on this box (`SANE FAIL exit=2` both times). An earlier draft of the header asserted it did; the claim is
removed rather than repeated, because an unverified claim in that file is worse than no claim.

---

#### ROUTE 2 — `PYTHONPATH` / `sitecustomize.py` — CLOSED

RED:

    $ PYTHONPATH=<dir with a 12-line sitecustomize.py> bash ops/check-pins
    PINS ok=99 skipped=0 pending=0 expired=0 failed=0 tier=linux
    EXIT=0
    $ PYTHONPATH=<same> bash ops/queue-check
    QUEUE OK (999 tasks)
    EXIT=0

Control on the same tree: `PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux`, `QUEUE OK (81
tasks)`. GREEN, identical commands:

    PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux     EXIT=0
    QUEUE OK (81 tasks)                                             EXIT=0

NEIGHBOUR SELF-ATTACK (one name over, a `PYTHON*` name nobody in this task has named). `site` also imports
`usercustomize` from `site.USER_SITE`, and `USER_SITE` is derived from `PYTHONUSERBASE`:

    $ PYTHONUSERBASE=<dir with Python314/site-packages/usercustomize.py> bash ops/check-pins
    RED:   PINS ok=99 skipped=0 pending=0 expired=0 failed=0 tier=linux   EXIT=0
           QUEUE OK (999 tasks)                                           EXIT=0
    GREEN: PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux    EXIT=0
           QUEUE OK (81 tasks)                                            EXIT=0

Neither `GIT` nor `PYTHONPATH` appears in that name. The seal drops it, and `PYTHONNOUSERSITE=1` is in
`_SCENIC_SET` (not optional) because `APPDATA` is forwarded to `SCENIC_TOOLCHAIN=1` scripts and reaches the
same door.

Second neighbour (one entry point over): forge the marker while carrying a name that is NOT allowlisted.

    $ SCENIC_SEALED=1 GIT_CONFIG_PARAMETERS="'core.autocrlf=true'" bash ops/sane
    sane: refusing: variable(s) outside the ops/lib/seal.sh allowlist survived the seal: … GIT_CONFIG_PARAMETERS …
    EXIT=2                                    <- refused, not silently dropped

---

#### ROUTE 3 — `PATH`, a script named `git` — CLOSED

RED:

    $ PATH=<dir with a 15-line script named git>:$PATH bash ops/sane
    (command -v git in the same transcript -> …/.artifacts/atk/bin/git)
    repo      ok     no stray .swift
    SANE OK
    EXIT=0

GREEN, identical command: `SANE FAIL exit=2`, `EXIT=2`.

NEIGHBOUR SELF-ATTACK (one name over — `ops/sane` pipes `git status` through `grep`, and the fix resolves
git absolutely but leaves grep to `PATH`):

    $ PATH=<dir with a shim named grep>:$PATH bash ops/sane
    SANE FAIL exit=2   EXIT=2        <- CLOSED: PATH is rebuilt from trusted dirs, /usr/bin/grep wins

And the same question asked of a pin assertion rather than of the wrapper, since `pins.py` runs assertions
through `bash -c` and the `git()` function is deliberately not exported. With a git shim, a grep shim, an
evil `HOME` and `GIT_CONFIG_PARAMETERS` all set by the caller at once:

    SEALED_PATH=/mingw64/bin:/usr/bin:/bin
    SCENIC_GIT=/mingw64/bin/git
    GIT_CONFIG_GLOBAL=/dev/null
    env-count=18
    assertion sees git at: /mingw64/bin/git
    assertion sees grep at: /usr/bin/grep
    assertion git excludesFile: <none>
    assertion git autocrlf: false
    assertion git status: 1                   <- the assertion still sees the stray

---

#### ROUTE 3b — the interpreter on the caller's `PATH` — **NOT CLOSED**

The neighbour of route 3 that is one *mechanism* over: do not shim `git`, shim the thing that is still
resolved from the caller's `PATH`. There is no python in any trusted directory on this box (measured:
`/usr/local/bin /usr/bin /bin /mingw64/bin` contain no `python`, `python3`, `.exe` or otherwise), so
`scenic_python` searches `SCENIC_HOST_PATH`. A shim that answers the capability probe and then prints the
answer wins, against the FIXED code:

    $ PATH=<dir with a shim named python3>:$PATH bash ops/queue-check
    queue-check: interpreter /c/…/.artifacts/atk/bin2/python3 (3.12.7, via PATH) - caller-supplied, not authenticated
    QUEUE OK (999 tasks)
    EXIT=0

    $ env -i PATH=/usr/bin:/mingw64/bin SCENIC_SEALED=1 SCENIC_HOST_PATH=<that dir> /usr/bin/bash ops/queue-check
    QUEUE OK (999 tasks)
    EXIT=0

**This route is reported closed=false with the surviving commands above.** It is the position part 3 of
`boot.sh` already states and the brief tells this task not to re-litigate: aiming the interpreter is exactly
what `PYTHON=` does, and a probe cannot tell a shim from a python because it asks the thing under test to
describe itself (T-0072). What the seal does remove is INJECTION into a legitimate interpreter — PYTHONPATH,
PYTHONSTARTUP, PYTHONUSERBASE and APPDATA/usercustomize are all gone. What was added is transparency, not a
boundary: `scenic_python` now prints the absolute path it ACTUALLY EXECUTED — not the `sys.executable` the
probe reported, because a shim writes the second and cannot write the first — whenever that path is outside
the trusted directories or came from `PYTHON=`. Trusted-dir python (Linux CI) stays quiet. The false green
above is now attributable in the transcript instead of silent. Written into `seal.sh` as open route (b).

---

#### ROUTE 4 — the entry shell — CLOSED for functions, **NOT CLOSED** for `SHELLOPTS`

Not in the brief; found while attacking the fix. An exported function needs no source edit:

    $ env "BASH_FUNC_git%%=() { …filters the evidence… }" bash ops/sane
    RED:   SANE OK exit=0        GREEN: sane: refusing: the calling shell is not clean … EXIT=2
    $ env BASH_ENV=<file defining git()> bash ops/sane
    GREEN: sane: refusing: the calling shell is not clean … EXIT=2

NEIGHBOUR SELF-ATTACK, and it BEAT the first draft of this fix. That draft's part 0 tests `declare -F`, and
`declare` can ITSELF be an exported function (measured: `env "BASH_FUNC_declare%%=() { :; }" bash -c 'echo
$(type -t declare)'` prints `function`). Blind part 0, then let `cd` lie about the wrapper's own directory —
honest for anything under `ops/lib`, so `SCENIC_ROOT` still validates — and the seal re-execs the
adversary's script:

    $ env "BASH_FUNC_declare%%=() { :; }" "BASH_FUNC_cd%%=<lies outside ops/lib>" bash ops/sane
    repo      ok     no stray .swift
    SANE OK
    EXIT=0                                    <- against the FIRST DRAFT of this fix

A `$0` re-check in the sealed pass does NOT catch this: the adversary's script never sources `boot.sh`, so
no check inside it ever runs. The re-exec target is therefore validated in the UNSEALED pass, against
`SCENIC_ROOT`, using ONLY shell keywords and parameter expansion — there is no command on those two lines to
shadow. After that change, the identical command:

    sane: refusing: the re-exec target resolved to
        /c/…/.artifacts/atk/evil/sane
      which is not /c/…/wt/T-0086/ops/sane. …
    EXIT=2

Its own neighbour (lie about `basename` instead of `cd`, re-aiming `bash ops/sane` at a DIFFERENT REAL
wrapper — `ops/queue-check` prints `QUEUE OK` and exits 0, a false green needing no adversary-written file
at all) is why the basename is compared too:

    $ env "BASH_FUNC_declare%%=…" "BASH_FUNC_basename%%=<returns queue-check>" bash ops/sane
    sane: refusing: the re-exec target resolved to /c/…/ops/queue-check, which is not /c/…/ops/sane.
    EXIT=2

The sealed pass keeps its own `$0` check, which is what refuses an out-of-tree script that sources `boot.sh`
directly: `bash .artifacts/atk/probe` -> `probe: refusing: … is not an ops/* script of …`, EXIT=2.

**Still open, and unreachable from inside a bash script at all** — bash imports `SHELLOPTS` at startup,
before line 1 of anything:

    $ env SHELLOPTS=noexec bash ops/sane
    EXIT=0                                    <- no output whatsoever, stray on disk, RED and GREEN alike

Nothing in `boot.sh` or `seal.sh` executes, so nothing in them can object. **Reported closed=false with the
surviving command.** The decision is written into `seal.sh` (c): every `ops/*` wrapper prints at least one
line on every run, so a caller that gets EMPTY output and exit 0 has been lied to and must treat it as a
failure. That is a property of the caller, not of these files.

---

#### GATES — last lines, verbatim

    $ bash ops/queue-check
    QUEUE OK (81 tasks)                                                        EXIT=0
    $ bash ops/check-pins
    PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux                EXIT=0
    $ bash ops/check-pins --source-only
    PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only    EXIT=0
    $ PYTHON=$(command -v python) bash ops/test          (after `npm ci` in services/api)
    TESTS linux=50/50 ios=skipped failed=0 skipped=0
    OK                                                                         EXIT=0
    $ bash ops/lib/check-exec-bits
    P-OPS-01: 25 files, 15 required present, all modes correct

Identical to the pre-fix control on the same tree. Nothing was weakened to make anything pass.

#### OTHER FINDINGS, not fixed here (outside `touches:`)

1. `ops/lib/check-exec-bits` and `ops/lib/check-line-cap` — the two pin assertion helpers — both still open
   with `cd "$(git rev-parse --show-toplevel)"`. That is the exact T-0077 shape in the scripts that police
   T-0077's own file modes and the 300-line cap. They do not source `boot.sh`. In practice the seal now
   contains them (`pins.py` runs assertions with cwd = `SCENIC_ROOT`, and `GIT_DIR`/`GIT_WORK_TREE` no
   longer survive to aim them), so this is latent rather than live — but it is the same defect and should
   be its own task.
2. `ops/lib/check-line-cap` only enforces the 300-line cap on tracked `.swift` files under `Sources/` and
   `Tests/`. `CLAUDE.md` states the cap for the repo. Nothing mechanical would have caught `boot.sh` at
   329 lines; it was split because the rule says to split, not because a check complained.
3. The brief said `CLAUDE.md` carries an NTFS section with eight rules. It does not — `CLAUDE.md` is 51
   lines with no such section, and there is exactly one `CLAUDE.md` in the tree. The Windows rules were
   followed from the task prompt instead. Worth correcting wherever that instruction is generated.
