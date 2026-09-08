---
id: T-0062
title: services/etl/tests/test_dockerfile.py is 436 lines on task/T-0046
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T02:08:19Z
lease_expires_at: 2026-09-08T08:08:19Z
worktree: wt/T-0062
branch: task/T-0062
exclusive: []
touches: [services/etl/tests/, ops/lib/check-line-cap]
pins_affected: []
reviewer: null
depends_on: [T-0046, T-0058]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`services/etl/tests/test_dockerfile.py` is **436 lines** on `task/T-0046`, against the 300-line cap. It was
125 lines on `task/T-0038` and grew across T-0046's four review rounds of pip-parser work.

Nothing reported it, because `ops/lib/check-line-cap` globbed Swift only. T-0058 extends the cap to Python and
TypeScript - and the merge rehearsal that found this file is the reason T-0058 carries an exemption for it:
without one, the first merge of the Dockerfile chain after T-0058 turns `main` red on a file that was over the
cap long before either task existed.

So this is not a regression and not T-0058's fault; it is a debt the new check made visible, which is what the
check is for. The exemption is the deliberate, auditable way to carry it for exactly as long as it takes to
land this task, and `check-line-cap` refuses an exemption whose file has dropped back under the cap, so it
cannot quietly become permanent.

- Split it along whatever seams the file already has. T-0046's log describes distinct concerns - the pip
  destination-flag whitelist, the PEP 508 marker segmentation, the shlex tokenizer, and the Dockerfile
  parsing itself - which is a good sign the file is several tests wearing one filename.
- Do NOT delete tests to get under the number. The file is long because T-0046 was attacked four times and
  each round added real cases; every one of them is load-bearing and a reviewer should refuse any diff that
  drops coverage to satisfy a line count.
- When it is under 300, DELETE the exemption entry from `ops/lib/check-line-cap`. Leaving it is itself a
  failure the check reports: "exemption(s) no longer needed - the file is under the cap, so delete the entry".
- Verify with the merge rehearsal, not just on the branch: merge `task/T-0046` and `task/T-0058` into a
  scratch branch and run `bash ops/lib/check-line-cap`. That combination is the only place the problem exists.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from a full merge rehearsal - 30 branches merged in dependency order
  into a throwaway, gates run after each. This file is invisible on every branch individually and only appears
  when the Dockerfile chain meets T-0058.
- 2026-09-08T02:08:19Z claimed by agent/claude-opus-5; lease until 2026-09-08T08:08:19Z

- 2026-09-08 agent/claude-opus-5 — split, exemption removed, verified on the branch combination that is the
  only place the problem exists.

  **The seam was already there.** The file was two things wearing one filename: pip's `install` argument
  grammar, which knows nothing about Docker, and a set of assertions about this repo's image. Lines 36-248
  were the parser, entire and self-contained. They moved verbatim into
  `services/etl/tests/pip_install_grammar.py`; `test_dockerfile.py` imports the two entry points it uses.

        services/etl/tests/test_dockerfile.py       436 -> 226 lines
        services/etl/tests/pip_install_grammar.py     0 -> 234 lines

  The module is deliberately NOT named `test_*`, so pytest does not collect it, and it imports nothing from
  the Dockerfile side. `tests/` is already a package and `pyproject.toml` sets `pythonpath = ["."]`, so
  `from tests.pip_install_grammar import ...` needed no configuration change.

  **No test was deleted, and this was proved rather than asserted.** The brief is explicit that the file is
  long because T-0046 was attacked four times and every case is load-bearing. Collected node ids before and
  after, sorted and diffed:

        before: 46   after: 46
        diff -> no output.  IDENTICAL TEST SET (same node ids, same count)

  `46 passed in 3.56s` both sides. Every docstring moved with its function: they carry the history of four
  review rounds - the hallucinated `--build` flag that abbreviated `--build-constraint` into a real bypass,
  the short-flag bundling that resolves through the FIRST value-taking letter, the PEP 508 marker torn apart
  by splitting on an unquoted `;` - and each is the reason its rule exists, so losing them would lose the
  argument for the code.

  **Red then green on the exemption, which is the second half of the task.** With the split done and the
  entry still in `ops/lib/check-line-cap`:

        P-SRC-02: exemption(s) no longer needed - the file is under the cap, so delete the entry:
          services/etl/tests/test_dockerfile.py (226 lines, exempt for T-0062)
        exit 1

  That exit code was checked directly (`bash ops/lib/check-line-cap >/dev/null 2>&1; echo $?`) and not
  through a pipe: `... | tail -8; echo $?` reports **tail's** status, which is 0, and would have read as a
  message printed by a passing check. After deleting the entry:

        P-SRC-02: 10 Swift files, 28 source files under the cap, 1 exempt      exit 0

  The one remaining exemption is `ops/lib/queue.py` for T-0059, untouched.

  **Verified on the merge, not just on the branch**, as the brief requires. This worktree is
  `task/T-0046` + `origin/task/T-0058` + `origin/main` merged - T-0046 carries the 436-line file, T-0058
  carries the Python cap and the exemption, and neither branch alone can see the problem. Both merges were
  clean. Gates on that tree:

        pytest (services/etl)   46 passed
        ops/queue-check         QUEUE OK (71 tasks)
        check-line-cap          P-SRC-02: 10 Swift files, 28 source files under the cap, 1 exempt
        check-exec-bits         P-OPS-01: 25 files, 15 required present, all modes correct

  Handing to review. The reviewer should re-run the node-id diff rather than trusting the count: a count is
  equally satisfied by deleting one test and adding another, which is the shape this task was warned about.
