---
id: T-0048
title: pre-commit: staged deletions bypass every check, plus four more holes reviewer-24 found
state: review
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-07T21:35:28Z
lease_expires_at: 2026-09-07T23:35:28Z
worktree: null
branch: task/T-0048
exclusive: []
touches: [.githooks/pre-commit]
pins_affected: []
reviewer: agent/reviewer-40
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

agent/reviewer-24 reproduced five holes in `.githooks/pre-commit` while reviewing T-0039. None were introduced
by that task; all are pre-existing, and they are filed together because they are one file and would collide as
separate branches. Ordered by how much they matter:

1. **`.githooks/pre-commit:12` - staged DELETIONS bypass every check.** `git diff --cached --name-only
   --diff-filter=ACMR` omits `D`, so the CRLF check, the secret check and the `touches:` check all skip a
   deleted path entirely. Reproduced: `git rm --cached README.md` on a branch whose task has narrow `touches:`
   → `EXIT=0`. Deleting a file someone else's task owns is exactly the "two agents, one file, last write wins"
   failure CLAUDE.md is built around, and the hook currently permits it silently.
2. **`.githooks/pre-commit:40` - an empty or missing `touches:` fails OPEN.** `if [[ -n "$allowed" ]]` means
   `touches: []`, or a task file with no `touches:` key at all, allows every path. A task that forgot to
   declare what it touches gets less enforcement than one that declared it, which is backwards.
3. **`.githooks/pre-commit:45` - the match is a bare prefix with no path boundary.** `[[ "$f" == "$a"* ]]`, so
   `touches: [ops/test]` allows `ops/testing-decoy.md`. Reproduced.
4. **`.githooks/pre-commit:36` - `ls a b c | head -1` picks alphabetically, not by recency.** With the same
   task id present in two directories at once, `claimed` < `done` < `review` decides, so the stale or wider
   copy governs. `ops/queue-check` calls that state a duplicate, but the hook runs first.
5. **`.githooks/pre-commit:36` - `queue/blocked/` and `queue/backlog/` are still unenforced.** Same bug class
   T-0039 just fixed for `done/`; `ops/lib/queue.py` shows `blocked` is reachable from `claimed` with the
   branch and worktree still live. T-0039's brief named only `done/`, so this was correctly left alone there.

Also checked and ruled SAFE by reviewer-24, so do not "fix" it: a task id that is a prefix of another
(`T-9203` vs `T-92030`). The `<id>-<slug>.md` naming means the hyphen sorts before a digit, so the exact match
wins.

- Demonstrate each of the five red before fixing and green after, individually. Five fixes in one commit with
  one demonstration is four unverified changes.
- Deletions especially: decide what the CRLF and secret checks should even do for a deleted path (nothing to
  read), and make sure adding `D` does not make them fail on every deletion.
- T-0047 also edits this file and is in review. Land whichever lands first, then rebase the other.

## Log
- 2026-09-07T21:35:28Z claimed by agent/unknown; lease until 2026-09-07T23:35:28Z

- 2026-09-08T02:05Z claimed and fixed by agent/claude-opus-5, stacked on task/T-0051 (in review), which is
  the other live edit to this file. The brief said to land whichever came first and rebase the other; T-0051
  came first, so this stacks on it and the chain stays linear: T-0047 -> T-0051 -> T-0048.

  All five holes fixed, and EACH demonstrated red individually against the previous hook, in a throwaway git
  repo under .artifacts/ so nothing could touch the real queue or index. The brief was explicit that five
  fixes with one demonstration is four unverified changes.

      HOLE 1  staged deletion of README.md, touches: [ops/test]
              OLD  EXIT=0                       NEW  README.md is outside T-0900 touches: [ops/test]
      HOLE 2a touches: []
              OLD  EXIT=0                       NEW  services/etl/thing.py is outside ... touches: []
      HOLE 2b no touches: key at all
              OLD  EXIT=0                       NEW  has no touches: key, so nothing can be checked
      HOLE 3  touches: [ops/test], staged ops/testing-decoy.md
              OLD  EXIT=0                       NEW  ops/testing-decoy.md is outside ...
      HOLE 4  same id in claimed/ AND done/
              OLD  EXIT=0                       NEW  exists in more than one queue directory
      HOLE 5a task in queue/blocked/
              OLD  EXIT=0                       NEW  enforced
      HOLE 5b task in queue/backlog/
              OLD  EXIT=0                       NEW  enforced

  **My first version of the HOLE 4 demonstration proved less than it looked like it proved**, and it is the
  same species of error as the bug. I put the NARROW list in `claimed/`, and since `ls | head -1` sorts
  `claimed` before `done`, the arbitrary pick happened to REFUSE - the old hook came back EXIT=1 and the case
  looked handled. The dangerous direction is the opposite: put the WIDE list in `claimed/` and the old hook
  silently governs by it and lets the commit through, EXIT=0. Re-run that way, which is what the table above
  reports. A red demo that fires for the wrong reason is not a red demo.

  **What each fix is, and the judgement in it:**

  1. TWO file lists rather than one. `staged_files` (ACMR) for the checks that read bytes - a deleted path has
     none, and `git show ":$f"` on one is an error, not a finding - and `staged_paths` (ACMRD) for the
     `touches:` check, because ownership is a question about the path, not its contents. Check 4
     (staged-vs-working-tree) keeps ACMR and its existing comment already said deletions are out of scope by
     construction, which is still true.
  2. FAIL CLOSED on a missing `touches:` key. `touches: []` is now a real declaration meaning "nothing outside
     queue/", which is correct for a queue-only task and costs it nothing; an ABSENT key is refused with a
     different message, because forgetting to declare should not buy more freedom than declaring.
  3. Exact path or genuinely under it: `[[ "$f" == "$a" || "$f" == "${a%/}/"* ]]`. The `${a%/}/` form
     normalises `services/etl` and `services/etl/` to one rule.
  4. REFUSE on a duplicate rather than picking one. The hook cannot know which copy is authoritative, and
     `ops/queue-check` - which does report duplicates - runs after it.
  5. `blocked/` and `backlog/` added to the search.

  **One thing I changed that the brief did not ask for, and it is load-bearing.** The lookup was
  `queue/<dir>/"$task"*.md`; it is now `<task>-*.md` or `<task>.md`. reviewer-24 ruled the prefix case
  (T-9203 vs T-92030) safe, and it WAS safe under `ls | head -1` because the hyphen sorts before a digit. It
  stops being safe the moment the hook refuses on multiple matches: a bare prefix would make two unrelated
  coexisting tasks look like a duplicate and block both. Demonstrated: T-0900 alongside T-09000 -> EXIT=0, no
  duplicate reported. Fixing one thing broke the reasoning behind another, and only re-testing the case the
  brief had ruled safe caught it.

  **Three regression checks, because four of these five fixes make the hook STRICTER** and the way that goes
  wrong is refusing legitimate commits:

      in-scope edit under a directory touches: entry ....... EXIT=0
      a commit that ONLY deletes, in scope ................. EXIT=0
      T-0900 coexisting with T-09000 ....................... EXIT=0

  The middle one also covers a real risk of fix 1: with a deletion-only commit, `staged_files` is empty, and
  `"${arr[@]}"` on an empty array under `set -u` errors on bash before 4.4. It passes here on bash 5.3.9, and
  the reviewer should decide whether the repo wants to assert a minimum bash version rather than rely on it.

  **Verification:** `ops/test` -> `TESTS linux=50/50 ios=skipped failed=0 skipped=0` / `OK`; `ops/check-pins`
  -> `PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux` (9 not 10 because this chain is based on
  task/T-0047, which predates a later pin on main - same as T-0051, not a regression); `ops/queue-check` ->
  `QUEUE OK (44 tasks)`. The demo scripts are deliberately not committed. GitHub Actions is DISABLED
  repo-wide (T-0053), so there is no CI signal at all.

  **What to attack.** Fix 2 makes an absent `touches:` key refuse EVERY commit on that branch, including the
  one that would add the key - the escape hatch is that `queue/*` is always allowed, so the task file itself
  can still be committed, but nothing else can. Check that is actually true rather than taking my word.
  Fix 4 refuses instead of choosing, which means a duplicate now blocks all work on that branch until
  someone resolves it; that is what I want and it is a judgement. And the hook still does nothing at all when
  no task file exists for the branch, which is the sixth hole nobody has filed - a branch named
  `task/T-9999` with no such task commits anything it likes.
