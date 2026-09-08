---
id: T-0102
title: ops/check-pins --tier with no value prints an IndexError traceback, the same shape T-0087 fixed in queue.py
state: done
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T08:53:47Z
lease_expires_at: 2026-09-08T10:53:47Z
worktree: null
branch: task/T-0102
exclusive: []
touches: [ops/lib/pins.py]
pins_affected: []
reviewer: agent/reviewer-pr64
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0087 was "three ops/* entry points print a traceback where every other one prints a usage line", and its
brief asked whether the same shape existed elsewhere. It does, one file over. `ops/lib/pins.py` reads the
value of `--tier` by index:

    ops/lib/pins.py:103:        tier = argv[argv.index("--tier") + 1]

so the flag written without a value indexes off the end of the list. Red, executed on task/T-0087 at
0be7589, from the worktree root:

    $ bash ops/check-pins --tier
        sys.exit(main(sys.argv[1:]))
                 ~~~~^^^^^^^^^^^^^^
      File "C:\Users\phineasf\Documents\GitHub\wt\T-0087\ops\lib\pins.py", line 103, in main
        tier = argv[argv.index("--tier") + 1]
               ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
    IndexError: list index out of range
    EXIT=1

Two things are wrong here, not one. The traceback is the visible half; the exit code is the other. Every
other ops/* entry point answers a bad invocation with exit 2, and this exits 1 - the code check-pins uses
for "a pin FAILED". An agent or a CI step that reads only the status cannot tell "you typed the flag wrong"
apart from "a load-bearing property of this repo is broken".

Wanted: a usage line and exit 2, matching queue.py's main() after T-0087. While in there, check what a
`--tier` value that is not a tier does - `ops/check-pins --tier bogus` must not be able to report a green
run over zero pins, which is the T-0066 vacuity class in a second place.

Not fixed under T-0087: `ops/lib/pins.py` is outside that task's `touches:` and is held by T-0066, which is
claimed. Filed rather than fixed so the finding is not lost and T-0066's owner is not conflicted with.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from T-0087, whose brief asked for the class to be swept rather
  than only the three named entry points. The red run above is verbatim.

- 2026-09-08 — **filed as `T-0088` and renumbered to `T-0102`: that id was allocated twice.** `main` carries a
  different `T-0088` ("the 69 mutation survivors are five gaps, and one of them is the fixture's own record
  shape"), filed from `task/T-0081` while this branch was in flight.

  **Neither tree was wrong on its own, which is the point.** `ops/queue-check` passes on `main` and passes on
  this branch; the duplicate exists only in the MERGE of the two, and it was found by merging them in a
  throwaway. That is the same merge-time-only class as the stale `claimed/` copy [[T-0063]] was filed for and
  the reason [[T-0065]]'s rehearsal exists — and it was invisible to that rehearsal too, because this branch
  has no open PR and the rehearsal enumerated pull requests ([[T-0099]]).

  Second instance of the same race in one day; `T-0099` was the first. Root cause and fix are [[T-0101]]:
  `next_id()` READS the refs and the commit that publishes the id happens minutes later, so two allocators
  that both read before either pushed get the same number. Allocation needs the compare-and-swap that
  claiming already has.
- 2026-09-08T08:53:47Z claimed by agent/claude-opus-5; lease until 2026-09-08T10:53:47Z

- 2026-09-08 — **the brief asked what a bad value does. The answer was worse than the traceback it was
  filed for.**

  **RED**, all four executed on this branch before the change:

        --tier          IndexError traceback                            real exit 1
        --tier bogus    PINS ok=0 skipped=9 pending=3 failed=0          real exit 0
        --tier device   PINS ok=0 skipped=9 pending=3 failed=0          real exit 0
        --nosuchflag    ignored entirely                                real exit 0
        extra-word      ignored entirely                                real exit 0

  **`--tier bogus` is the finding, not the traceback.** A typo — `--tier linx` — skips every pin, runs no
  assertion, prints a summary that reads exactly like success, and exits 0. That is P-PROC-01 passing on an
  empty set, reachable by a slip of the finger, which is the defect class this repository exists to refuse.
  `--tier device` does the same, and `device` is not even a tier any pin declares; the declared set is
  measured from `runs_on` as `{linux: 11, mac: 9, human: 1}`.

  The traceback's exit code was the brief's second point and it stands: `1` is what this tool returns for
  *a pin FAILED*, so a CI step reading only the status could not tell a typo from a broken invariant.

  **GREEN:**

        --tier          exit 2  check-pins: --tier needs a value; it was the last word on the line.
        --tier bogus    exit 2  --tier 'bogus' is a tier no pin declares. Declared: human, linux, mac.
        --tier device   exit 2  --tier 'device' is a tier no pin declares. Declared: human, linux, mac.
        --nosuchflag    exit 2  --nosuchflag is not an option of check-pins.
        extra-word      exit 2  'extra-word' is not an option. check-pins takes no operands.
        --tier human    exit 1  PINS ok=0 ... - no assertion ran: every pin was skipped or is pending

  **The real invocations are unchanged**, which is the control that matters for a change to the gate itself:

        (no args)       exit 0  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
        --source-only   exit 0  PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
        --tier linux    exit 0  PINS ok=9 ...
        --tier mac      exit 0  PINS ok=9 ...

  **Two decisions worth stating.**

  The tier set is **derived from the pins**, never a literal `{linux, mac, device, human}` here. A hard-coded
  list would keep accepting `--tier device` long after the last device pin was deleted, and would reject a
  tier somebody legitimately adds — both are the check disagreeing with the file it exists to enforce. This
  is the same argument `ops/merge-rehearse` makes for deriving its ordering edges instead of listing them.

  `ok == 0` now exits 1 with a line saying so. `--tier human` reaches that honestly — its one pin is pending
  — and that is exactly the state that must not read as success, because "nothing ran" and "everything
  passed" print the same summary otherwise. The counts already said why; now the exit code says it too.

  Every exit code above was read with the pipe removed. `... | head -1; echo $?` reports the status of
  `head`, and this file's own brief was written from a `$?` that had been through a pipe.

- 2026-09-08 — **reviewed by agent/reviewer-pr64 (not the owner). PASS. Every claim in the GREEN, RED and
  control tables above was re-executed on this branch at `2b20533`, not read.** Exit codes were taken with
  `<cmd> >/dev/null 2>&1; echo $?` — no pipe on the measured command — because `... | head -1; echo $?`
  reports `head`'s status, which is how this task's own brief came to be written from a wrong `1`.

  **Verify commands.** `bash ops/test` → exit **0**, `TESTS linux=50/50 ios=skipped failed=0 skipped=0`.
  `bash ops/check-pins` → exit **0**, `PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux`.
  `acceptance:` is `[]` — that is the `ops/new-task` default (`ops/lib/queue.py:266`), not an omission, so
  `verify:` was run as the acceptance set.

  **Two environment traps had to be cleared first, and both would have produced a false FAIL.** The worktrees
  moved from `GitHub/wt/<id>` to `GitHub/scenic_drive/.worktrees/<id>`, so `.build`'s Swift ModuleCache still
  carried the old absolute path and `swift test` died with `could not build module 'vcruntime'` — P-SAFE-05
  failed and `check-pins` exited 1 on the *unmodified* control. Deleting
  `.build/x86_64-unknown-windows-msvc/debug/ModuleCache` fixed it. Separately `services/api/node_modules` was
  never installed here, so `ops/test` exited 1 on `FAIL: services/api exists but vitest produced no report`;
  `npm ci` fixed it. Neither is attributable to this change — it touches `ops/lib/pins.py` only — but both
  are worth recording, because a reviewer who stopped at the first non-zero would have failed a good task.

  **RED, reproduced by the reviewer** by checking out `2b20533^:ops/lib/pins.py` over the working file and
  re-running the matrix, then restoring:

        --tier          IndexError at pins.py:103, verbatim as filed        real exit 1
        --tier bogus    PINS ok=0 skipped=9 pending=3 failed=0 tier=bogus   real exit 0
        --tier device   PINS ok=0 skipped=9 pending=3 failed=0 tier=device  real exit 0
        --tier human    PINS ok=0 skipped=9 pending=3 failed=0 tier=human   real exit 0
        --nosuchflag    ignored entirely, ok=9                              real exit 0
        extra-word      ignored entirely, ok=9                              real exit 0
        --tier=linux    ignored entirely (old code matched only bare --tier) real exit 0

  `--tier bogus` exiting **0** over nine skipped pins and zero assertions is the finding, and it is real. The
  check is not vacuous: its subject was broken and it went from 2 to 0 on exactly the inputs claimed.

  **GREEN and control, re-measured:** `--tier` / `--tier bogus` / `--tier device` / `--nosuchflag` /
  `extra-word` / `--tier=` all exit **2** with the quoted messages; `--tier human` exits **1** with the
  `no assertion ran` line; and the four real invocations are untouched — `(no args)` ok=9 exit 0,
  `--source-only` ok=3 skipped=8 pending=1 exit 0, `--tier linux` ok=9 exit 0, `--tier mac` ok=9 exit 0.
  Both CI steps in `.github/workflows/linux-core.yml` are `check-pins` and `check-pins --source-only`, so
  neither regresses. The `{linux: 11, mac: 9, human: 1}` tally reproduces from `pins/PINS.yaml`.

  **The "derived from the pins, never a literal" claim was tested, not taken on faith.** Adding `device` to
  one pin's `runs_on` flipped `--tier device` from exit 2 to exit **0** with `ok=1 tier=device`; PINS.yaml was
  then restored. A hard-coded list could not have done that, so the decision recorded above is the one the
  code actually implements.

  **Two nits, neither blocking, both filed here rather than fixed — a reviewer finds and does not fix.**
  (1) Repeated `--tier` is silent last-wins: `--tier bogus --tier linux` exits **0** and swallows the typo,
  while `--tier linux --tier bogus` exits 2. That is [[T-0084]]'s "repeated scalar flags should be an error,
  not a silent last-wins" reappearing in brand-new code. (2) `pins/PINS.yaml:4` is a schema comment reading
  `runs_on [linux|mac|device|human]`, and `--tier device` is now refused — the comment advertises a tier the
  tool rejects. The implementation is right to ignore it (CLAUDE.md: never anchor on a comment), but the
  comment is now stale. Also noted: nothing automated will catch a revert of `_argv` — there is no pin or
  test over check-pins' own argument handling, exactly as [[T-0087]] left `queue.py`.
