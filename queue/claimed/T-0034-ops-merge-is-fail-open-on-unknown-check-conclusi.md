---
id: T-0034
title: ops/merge is fail-open on unknown check conclusions and crashes on a nameless check
state: claimed
owner: agent/fixer-T0034
owner_session: d217767a
claimed_at: 2026-09-08T13:37:04Z
lease_expires_at: 2026-09-08T15:37:04Z
worktree: .worktrees/T-0034
branch: task/T-0034
exclusive: []
touches: [ops/lib/check-merge-fail-closed, pins/PINS.yaml]
pins_affected: [P-OPS-03]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "P-OPS-03 exists and its assertion, ops/lib/check-merge-fail-closed, passes on main"
  - "RED-1: the check fails when ops/merge is replaced by its pre-T-0021 body (the real historical defect)"
  - "RED-2: the check fails when classify-checks.py's PASSING set is widened to accept SKIPPED"
  - "RED-3: the check fails when the classifier is made to refuse everything (the non-vacuity control)"
  - "RED-4: ops/check-pins itself reports failed=1 naming P-OPS-03 when the classifier is regressed"
  - "ops/merge is NOT modified by this task: the defect in the title is not reproducible on main"
---
## Brief

**The defect in this task's title is not reproducible on main. It was already fixed, by T-0021, before this
task was claimed.** The honest finding is therefore REFUTED-as-filed, and the work this task actually delivers
is the check that was missing: the property is now pinned instead of remembered.

What was filed. T-0034 was opened from reviewer-11's fast-follow recommendation on PR #10: ops/merge's inline
classification asked *"is this conclusion in my list of BAD ones?"*, so `SKIPPED`, `NEUTRAL`, `STALE` or any
conclusion GitHub invents next year was neither pending nor failed and the gate proceeded; and a check record
with no `name` raised `KeyError` inside a shell substitution, which bash swallowed into `failed=""`, so a
genuine FAILURE printed "every gate passed". The Brief was never written, so the task file carried only the
title.

What happened next. T-0021 absorbed that recommendation in the same PR the reviewer raised it on: it moved
classification into `ops/lib/classify-checks.py` (SUCCESS is the only passing conclusion; a nameless check is
labelled `<unnamed check #n>`; a parse error exits non-zero) and landed on main. Nobody re-filed or closed
T-0034, so it sat in `ready/` describing a defect that no longer existed.

**RED, recorded against the code that actually had the defect** (`git show 8ba0fed^:ops/merge`, driven through
`ops/lib/gh-stub-for-merge-tests`, `--dry-run`, no network):

    [{"name":"core","c":"SKIPPED"}]          -> checks total=1 pending=0 failed=[none] -> "every gate passed", exit 0
    [{"name":"core","c":"QUANTUM_FAILED"}]   -> checks total=1 pending=0 failed=[none] -> "every gate passed", exit 0
    [{"c":"FAILURE"}]                        -> KeyError: 'name' traceback, then failed=[none] -> "every gate passed", exit 0

The same three shapes against main's `ops/merge` refuse with exit 1 and name the check
(`core(SKIPPED)`, `future(QUANTUM_FAILED)`, `<unnamed check #0>(FAILURE)`). I could not make main's gate
fail-open on any conclusion I tried, and I did not invent a change to `ops/merge` in order to have something
to show: **this task's diff does not touch `ops/merge` at all.**

Why the task is still worth its number. The property was won once and then guarded by nothing: no test, no
pin, no assertion anywhere. It survived only as prose in a merged task log, while three open tasks
([[T-0115]], [[T-0065]], [[T-0044]]) queue up to edit `ops/merge` and one plausible edit - widening the
passing set to quiet a noisy SKIPPED check - restores the exact defect with the suite green, CI green and the
merge gate quietly saying yes. Per CLAUDE.md, *a check that has never been seen red is untested*; this one had
never been seen at all.

So T-0034 delivers **P-OPS-03** and its assertion `ops/lib/check-merge-fail-closed`, which asserts, offline,
through the repository's own recorded `gh` stub:

1. every conclusion GitHub documents that is not SUCCESS, plus conclusions it has not invented yet, plus
   strings that only look like success (`SUCCESSFUL`, `SUCCESS_WITH_WARNINGS`, `success_ish`), is refused;
2. an empty conclusion counts as pending - it blocks, it never passes;
3. a check with no `name` is labelled and reported, never dropped, and never crashes the classifier;
4. an unparseable rollup refuses instead of proceeding on an empty answer;
5. `ops/merge` still routes classification through `classify-checks.py` in executable (non-comment) code;
6. **two positive controls**: an all-SUCCESS rollup classifies clean, and `ops/merge` prints `failed=[none]`
   for it - without these, a gate that refused everything would satisfy points 1-4 trivially.

**Not absorbed, deliberately.** [[T-0115]] (zero-file-diff merges) touches the same file and is a different
task; nothing here fixes or pre-empts it. One forward dependency is worth naming for whoever takes it: if
T-0115 adds a gate that refuses *before* the checks loop, P-OPS-03's positive control (point 6) goes red,
because the fixture branch `task/T-0000-fail-closed-fixture` has no diff at all. That is the pin doing its
job, not a bug in it - the fixture should be extended (give the stub a non-empty diff, or pass T-0115's
override), never deleted. The check prints that instruction in its own failure message.

## Log
- 2026-09-08T13:37:04Z claimed by agent/fixer-T0034; lease until 2026-09-08T15:37:04Z
- 2026-09-08T13:45:00Z Read the brief-less task, `ops/merge`, `ops/lib/classify-checks.py`, the gh stub, and
  [[T-0115]] (read, not fixed). `git log -- ops/merge` shows 8ba0fed "T-0021: make the merge gate fail-closed;
  fix the stub that hid it" is already on main - so the title's defect was suspect before I ran anything.
- 2026-09-08T13:50:00Z ATTEMPTED RED on main, the two shapes from the title, through the recorded stub
  (`STUB_ROLLUP=... bash ops/merge 1 --dry-run --no-task-reason="T-0034 probe"`, `gh` = the stub on PATH):
  `[{"name":"core","c":"SKIPPED"}]` -> `MERGE REFUSED: failing checks: core(SKIPPED)`, exit 1.
  `[{"c":"FAILURE"}]` -> `MERGE REFUSED: failing checks: <unnamed check #0>(FAILURE)`, exit 1.
  **Could not reproduce.** No fail-open path found in `ops/merge` by inspection either: gate 1 (queue/done),
  the `mergeStateStatus` case, the classify exit-code check and the total/pending/failed scrape are all
  fail-closed, and the jq that feeds the classifier (`.name // .context`, `.conclusion // .state // "PENDING"`)
  cannot produce a passing value for a missing field.
- 2026-09-08T13:55:00Z RED, recorded against the body that DID have the defect, `git show 8ba0fed^:ops/merge`
  (saved to .artifacts/T-0034/ops-merge.prefix, never committed): SKIPPED -> exit 0 "every gate passed";
  QUANTUM_FAILED -> exit 0; nameless FAILURE -> `KeyError: 'name'` traceback swallowed into `failed=[none]`,
  exit 0. This is the red run the Brief asked for; it is dated, not live.
- 2026-09-08T14:20:00Z Wrote `ops/lib/check-merge-fail-closed` (P-OPS-03's assertion). Design notes: it drives
  BOTH the classifier directly and the whole gate through the recorded stub, so it fails whether the
  regression lands in `classify-checks.py` or in `ops/merge`'s wiring; the structural half greps `ops/merge`
  with comment lines stripped first, per CLAUDE.md's "never anchor a guard on a comment"; it carries two
  positive controls so it cannot be satisfied by a gate that refuses everything; and it sweeps all twelve
  conclusions in ONE rollup because process spawns dominate its runtime on the Windows box.
- 2026-09-08T14:25:00Z GREEN: `bash ops/lib/check-merge-fail-closed` -> "P-OPS-03: 12 unrecognised conclusions
  refused, nameless check reported not dropped, green rollup still merges", exit 0. Wall clock 2m10s on the
  Windows dev box, of which ~2m is process creation (8 interpreter starts measured at 2.4-5.7 s each here);
  it is 8 python starts and ~20 short bash processes, so it is seconds on Linux CI. Timed with `time`, not
  estimated.
- 2026-09-08T14:35:00Z **RED-1** (the real historical defect): `cp .artifacts/T-0034/ops-merge.prefix ops/merge`
  -> the check exits 1 with three findings: "ops/merge no longer calls ops/lib/classify-checks.py in
  executable code"; "ops/merge ACCEPTED SKIPPED + an unknown conclusion + a nameless FAILURE (exit 0)" quoting
  the `KeyError: 'name'` traceback and `failed=[none]`; and "ops/merge ACCEPTED an unparseable rollup (exit 0)"
  quoting two `TypeError: string indices must be integers` tracebacks under "every gate passed". Reverted.
- 2026-09-08T14:40:00Z **RED-2** (the regression an agent would actually write): `PASSING = {"SUCCESS",
  "SKIPPED"}` in classify-checks.py -> exit 1, "conclusion 'SKIPPED' is neither failed nor pending - the gate
  is fail-OPEN for it" and "the refusal never named core(SKIPPED)". Reverted.
- 2026-09-08T14:45:00Z **RED-3** (non-vacuity control): `PASSING = set()`, i.e. a gate that refuses everything
  -> exit 1 on both positive controls ("an all-SUCCESS rollup was reported as failing", "never reached a clean
  checks line"). Without this control the other four reds could be satisfied by a broken gate. Reverted.
- 2026-09-08T14:55:00Z **RED-4** (the pin wiring, not just the script): with a one-pin `pins/PINS.yaml` and the
  RED-2 mutation, `bash ops/check-pins` -> `PINS ok=0 skipped=0 pending=0 expired=0 failed=1 tier=linux`,
  naming P-OPS-03 and quoting the check's output, exit 1. Both files restored; that restore also reverted my
  own uncommitted PINS.yaml edit, which I re-applied - noting it because a demo script that runs
  `git checkout --` on a file you are editing will silently eat your work.
- 2026-09-08T15:05:00Z Full `bash ops/check-pins` and `bash ops/test` results recorded below.
- 2026-09-08T15:05:00Z Scope kept deliberately small: **no change to `ops/merge`**. Two things I found and did
  NOT fix, so they stay visible for their owners: (a) [[T-0115]]'s zero-file-diff gate will interact with
  P-OPS-03's positive control as described in the Brief; (b) `ops/merge`'s `task="$(... grep -oE 'T-[0-9]{4}')"`
  returns MULTIPLE lines for a branch naming two task ids, which then goes into `grep -q "^$task-"` as a
  two-pattern query - adjacent to [[T-0092]]/[[T-0044]] (embedded newlines in task-file values), not to this
  task's title, and not reproducible as a merge of the wrong thing.
