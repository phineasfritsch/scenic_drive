---
id: T-0070
title: queue-check cannot see a duplicate task, only a duplicate id, and reports OK on an empty queue
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T03:01:15Z
lease_expires_at: 2026-09-08T09:01:15Z
worktree: wt/T-0070
branch: task/T-0070
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**Two task files can carry different ids and the same brief, and nothing anywhere notices.** Found by
reading, then confirmed byte-for-byte:

    diff <(sed 's/^id: T-006[67]$/id: X/' queue/backlog/T-0066-*.md) \
         <(sed 's/^id: T-006[67]$/id: X/' queue/backlog/T-0067-*.md)
    -> IDENTICAL apart from the id line

`ops/new-task` was invoked twice for one finding during the self-referential-check sweep and allocated
T-0066 and T-0067 for the same work. `ops/queue-check` passed on that tree, because its only uniqueness
assertion is on the id:

    if tid in seen:
        problems.append(f"duplicate id {tid}: ...")

The id is exactly the field `new-task` guarantees is unique, so the check can never fire on anything
`new-task` produces. It is a gate on the one thing that cannot go wrong.

**The cost is not cosmetic.** Two ids for one defect means two agents claim, two worktrees, two branches
touching the same paths, and the collision surfaces at merge as a conflict rather than at claim as a
refusal. That is the merge-time defect class `ops/merge-rehearse` exists to find, filed into the queue by
the queue's own tooling.

**Second, unrelated hole in the same function.** The success line is

    print(f"QUEUE OK ({len(seen)} tasks)")

and `seen` is populated by iterating `tasks()`. An empty or unreadable `queue/` prints `QUEUE OK (0 tasks)`
and exits 0 - the same shape already fixed in `ops/lib/check-exec-bits` (MIN_FILES + REQUIRED) and
`ops/lib/check-line-cap` (MIN_CAPPED), and filed against `ops/check-pins` as [[T-0066]]. Demonstrate it
before fixing it: point the queue root at an empty directory and show the exit code.

- Refuse two tasks whose titles are equal after normalisation, and two whose briefs are equal ignoring the
  `id:` line. Report both paths, the way the duplicate-id arm does.
- Put a floor under the task count so an empty queue is red, not `QUEUE OK (0 tasks)`.
- `ops/new-task` should refuse at creation time, not only at check time - a duplicate that is never
  committed costs nothing, and one that is claimed costs two worktrees.
- Dead code in the same function, found while reading, worth removing in the same pass:

        if state == "done":
            for dep in fm.get("depends_on") or []:
                pass  # done tasks may reference anything

  It iterates to do nothing. Delete it or make it assert something.
- Demonstrate each case red then green in this log.

## Log
- 2026-09-08 filed by agent/claude-opus-5 after `ops/new-task` filed the same finding twice as T-0066 and
  T-0067 and `ops/queue-check` stayed green. T-0067 was deleted; T-0066 keeps the finding.
- 2026-09-08T03:01:15Z claimed by agent/claude-opus-5; lease until 2026-09-08T09:01:15Z

- 2026-09-08 agent/claude-opus-5 — duplicate work detected, `new-task` refuses at creation, dead loop removed.

  **Half of this task was already done by [[T-0073]]** and is recorded here so the next reader does not go
  looking for it: the population floor (`MIN_TASKS = 40`), the missing-state-directory check, the
  outside-`STATES` check and the widened glob all landed with T-0073's round-two fix. `QUEUE OK (0 tasks)` is
  already dead. What was left is the duplicate.

  **RED.** Copy any task under a fresh id — which is exactly how T-0066 and T-0067 came to exist, filed
  minutes apart for one finding, byte-identical apart from the `id:` line:

        sed 's/^id: T-[0-9]\{4\}$/id: T-9901/' queue/backlog/T-0008-*.md > queue/backlog/T-9901-duplicate.md
        bash ops/queue-check
        QUEUE OK (77 tasks)                                                            exit 0

  The only uniqueness assertion was on the id, and the id is the one field `new-task` guarantees. It was a
  gate on the one thing that could not go wrong.

  **GREEN**, three ways, each executed:

        same brief, different id
          QUEUE CHECK FAIL
           - 2 tasks share one brief (identical but for the id line): queue/backlog/T-0008-...md,
             queue/backlog/T-9901-duplicate-of-another-task.md                          exit 1

        same title, genuinely different brief
          QUEUE CHECK FAIL
           - 2 tasks share one title: queue/backlog/T-0008-...md, queue/backlog/T-9902-...md

        ops/new-task with an existing title
          refusing: T-0008 already has this title (queue/backlog/T-0008-...md).
          Add to that task, or give this one a title that says how it differs.          exit 1

        the same title with different case, spacing and punctuation - which is how two agents actually collide
          refusing: T-0008 already has this title (...)                                 exit 1

        control: a genuinely new title
          queue/backlog/T-0082-a-title-nothing-else-in-the-queue-has.md                 exit 0

  Refused at creation as well as at check on T-0056's argument: after the fact is a report, at the transition
  is a prevention. A duplicate never committed costs nothing; one that is claimed costs two worktrees, two
  branches over the same paths, and a merge conflict instead of a refusal.

  **AN INVALID TEST, RECORDED BECAUSE I NEARLY BELIEVED IT.** The first `new-task` run did NOT refuse, and it
  looked like the fix was dead. It was not: I had typed *"container, Bay Area graph, 20 goldens"* while
  T-0008's real title is *"container + Bay Area graph from R2, 20 goldens"*. Two different titles, correctly
  not matched. The check that saved me was reading both `title:` lines rather than trusting the slug, which is
  the same mistake shape as T-0071's invalid hook demonstration one task earlier.

  **SELF-ATTACK, and the honest limit.** Normalising case, punctuation and whitespace catches the collision
  that actually happens - two agents writing the same sentence minutes apart. It does not catch two genuinely
  different sentences describing one finding, and no syntactic check can. This narrows the window; it does not
  close the class, and anyone reading `2 tasks share one title` should not conclude that its absence means no
  duplicate exists.

  Also removed, found while reading:

        if state == "done":
            for dep in fm.get("depends_on") or []:
                pass  # done tasks may reference anything

  A loop that iterates to do nothing. Now zero occurrences.

  `ops/lib/queue.py` is 653 lines - it was 615 before this change and is exempt for [[T-0059]], which owns the
  split. This adds 38 lines to a file already three times over the cap. Stated rather than hidden: T-0059 is
  now more urgent than when it was filed, and this task made it worse.

  Gates: `QUEUE OK (76 tasks)`, `PINS ok=9 failed=0`, `P-SRC-02` clean, `P-OPS-01: 26 files, all modes correct`.

- 2026-09-08 agent/claude-opus-5 — **an independent reviewer of PR #50 returned FAIL, and was right. This
  change shipped a regression that broke three real branches.** Fixed here.

  **CRITICAL — the duplicate-brief guard fired on `ops/new-task`'s own placeholder.** Every task the tool
  creates carries the same template body, so any two freshly-filed, entirely unrelated tasks hashed
  identically and turned `queue-check` — and pin P-PROC-01 with it — red. Reproduced on a real pushed branch:

        task/T-0040 with its own queue.py     QUEUE OK (61 tasks)                       exit 0
        task/T-0040 with this change          QUEUE CHECK FAIL
                                               - 3 tasks share one brief ...: T-0032, T-0033, T-0034

  Three unrelated tasks whose only shared text was the template. `task/T-0027` and `task/T-0029` regressed
  the same way. **A guard that fires on the tool's own output is the false-positive failure this session
  already recorded once**, in T-0079's ratchet check, and I shipped it again a few hours later.

  The fix uses `brief_is_unwritten()`, which T-0056 added and which matches on SHAPE rather than on the
  placeholder wording — so rephrasing the template cannot silently switch the guard off. After it:

        task/T-0027   base: QUEUE OK (51 tasks)   fixed: QUEUE OK (51 tasks)
        task/T-0029   base: QUEUE OK (51 tasks)   fixed: QUEUE OK (51 tasks)
        task/T-0040   base: QUEUE OK (61 tasks)   fixed: QUEUE OK (61 tasks)

        CONTROL, the duplicate this guard exists for, on task/T-0021:
        QUEUE CHECK FAIL
         - 2 tasks share one written brief: T-0066..., T-0067...

  **MEDIUM — "identical but for the id line" was false, in the code and in the message.** The hashed text is
  the body AFTER the front matter, which never contains an `id:` line, so the filter was dead code with a
  misleading name and the emitted message described something that could not happen. Filter removed, message
  now reads "share one written brief", docstring corrected.

  **LOW — an empty-normalising title exempted a task from the title check entirely.** Two files for one
  finding could pass green by having no usable title. Now reported.

  **LOW — the suppression predicate silenced genuine title duplicates.** `set(paths) <= set(q)` let any
  SUPERSET body group suppress a real title report, naming an innocent third task. Now an exact-set test.

  **Not fixed here, and the reviewer is right that it stands:** the creation-time refusal in `cmd_new` reads
  only the local working tree, so the "two agents, two worktrees" duplicate this task's own Brief calls the
  entire cost is not prevented — while `_ids_in_refs()` in the same file deliberately scans remote refs for
  exactly that reason. That is a real gap and it needs the same remote scan; filed as its own task rather
  than bolted on here, because it changes `ops/new-task` from a local operation into a networked one.
