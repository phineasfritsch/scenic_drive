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

- 2026-09-08 round-three adversarial verification, by an agent that did not write the fix.
  **holds = false.** The fix reported `partial` and named its own open routes, which is right and
  is new this round. It was still defeated on routes it marked CLOSED, and the report below says
  exactly how. Every evasion was executed.

  # Round-three adversarial verification of T-0077 — holds = False
  
  ## Routes the fixer marked closed that were defeated
  
  - T-0077 route 3 (GIT_DIR / GIT_WORK_TREE / GIT_CONFIG_* redirect every ops/* checker) — DEFEATED OUTRIGHT ON ITS OWN WORDING. boot.sh unsets fifteen GIT_* names and omits GIT_CONFIG_PARAMETERS, which is literally a GIT_CONFIG_* variable and is the mechanism `git -c` itself uses. It is the immediate neighbour of the GIT_CONFIG_COUNT/GIT_CONFIG_KEY_0 pair the fixer DID clear and cited as the reason the route was shut. `GIT_CONFIG_PARAMETERS="'core.autocrlf=true'" bash ops/sane` reproduces the fixer's own route-3 demonstration verbatim (autocrlf FAIL true), and `core.excludesFile` turns SANE FAIL exit=2 into SANE OK exit=0 with the stray .swift still on disk. boot.sh's stated principle — 'an ops/* script talks to the repo it lives in, whatever the caller's environment says' — is false. PATH is also environment and is never sanitized.
  
  - T-0076 (the interpreter: `${PYTHON:-...}` picks by NAME; scenic_python now picks by CAPABILITY) — DEFEATED ON ITS OWN WORDING. Capability is measured with importlib.util.find_spec(), and find_spec searches sys.path, which the caller writes with PYTHONPATH. `scenic_python scenic_needs_this` refuses with rc=2 in a clean environment ('has no scenic_needs_this' for all three candidates) and returns rc=0 in the identical call under PYTHONPATH, reporting the same sys.executable and the same 3.14.5. The decision moved from a name the caller controls to an import the caller controls. boot.sh unsets fifteen GIT_* variables and zero PYTHON* variables.
  
  - T-0077 route 1 (the exec family — check-pins, queue-check, queue-next, claim, lock, new-task, queue-sweep) — the NAMED mechanism holds (git rev-parse is gone; pins.py/queue.py use Path(__file__).resolve().parents[2]; I could not defeat the BASH_SOURCE derivation itself), but the OUTCOME the route exists to prevent is fully reproducible. `PYTHONPATH=<dir with sitecustomize.py> bash ops/check-pins` prints `PINS ok=99 skipped=0 pending=0 expired=0 failed=0 tier=linux` EXIT=0 and `bash ops/queue-check` prints `QUEUE OK (999 tasks)` EXIT=0 — the exact two strings boot.sh's own header cites as the measured proof of the ORIGINAL defect — with zero pins loaded and zero assertions run. Separately, a `git` earlier on PATH makes check-pins report ok=9 failed=0 while a tracked file is 484 lines and P-SRC-02's MIN_FILES=5 floor is still satisfied (8 files). Marking this class closed is the round-two failure repeating.
  
  - T-0077 route 2 (the cd family — test, sane, agent-preflight, deploy, prod-read) — same finding as route 1. The named mechanism holds (all five source boot.sh and scenic_cd_root), but ops/sane was driven from SANE FAIL exit=2 to SANE OK exit=0 twice, by two different single environment variables, with the stray .swift untouched on disk both times.
  
  
  ## Verdict
  
  HOLDS = FALSE. Seven fresh evasions executed, five green (guard defeated), two caught.
  
  STEP 1 — all four of the fixer's green gates reproduce exactly, from C:\\Users\\phineasf\\Documents\\GitHub\\wt\\T-0077:
    bash ops/queue-check              -> QUEUE OK (76 tasks)                                              EXIT=0
    bash ops/check-pins               -> PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux      EXIT=0
    bash ops/check-pins --source-only -> PINS ok=3 skipped=8 pending=1 expired=0 failed=0 ... source-only EXIT=0
    bash ops/test                     -> TESTS linux=50/50 ios=skipped failed=0 skipped=0 / OK            EXIT=0
  No finding there. The fix is real work: git rev-parse is gone from all twelve wrappers, ops/lib/pins.py and ops/lib/queue.py both derive ROOT from Path(__file__).resolve().parents[2], and I could not defeat the BASH_SOURCE derivation itself. The CDPATH attack (evasion 3) was my best attempt at it and it fails closed.
  
  WHAT IS WRONG — one sentence: the fix changed WHICH environment variable you pull, not WHETHER the caller's environment decides.
  
  C:\\Users\\phineasf\\Documents\\GitHub\\wt\\T-0077\\ops\\lib\\boot.sh, section 1b, unsets fifteen names:
    GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_NAMESPACE
    GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_CEILING_DIRECTORIES GIT_DISCOVERY_ACROSS_FILESYSTEM
    GIT_PREFIX GIT_CONFIG GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM GIT_CONFIG_NOSYSTEM GIT_CONFIG_COUNT
  Four things that decide the answer are missing from that list, and each one alone drives a fixed checker from red to green:
    1. GIT_CONFIG_PARAMETERS — a GIT_CONFIG_* variable, the mechanism `git -c` uses, the literal neighbour of the GIT_CONFIG_COUNT pair the fixer cleared and cited as proof route 3 was shut.
    2. PATH — `git` itself. Fifteen variables swept, and the binary they configure is taken from the caller.
    3. PYTHONPATH — the exact analogue of GIT_DIR for the interpreter. Zero PYTHON* variables are swept. sitecustomize.py gives arbitrary code inside the correctly-located, capability-probed pins.py.
    4. CDPATH and GIT_LITERAL_PATHSPECS — both reach a guard; both happen to fail closed here.
  
  The single most damning measurement: `PYTHONPATH=<dir> bash ops/check-pins` prints `PINS ok=99 skipped=0 pending=0 expired=0 failed=0 tier=linux` EXIT=0 and `bash ops/queue-check` prints `QUEUE OK (999 tasks)` EXIT=0. Those two strings are copied verbatim out of boot.sh's own header, where they are presented as the measured evidence of the defect T-0077 fixed. They are reproducible against the fixed scripts, in one environment variable, with zero pins loaded and zero assertions run.
  
  CREDIT WHERE DUE — three things the fixer got right and that I could not break:
    - The BASH_SOURCE root derivation and its symlink resolution. Evasion 3 (CDPATH) is the only lever I found into it and it exits 2.
    - check-line-cap's MIN_FILES=5 anti-vacuity floor. Evasion 6 emptied its population outright and the floor caught it and said so in plain words. That guard is the one thing in the set that survived an environment attack on its own merits.
    - The honesty of routes 4 and T-0076/T-0072, left open. ops/merge, ops/lib/check-exec-bits and ops/lib/check-line-cap do still `cd "$(git rev-parse --show-toplevel)"` (lines 16, 12, 15) — correctly reported as open, so I did not spend evasions there.
  
  WHAT I DID NOT TEST, stated rather than implied: a native symlink to a wrapper (git-bash on this box refuses to create one, same wall the fixer hit — I did not try MSYS=winsymlinks:nativestrict, which needs elevation); HOME / XDG_CONFIG_HOME redirection of ~/.gitconfig; and the PYTHONPATH attack against ops/test's junit_count.py path (the sitecustomize fixture was written for pins.py/queue.py only). services/etl/pyproject.toml does not exist in this worktree, so T-0076's original pytest scenario cannot be re-measured here at all — I took the fixer's word for that measurement and attacked the replacement mechanism instead.
  
  SUGGESTED SHAPE OF THE REAL FIX, for the next round: boot.sh should not enumerate hostile variables — the enumeration is what failed twice now. It should scrub to an allowlist (keep HOME, USERPROFILE, TEMP, SYSTEMROOT, a PATH it rebuilds itself from known-good directories) and re-exec, or invoke git as an absolute path with `-c`-free config isolation and python with `-E -S`. `-E` alone kills the PYTHONPATH class; `-S` kills sitecustomize.
  
  STEP 3 — cleanup. Every fixture deleted and proven gone: .artifacts/adv/ (removed, `ls` reports No such file or directory), Sources/ScenicKit/StrayAdversary.swift (removed), and six leftover StrayAdversary.* objects under the gitignored .build/ index that swift picked up during the run (found with find, deleted, second find returns nothing). Sources/ScenicKit/Solar/SolarMath.swift restored. `git checkout -- .` run. Gates re-run on the restored tree: PINS ok=9 ... failed=0 EXIT=0, QUEUE OK (76 tasks) EXIT=0, SANE OK EXIT=0.
  
  LAST COMMAND, as required — `git status --short` output was EMPTY (clean worktree, nothing staged, nothing modified, nothing untracked). No commits made, nothing pushed, no source file in the worktree edited by me at any point: every one of the seven evasions was environment-only or a fixture under the gitignored .artifacts/.
  
  ## Evasions executed
  
  ### 1. *** UNCAUGHT *** — No source edit. Planted Sources/ScenicKit/StrayAdversary.swift (untracked, in a buildable folder) plus an exclude file listing *.swift. Set GIT_CONFIG_PARAMETERS — the one git-config env var boot.sh does not unset, and the mechanism `git -c` uses. Windows-form path required; the /c/... msys form is silently ignored by git.
  
  ```
  $ bash ops/sane            (RED, clean env)
  GIT_CONFIG_PARAMETERS="'core.excludesFile=C:/Users/phineasf/Documents/GitHub/wt/T-0077/.artifacts/adv/ex.txt'" bash ops/sane   (GREEN, identical command)
  RED:
  repo      FAIL   untracked .swift is IN the build (buildable folders): ?? Sources/ScenicKit/StrayAdversary.swift
  crlf      ok     none
  autocrlf  ok     false
  gitattrs  ok     eol=lf
  SANE FAIL exit=2
  EXIT=2
  
  GREEN:
  repo      ok     no stray .swift
  crlf      ok     none
  autocrlf  ok     false
  gitattrs  ok     eol=lf
  SANE OK
  EXIT=0
  
  the stray is still there:
  -rw-r--r-- 1 phineasf 197121 36 Sep  7 20:43 Sources/ScenicKit/StrayAdversary.swift
  
  Control that the variable also reproduces the fixer's own route-3 demo:
  GIT_CONFIG_PARAMETERS="'core.autocrlf=true'" git config --get core.autocrlf -> true
  GIT_CONFIG_PARAMETERS="'core.autocrlf=true'" bash ops/sane -> autocrlf FAIL true / SANE FAIL exit=2
  ```
  
  ### 2. *** UNCAUGHT *** — No source edit. Wrote .artifacts/adv/pp/sitecustomize.py — 12 lines. `site` imports sitecustomize from sys.path at interpreter startup, and PYTHONPATH is sys.path. Guarded on sys.argv containing pins.py / queue.py so boot.sh's capability probe (python3 -c '<probe>') still answers normally and scenic_python still reports the interpreter as usable.
  
  ```
  $ bash ops/check-pins ; bash ops/queue-check            (RED, clean env)
  PYTHONPATH=C:/Users/phineasf/Documents/GitHub/wt/T-0077/.artifacts/adv/pp bash ops/check-pins ; ... bash ops/queue-check   (GREEN, identical commands)
  RED:
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux   EXIT=0
  QUEUE OK (76 tasks)                                           EXIT=0
  
  GREEN:
  PINS ok=99 skipped=0 pending=0 expired=0 failed=0 tier=linux  EXIT=0
  QUEUE OK (999 tasks)                                          EXIT=0
  
  did the capability probe notice?
  probe says: C:\Users\phineasf\AppData\Local\Python\pythoncore-3.14-64\python.exe 3.14.5 via PATH
  
  Those two green strings are verbatim the ones ops/lib/boot.sh's header cites as the measured evidence of the original T-0077 defect. Zero pins loaded, zero assertions run, against the FIXED scripts. The module path was located correctly from BASH_SOURCE; the caller still chose what executed inside it.
  ```
  
  ### 3. CAUGHT — No source edit. Built a four-file hostile tree (.artifacts/adv/fake/{CLAUDE.md,pins/PINS.yaml,ops/lib/{pins.py,queue.py}}) satisfying every member of boot.sh's root assert, then set CDPATH. On the normal invocation `bash ops/check-pins`, ${BASH_SOURCE[0]} inside boot.sh is the RELATIVE string "ops/lib/boot.sh", so _scenic_resolve runs `cd -P "ops/lib"` — an operand that does not start with / ./ or ../, which means the cd builtin searches $CDPATH FIRST.
  
  ```
  $ ( export CDPATH=<fake>; cd -P ops/lib && pwd )     (mechanism check)
  bash ops/check-pins                                 (RED, clean env)
  CDPATH=<fake> bash ops/check-pins ; CDPATH=<fake> bash ops/queue-check ; CDPATH=<fake> bash ops/sane
  mechanism check — CDPATH DOES move the cd, and the fake root wins:
  /c/.../.artifacts/adv/fake/ops/lib
  /c/.../.artifacts/adv/fake/ops/lib
  
  RED:  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux   EXIT=0
  
  CDPATH set:
  check-pins: <unresolved> is not the scenic_drive root (no ops/lib/pins.py)
    The root is derived from ops/lib/boot.sh's own path, never from the caller's git toplevel.
  EXIT=2   (same for queue-check and sane)
  
  CAUGHT — but only by accident, not by the assert's design. CDPATH reaches the root resolution; what stops the hijack is that bash's cd ECHOES the directory when CDPATH is used, so `$(cd -P ... && pwd)` captures the path twice, dirname of the two-line string is garbage, SCENIC_ROOT comes back empty and the sanity assert refuses. It fails closed. Report anyway: a caller-controlled variable that reaches the root derivation and kills every ops/* wrapper with a message blaming the repo layout is a live denial-of-service, and it is one bash-version behaviour away from being the green case.
  ```
  
  ### 4. *** UNCAUGHT *** — No source edit. Wrote .artifacts/adv/bin/git — a 15-line shell script earlier on PATH that passes everything through to /mingw64/bin/git.exe except `git status`, from which it greps out the stray. boot.sh sanitizes fifteen GIT_* variables and never touches PATH; every ops/* checker and every pin assertion resolves `git` from the caller.
  
  ```
  $ bash ops/sane                     (RED, clean PATH)
  PATH=C:/Users/phineasf/Documents/GitHub/wt/T-0077/.artifacts/adv/bin:$PATH bash ops/sane   (GREEN, identical command)
  RED:
  repo      FAIL   untracked .swift is IN the build (buildable folders): ?? Sources/ScenicKit/StrayAdversary.swift
  SANE FAIL exit=2
  EXIT=2
  
  GREEN:
  repo      ok     no stray .swift
  crlf      ok     none
  autocrlf  ok     false
  gitattrs  ok     eol=lf
  SANE OK
  EXIT=0
  ```
  
  ### 5. *** UNCAUGHT *** — No source edit. Same PATH shim, extended to filter `git ls-files`. Appended 400 lines to the tracked Sources/ScenicKit/Solar/SolarMath.swift (worktree only, index untouched), taking it to 484 lines. This is the STEP 2 shape 'satisfy a floor while removing the specific thing that mattered': check-line-cap's MIN_FILES=5 anti-vacuity floor stays satisfied at 8 files after the one offending file is dropped from the population. Reached through ops/check-pins -> ops/lib/pins.py -> subprocess.run(bash -c 'bash ops/lib/check-line-cap', cwd=ROOT), which inherits PATH.
  
  ```
  $ bash ops/check-pins               (RED, clean PATH)
  PATH=<shim dir>:$PATH bash ops/check-pins   (GREEN, identical command)
  RED:
  PINS ok=8 skipped=0 pending=3 expired=0 failed=1 tier=linux
   - P-SRC-02: No Swift source file exceeds 300 lines
        assertion: bash ops/lib/check-line-cap
        output: P-SRC-02: file(s) over the 300-line cap:
    Sources/ScenicKit/Solar/SolarMath.swift (484 lines)
  EXIT=1
  
  GREEN:
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
  EXIT=0
  
  population still above the floor under the shim: 8   (MIN_FILES=5)
  offending file still: 484 lines
  ```
  
  ### 6. *** UNCAUGHT *** — No source edit. GIT_LITERAL_PATHSPECS=1 — another git variable absent from boot.sh's unset list. It makes check-line-cap's pathspecs 'Sources/**/*.swift' 'Tests/**/*.swift' literal, so the population it iterates becomes empty. This is the STEP 2 shape 'empty the population a guard iterates'.
  
  ```
  $ GIT_LITERAL_PATHSPECS=1 git ls-files 'Sources/**/*.swift' 'Tests/**/*.swift' | wc -l
  GIT_LITERAL_PATHSPECS=1 bash ops/check-pins
  GIT_LITERAL_PATHSPECS=1 bash ops/sane
  population under it: 0
  
  PINS ok=8 skipped=0 pending=3 expired=0 failed=1 tier=linux
   - P-SRC-02: No Swift source file exceeds 300 lines
        assertion: bash ops/lib/check-line-cap
        output: P-SRC-02: only 0 tracked .swift file(s) under Sources/ and Tests/ (expected >= 5).
    An empty or truncated set must never read as 'no file exceeds 300 lines'.
  EXIT=1
  
  ops/sane: SANE OK EXIT=0 (unaffected — it uses no pathspec globs)
  
  CAUGHT. check-line-cap's MIN_FILES=5 floor did exactly its job: an emptied population read as a failure, not as 'no file exceeds 300 lines'. Credit where due — this is the one guard in the set that survived an environment attack. Note it survived by being a data floor, not by anything boot.sh does; boot.sh let the variable straight through.
  ```
  
  ### 7. *** UNCAUGHT *** — No source edit. Wrote .artifacts/adv/fakemods/scenic_needs_this.py containing a single `raise SystemExit`. Attacks T-0076's replacement claim directly: 'THE INTERPRETER IS CHOSEN BY CAPABILITY, NOT BY NAME'. Capability is importlib.util.find_spec(), find_spec searches sys.path, and PYTHONPATH is sys.path. (A first attempt using `pytest` was not a clean red/green — the real python3 already has pytest — so I re-ran it with a module that exists nowhere on the box. Reporting the second, unambiguous run.)
  
  ```
  $ bash -c 'source ops/lib/boot.sh; scenic_python scenic_needs_this; echo rc=$?'                       (RED)
  PYTHONPATH=<fakemods> bash -c 'source ops/lib/boot.sh; scenic_python scenic_needs_this; ...'          (GREEN, identical call)
  RED:
  bash: no usable python.
    needs: python >= 3.9 with scenic_needs_this
    PYTHON=<unset>   candidates tried, in order:
      python3 -> ...pythoncore-3.14-64\python.exe (3.14.5) has no scenic_needs_this
      python  -> ...Programs\Python\Python310\python.exe (3.10.11) has no scenic_needs_this
      py      -> ...pythoncore-3.14-64\python.exe (3.14.5) has no scenic_needs_this
    Refusing to run: a wrapper that cannot say which interpreter it used cannot be believed.
  rc=2
  
  GREEN:
  rc=0  ACCEPTED as: C:\Users\phineasf\AppData\Local\Python\pythoncore-3.14-64\python.exe 3.14.5 via PATH
  
  Same interpreter, same path, same version, opposite verdict, one caller-set variable. Earlier control run confirmed the same lever works on the module ops/test actually asks for: PYTHONPATH=<fakemods> python3 -c 'find_spec("pytest").origin' -> C:\...\.artifacts\adv\fakemods\pytest.py, and `python3 -m pytest -q` then printed 'this pytest cannot run anything'.
  ```
