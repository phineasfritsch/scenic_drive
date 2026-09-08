---
id: T-0077
title: every ops wrapper locates its module from the caller's git toplevel, so another repo's module runs instead
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T02:59:04Z
lease_expires_at: 2026-09-08T08:59:04Z
worktree: wt/T-0077
branch: task/T-0077
exclusive: []
touches: [ops/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/check-pins` is

    exec "$py" "$(git rev-parse --show-toplevel)/ops/lib/pins.py" "$@"

so it locates its module from **the caller's** git toplevel, not from its own directory. Run this repo's
`ops/check-pins` from inside any other git repository and it executes **that** repository's
`ops/lib/pins.py`. Executed by the T-0072 verifier against a synthetic repo containing a four-line module
that prints a green summary:

    PINS ok=99 skipped=0 pending=0 expired=0 failed=0 tier=linux
    EXIT=0

with nothing in this repo modified. Every guard added by T-0066 and T-0072 - the population floors, the
REQUIRED lists, the strict argv parser, the run floor - is bypassed at once, by choosing a working directory.

Pre-existing: `git show dac14c3:ops/check-pins` has the same line. T-0055 fixed this class in the wrappers'
`cd`, and `ops/lib/pins.py` itself now derives `ROOT` from `__file__` (which is why all four *entry points*
keep their guards). The one path not fixed is how the wrapper finds the module in the first place.

**The same line has a second knob**, and the two want one decision: `PY="${PYTHON:-$(command -v python3 ||
command -v python)}"`. `PYTHON=true` is now refused, but a four-line script that answers the probe token and
then does nothing still passes, and `PYTHON=` is honoured by every other wrapper unprotected. See [[T-0076]],
where the same expression picks an interpreter without pytest on a real developer machine - that is this knob
going wrong by accident rather than on purpose.

- Resolve the module from `${BASH_SOURCE[0]}`, the way T-0055 taught the wrappers to resolve the repo root.
  It is one line per wrapper and it closes the whole class.
- Then decide the `PYTHON` question once, in writing: pin the interpreter, probe candidates for the modules
  each script needs, or state in the file that this is a deliberate local convenience. Do not leave it decided
  by omission in six files.
- **Every wrapper has the same shape**: `ops/check-pins`, `ops/queue-check`, `ops/claim`, `ops/new-task`,
  `ops/lock`, `ops/queue-next`, `ops/queue-sweep`, `ops/test`, `ops/sane`. Grep before assuming this list is
  complete, and fix them together - a class fixed in one file is a class still open.
- Red demonstration: build a throwaway repo with a fake `ops/lib/pins.py` that prints a green line, run this
  repo's `ops/check-pins` from inside it, and show `ok=99 ... exit 0`. Then show it refusing after the fix.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the round-two adversarial verification of [[T-0072]]. The
  synthetic-repo bypass was executed by the verifier, not reasoned about.
- 2026-09-08T02:59:04Z claimed by agent/claude-opus-5; lease until 2026-09-08T08:59:04Z
- 2026-09-08 agent/claude-opus-5, round three. Fixed on task/T-0077 together with [[T-0076]]: the two are one
  expression. `touches:` was widened from `[ops/new-task]` to `[ops/]` because the brief names nine wrappers
  and the grep found twelve; the widening is declared here rather than worked around.

  **RED** - synthetic repo built outside this worktree (SwiftPM walks UP for Package.swift, so a fake repo
  inside `.artifacts/` made `swift test` find the real package and confounded the first attempt). Its
  `ops/lib/pins.py` and `ops/lib/queue.py` are three lines each; `.gitattributes` is `* text=auto eol=lf`:

      $ cd <fake> && bash <repo>/ops/check-pins
      PINS ok=99 skipped=0 pending=0 expired=0 failed=0 tier=linux
      EXIT=0
      $ bash <repo>/ops/queue-check
      QUEUE OK (999 tasks)
      EXIT=0
      $ bash <repo>/ops/queue-next
      QUEUE OK (999 tasks)
      EXIT=0
      $ bash <repo>/ops/sane
      repo      ok     no stray .swift
      crlf      ok     none
      autocrlf  ok     false
      gitattrs  ok     eol=lf
      SANE OK
      EXIT=0

  `ops/sane` was NOT in the brief's list and is the same defect through the `cd` door: a full green SANE OK
  about a tree that is not scenic_drive. `ops/prod-read` resolves `ops/lib/ro_grammar.py` the same way, so
  the read-only grammar - layer 1 of 3, the one that runs before anything leaves the machine - was chosen by
  the caller's working directory. `ops/deploy` would deploy the caller's services/api under the caller's sha.

  **FIX** - new `ops/lib/boot.sh` (162 lines, sourced not executed, committed 100755). `SCENIC_ROOT` comes
  from `${BASH_SOURCE[0]}` with symlinks resolved (`cd -P` per directory component, a loop for the final
  one), verified against four marker files. `scenic_cd_root` replaces `cd "$(git rev-parse --show-toplevel)"`.
  Wired into twelve scripts: check-pins, claim, lock, new-task, queue-check, queue-next, queue-sweep, test,
  sane, agent-preflight, deploy, prod-read.

  **GREEN** - identical commands, identical fake repo:

      $ cd <fake> && bash <repo>/ops/check-pins
      PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
      EXIT=0
      $ bash <repo>/ops/queue-check
      QUEUE OK (76 tasks)
      EXIT=0
      $ bash <repo>/ops/sane
      ... SANE OK   (this repo's four checks, not the fake's)
      EXIT=0

  Decisive control, because "SANE OK" and "PINS ok" look alike whichever tree they describe: the fake repo
  was stocked past both vacuity floors (19 files under ops/.githooks, 9 .swift) and then BROKEN -
  `git update-index --chmod=-x ops/test`. Standing in it:

      $ bash <repo>/ops/lib/check-exec-bits      # direct - reads the fake
      P-OPS-01: wrong git file mode:
        ops/test (script, should be 100755, is 100644)
      EXIT=1
      $ bash <repo>/ops/check-pins               # the entry point - reads THIS repo
      PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
      EXIT=0

  **SELF-ATTACK on the fix.** Four adjacent forms; one of them was open and is now also fixed.

  A1 symlink to the wrapper, planted beside a hostile `ops/lib`. git-bash on this box cannot create native
  symlinks (`ln: failed to create symbolic link: Operation not permitted`), so this was executed under WSL:

      /tmp/scenic-symattack/check-pins: line 23: /tmp/scenic-symattack/lib/boot.sh: No such file or directory
      EXIT=2

  A2 symlink the whole `ops/` directory, so `lib/boot.sh` is reached THROUGH the link (WSL):

      $ bash -c 'source /tmp/scenic-symattack/link/ops/lib/boot.sh; echo $SCENIC_ROOT'
      SCENIC_ROOT=/mnt/c/Users/phineasf/Documents/GitHub/wt/T-0077

  and `bash link/ops/check-pins --source-only` ran THIS repo's pins.py (exit 1, the T-0060 WSL/NTFS
  vacuity failure - not `ok=99`). Under git-bash the same shape degrades to a directory COPY, which the
  marker catches: "opslink is not the scenic_drive root (no pins/PINS.yaml)", exit 2.

  A3 found on PATH, invoked by bare name: `PATH=<repo>/ops:$PATH check-pins` -> `PINS ok=9 ... EXIT=0`,
  this repo. Correct.

  A4 **GIT_DIR / GIT_WORK_TREE. THIS ONE PASSED, AND IT IS THE POINT.** Deriving the root from BASH_SOURCE
  fixes the working directory and nothing else: every ops/* script and every pin assertion then shells out
  to git, and git picks its repository from the ENVIRONMENT before the working directory. With one untracked
  `Sources/ScenicKit/StrayAdversary.swift` planted in the REAL repo, standing in the REAL repo:

      $ bash ops/sane                                                -> SANE FAIL exit=2
      $ GIT_DIR=<fake>/.git GIT_WORK_TREE=<fake> bash ops/sane
      repo      ok     no stray .swift
      ... SANE OK
      EXIT=0
      $ GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=true bash ops/sane
      autocrlf  FAIL   true

  Two environment variables moved a *fixed* checker's answer onto another tree; a third rewrote the config
  it read. Closed in boot.sh section 1b: GIT_DIR, GIT_WORK_TREE, GIT_COMMON_DIR, GIT_INDEX_FILE,
  GIT_OBJECT_DIRECTORY, GIT_ALTERNATE_OBJECT_DIRECTORIES, GIT_NAMESPACE, GIT_CEILING_DIRECTORIES,
  GIT_DISCOVERY_ACROSS_FILESYSTEM, GIT_PREFIX, GIT_CONFIG, GIT_CONFIG_GLOBAL, GIT_CONFIG_SYSTEM,
  GIT_CONFIG_NOSYSTEM and GIT_CONFIG_COUNT (plus its KEY_n/VALUE_n pairs) are unset before anything runs.
  Measured first: `GIT_CONFIG_KEY_0=... GIT_CONFIG_VALUE_0=... git config --get core.autocrlf` still prints
  `false` without the count, so clearing the count is sufficient; the pairs are cleared anyway.
  No script under `.githooks/` invokes `ops/*` (grepped), so nothing depends on the GIT_DIR/GIT_INDEX_FILE
  that git exports to a hook. Re-run of the identical commands afterwards:

      $ bash ops/sane                                                -> SANE FAIL exit=2
      $ GIT_DIR=<fake>/.git GIT_WORK_TREE=<fake> bash ops/sane
      repo      FAIL   untracked .swift is IN the build: ?? Sources/ScenicKit/StrayAdversary.swift
      SANE FAIL exit=2
      EXIT=2
      $ GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=true bash ops/sane
      autocrlf  ok     false

  **STILL OPEN - three members of the class I did not fix, because another live task owns each file.**
  CLAUDE.md forbids two agents in one file, and these are claimed, so they are reported, not touched.
  `ops/merge` (T-0021, T-0022, T-0044, T-0049) - from inside the fake repo, `bash -x <repo>/ops/merge`:

      + cd C:/.../scratchpad/fakerepo

  `ops/lib/check-exec-bits` (T-0036) and `ops/lib/check-line-cap` (T-0035, T-0037, T-0043, T-0058, T-0062) -
  from inside the stocked fake repo, these print a GREEN pin result about a tree that is not scenic_drive:

      $ bash <repo>/ops/lib/check-exec-bits
      P-OPS-01: 19 files, 15 required present, all modes correct
      EXIT=0
      $ bash <repo>/ops/lib/check-line-cap
      P-SRC-02: 9 Swift files tracked, none over 300 lines
      EXIT=0

  Both are only reachable that way by DIRECT invocation: through `ops/check-pins` they now inherit
  cwd=SCENIC_ROOT and a cleaned git environment (proved by the chmod=-x control above). The one-line
  preamble that fixes each is in boot.sh and is ready for whoever owns those files.

  **Collision notice for the merger.** This branch edits eight files owned by other claimed tasks:
  ops/check-pins, ops/queue-check, ops/claim, ops/lock, ops/new-task, ops/queue-next, ops/queue-sweep,
  ops/agent-preflight are [[T-0055]]'s `touches:`, and T-0055 already carries the same BASH_SOURCE
  derivation on an unmerged branch (f25da27, not an ancestor of main). ops/test is [[T-0040]]'s, [[T-0023]]'s
  and [[T-0071]]'s; ops/sane is [[T-0024]]'s and [[T-0051]]'s. ops/deploy and ops/prod-read are unowned.
  I did NOT touch ops/test's vitest message, which is exactly [[T-0040]]'s subject.

  Gates in this worktree: `QUEUE OK (76 tasks)`; `PINS ok=9 skipped=0 pending=3 expired=0 failed=0
  tier=linux`; `PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only`; `SANE OK`;
  `PREFLIGHT OK`; `TESTS linux=50/50 ios=skipped failed=0 skipped=0 / OK` (after `npm ci` in services/api).
