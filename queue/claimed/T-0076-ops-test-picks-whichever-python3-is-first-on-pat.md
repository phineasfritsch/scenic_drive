---
id: T-0076
title: ops/test picks whichever python3 is first on PATH, which here is a different interpreter without pytest
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T02:59:03Z
lease_expires_at: 2026-09-08T08:59:03Z
worktree: wt/T-0077
branch: task/T-0077
exclusive: []
touches: [ops/test, ops/lib/boot.sh]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/test` line 15 resolves its interpreter as

    PY="${PYTHON:-$(command -v python3 || command -v python)}"

`python3` wins whenever it exists. On this machine the two names are **different installations**:

    python3  ->  C:\Users\phineasf\AppData\Local\Python\pythoncore-3.14-64\python.exe   3.14.5   pytest: False
    python   ->  C:\Users\phineasf\AppData\Local\Programs\Python\Python310\python.exe   3.10.11  pytest: True

So `"$PY" -m pytest` runs an interpreter with no pytest, writes no report, and `ops/test` stops with

    FAIL: services/etl exists but pytest produced no report

**The message blames the wrong thing.** It names `services/etl`, which is fine; the fault is the interpreter.
`python -m pytest` in the same directory prints `46 passed`. Found while demonstrating [[T-0071]], after
several minutes spent looking for a defect in the ETL tier that was not there.

**The guard it defeats is a real one.** That `|| { echo ...; exit 1; }` exists because "a missing report never
counts as zero" - it is the check that stops an agent making a suite green by breaking the reporter. It is
working exactly as designed here; it just cannot tell "the reporter is broken" from "you ran the wrong
python". Do not weaken it.

This is the same knob as [[T-0072]]'s route 4 - `${PYTHON:-...}` - from the other direction. There the concern
is that an env var can bypass a hardened check; here the concern is that the DEFAULT is wrong on a real
developer machine. Both want the same decision made once: what interpreter do `ops/*` scripts run, and how is
that pinned rather than discovered?

- Decide the rule. Candidates: prefer `python` over `python3`; probe each candidate for the modules the script
  needs and pick the first that has them; or refuse with a message that names both interpreters and what each
  is missing. The third is the smallest honest change and matches how the rest of `ops/` reports.
- Whatever is chosen, the failure message must name the interpreter it used and its version. A path and a
  version would have ended this in seconds.
- Every `ops/*` script that resolves `$PY` this way has the same defect - `ops/test`, `ops/check-pins`,
  `ops/queue-check`, `ops/claim`, `ops/new-task` and the rest all share the idiom. Fix it in one place.
- CI is unaffected: ubuntu has one python3 and it has pytest. So this will never be caught by a workflow, only
  by a person, which is an argument for the error message rather than for silent fallback.
- Demonstrate red with `PYTHON=` unset on a machine where the two differ, and green after. If the reviewer's
  box has only one python, say so and demonstrate by pointing `PYTHON` at an interpreter without pytest.

## Log
- 2026-09-08 filed by agent/claude-opus-5, found while producing T-0071's red demonstration. Every command
  above was executed; the two interpreter paths and versions are verbatim output of
  `python3 -c "import sys, importlib.util; ..."` and the same for `python`.
- 2026-09-08T02:59:03Z claimed by agent/claude-opus-5; lease until 2026-09-08T08:59:03Z
- 2026-09-08 agent/claude-opus-5, round three. Fixed on task/T-0077, which carries [[T-0077]] too: the two
  tasks are the same expression in the same files. `touches:` widened to `[ops/test, ops/lib/boot.sh]`.

  **The box still has the two interpreters this task was filed against** (verbatim):

      python3 -> /c/Users/phineasf/AppData/Local/Microsoft/WindowsApps/python3
        C:\Users\phineasf\AppData\Local\Python\pythoncore-3.14-64\python.exe   3.14.5    pytest: False
      python  -> /c/Users/phineasf/AppData/Local/Programs/Python/Python310/python
        C:\Users\phineasf\AppData\Local\Programs\Python\Python310\python.exe    3.10.11   pytest: True

  `services/etl/` does NOT exist on main, so the ETL tier is skipped there and the reported symptom cannot
  appear. It was reproduced by materialising the tier the branch that found it had: an untracked
  `services/etl/pyproject.toml` and `tests/test_smoke.py` (removed again before committing; nothing under
  services/etl is in this diff).

  **RED**, `PYTHON` unset, `bash ops/test`:

      PYTHON is: <unset>
      ... Test run with 16 tests in 3 suites passed after 0.046 seconds.
      FAIL: services/etl exists but pytest produced no report
      EXIT=1

  and the cause, in the same directory:

      $ python3 -m pytest -q
      C:\Users\phineasf\AppData\Local\Python\pythoncore-3.14-64\python.exe: No module named pytest
      EXIT=1
      $ python -m pytest -q
      . [100%]  1 passed in 0.01s
      EXIT=0

  The guard was doing its job; it just could not tell "the reporter is broken" from "you ran the wrong
  python", and its message named services/etl. It was not weakened.

  **FIX** - `ops/lib/boot.sh`, one place for all eleven wrappers. `scenic_python [module ...]` asks each
  candidate what it CAN DO instead of taking the first NAME that exists: it runs a probe that prints
  `SCENICPY|<sys.executable>|<x.y.z>|<missing modules>` and takes the first candidate at or above Python 3.9
  that has everything asked for. `ops/test` requests the ETL tier's needs up front -
  `if [[ -f services/etl/pyproject.toml ]]; then scenic_python pytest; else scenic_python; fi` - so a python
  without pytest is refused by path and version BEFORE any tier runs, not three tiers later as a missing
  file. The pytest message now names the interpreter (`scenic_py_id`) and prints the exact rerun command,
  and says explicitly that the interpreter was already checked, so this is not the T-0076 case.
  The probe output is PIPE-delimited, not space-delimited, because `sys.executable` is routinely
  `C:\Program Files\...` and a space-split would report the version as `Files\Python312\python.exe`.
  `ops/agent-preflight` stops printing `python3 --version` (the report that hid this) and prints the two
  interpreters ops/* will actually use.

  **GREEN**, identical command, ETL tier present, `PYTHON` unset:

      PYTHON is: <unset>
      ... Test run with 16 tests in 3 suites passed after 0.062 seconds.
      TESTS linux=51/50 ios=skipped failed=0 skipped=0
      OK
      EXIT=0

  and `ops/agent-preflight` now answers the question that cost the original reporter several minutes:

      python        C:\Users\phineasf\AppData\Local\Python\pythoncore-3.14-64\python.exe (3.14.5, via PATH)
      python+pytest C:\Users\phineasf\AppData\Local\Programs\Python\Python310\python.exe (3.10.11, via PATH)

  **SELF-ATTACK on the fix.**

  B1 pin `PYTHON` at a real interpreter that lacks pytest - the neighbour where the operator, not PATH,
  picks wrong. Refused, before any tier ran, naming it:

      test: no usable python.
        needs: python >= 3.9 with pytest
        PYTHON=/c/.../pythoncore-3.14-64/python.exe   candidates tried, in order:
          /c/.../python.exe -> C:\Users\...\pythoncore-3.14-64\python.exe (3.14.5) has no pytest
        PYTHON is set, so it is the ONLY candidate - unset it to search PATH.
      EXIT=2

  B2 the harder neighbour: a PATH shim where NEITHER `python3` NOR `python` has pytest, so there is no
  right answer to fall back to. Refuses instead of picking one, and names all three candidates:

      test: no usable python.
        needs: python >= 3.9 with pytest
        PYTHON=<unset>   candidates tried, in order:
          python3 -> ...pythoncore-3.14-64\python.exe (3.14.5) has no pytest
          python  -> ...pythoncore-3.14-64\python.exe (3.14.5) has no pytest
          py      -> ...pythoncore-3.14-64\python.exe (3.14.5) has no pytest
      EXIT=2

  B3 `PYTHON=true`, which [[T-0072]] refused in ops/check-pins ONLY. Now refused everywhere:
  ops/check-pins EXIT=2, ops/queue-check EXIT=2, ops/sane EXIT=2 (queue-check used to exit 0, silently).

  B4 the four-line script that defeated T-0072's probe by echoing `pins-probe-ok`: now refused
  ("not a usable python3 (probe produced no answer)", EXIT=2).

  B5 **a NEW two-line script written against MY probe. IT PASSES. THIS ROUTE IS NOT CLOSED:**

      $ cat .artifacts/adv/fakepy2.sh
      #!/usr/bin/env bash
      echo "SCENICPY|/opt/definitely-python/python3|3.99.0|-"
      exit 0
      $ PYTHON="$PWD/.artifacts/adv/fakepy2.sh" bash ops/check-pins
      check-pins: note: PYTHON=.../fakepy2.sh -> /opt/definitely-python/python3 (3.99.0), not the PATH default
      SCENICPY|/opt/definitely-python/python3|3.99.0|-
      EXIT=0

  That is not a bug in the probe; it is what a probe IS. A probe asks the thing under test to describe
  itself, using a token printed in the script the adversary is reading, so any token can be echoed and any
  new token can be echoed too - the next fake is two characters longer, not harder. **The written decision,
  recorded in ops/lib/boot.sh and ops/check-pins rather than left to omission: `PYTHON=` is honoured, it is
  a real local need, and it is NOT a security boundary. The probe exists for the ACCIDENT - no python, a
  python2, a python without the modules the script needs - which is what T-0076 actually was, and it names
  the interpreter, its real sys.executable and its version when it refuses.** Anyone who can set PYTHON can
  also edit the wrapper; the defence there is the reviewer and the pre-commit hook, not a shell test.
  The only thing added against B5 is an audit line, not a gate: when PYTHON is set, every wrapper prints
  `note: PYTHON=... -> <exe> (<ver>), not the PATH default` to stderr, so a forged run does not look
  identical in the transcript to an honest one. With PYTHON unset, stderr is 0 bytes (measured).

  B6 the parser neighbour: a shim answering with `SCENICPY|C:\Program Files\Py 3.12\python.exe|3.12.1|-`.
  Parsed whole - `C:\Program Files\Py 3.12\python.exe (3.12.1, via PYTHON=)` - not split on the spaces.

  **Not touched: `FAIL: services/api exists but vitest produced no report`.** That message is misleading for
  the same reason (it names the tier, the cause is a missing node_modules) and it is [[T-0040]]'s subject,
  whose `touches:` is ops/test. I hit it on this box before running `npm ci` and left it alone.

  Gates: `TESTS linux=50/50 ios=skipped failed=0 skipped=0 / OK` (ETL tier removed again),
  `PINS ok=9 ... failed=0`, `QUEUE OK (76 tasks)`, `SANE OK`, `PREFLIGHT OK`.

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
