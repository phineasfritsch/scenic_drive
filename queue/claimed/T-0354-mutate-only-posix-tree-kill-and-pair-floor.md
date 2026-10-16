---
id: T-0354
title: check-mutate-only's POSIX process-group tree kill is seen red then green on Linux CI, and PAIR_FLOOR is raised to the measured merged-head count
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-15T23:39:57Z
lease_expires_at: 2026-10-16T23:39:57Z
worktree: .worktrees/T-0354
branch: task/T-0354
exclusive: []
touches: [ops/lib/check-mutate-only.py, ops/lib/mutate_only_pairs.py, ops/lib/tree-kill-demo.py]
pins_affected: [P-PROC-06]
reviewer: null
depends_on: [T-0353]
verify: [ops/check-pins]
acceptance:
  - "A1 MEASURED: bare `python ops/lib/check-mutate-only.py` on the merged head exits 0 and prints `NAME-PAIRS OK: 201117 pair tokens over 44 id populations` (measured 2026-10-15 on 97299cc5 = origin/main), and ops/lib/mutate_only_pairs.py carries the literal `PAIR_FLOOR = 201117`"
  - "A2 FLOOR RED: with PAIR_FLOOR = 201118 (one above the measured count, i.e. the count one below the floor) the same bare run exits 2 with `NAME-PAIRS FAILED: 201117 pair tokens ... floor 201118 tokens`; restored byte-identical, it exits 0"
  - "A3 POSIX GREEN: `python3 ops/lib/tree-kill-demo.py` in python:3.12-slim (WSL docker, --init) calls the SHIPPED check-mutate-only.py run_tree() with a 3 s timeout on a parent with a 60 s sleeping grandchild sharing its stdout pipe, and exits 0 with `kill: killpg <pid> SIGKILL` and `GRANDCHILD KILLED (shipped)`"
  - "A4 POSIX RED: the same demo on the shipped text with one mutant applied (each anchor occurring exactly once) exits 1 with `GRANDCHILD SURVIVED`: `--mutant direct-child` (os.killpg -> os.kill: only the direct child dies) and `--mutant no-session` (start_new_session dropped: killpg names no group); both runs also show the output pipe still held after the 30 s drain"
  - "A5 gates on the merged head, each run bare: check-mutate-only, check-mutate-population, check-exec-bits, check-pins-yaml, queue-check exit 0; ops/lib/tree-kill-demo.py is 100644 like every ops/lib/*.py (P-OPS-01) and every touched file stays under the 300-line cap"
---
## Brief

rv2-t0353 recordables (a) and (b), PR #239, filed per the two-round rule. (a) run_tree()/kill_tree() kill a timed-out
probe's whole tree: the Windows `taskkill /T /F` branch was seen red on HEAD's probe_once and green after, but the
POSIX branch (start_new_session + os.killpg SIGKILL) has never run - this box is Windows. Demonstrate it red/green
where it runs (a Linux CI job step or the swift:6.1-noble docker via WSL, no git in WSL) with the same
parent-plus-sleeping-grandchild demo. (b) PAIR_FLOOR = 192168 is the pre-merge measurement; the merged head counts
195379 pair tokens. Re-measure on today's head and set the literal floor to it.

## Log
- 2026-10-10T03:20:00Z filed by agent/claude-opus-5 (orchestrator) from rv2-t0353 recordables (a), (b).
- 2026-10-15T23:39:57Z claimed by agent/claude-opus-5; lease until 2026-10-16T23:39:57Z
- 2026-10-15T23:55:13Z MEASURED (b) on 97299cc5 (HEAD == origin/main after `git fetch origin`), bare run 23:50:13Z-23:55:13Z, exit 0:
  `MUTATE-ONLY OK: 219 of 219 driver runs refused with exit 64 (59 drivers, 101 range probes: 23 digit, 42 name, 36 N-(N+1))`
  `NAME-PAIRS OK: 201117 pair tokens over 44 id populations, each refused in process by select_only in 4 modes and by onlyIds (0 calls not refused, floor 192168 tokens)`
  (An earlier run at 23:42:20Z exited 1 `TREE CHANGED` because I wrote ops/lib/tree-kill-demo.py into the worktree mid-run - the tree-change guard working as designed, not a driver; it printed no counts.)
- 2026-10-15T23:56:00Z RULINGS (author rule) before code:
  R1 Brief vs reality: the Brief's 195379 was the 2026-10-10 merged head; today's head counts 201117 (more drivers since: 59 vs 55). The literal floor is today's measurement, 201117, re-measured on the final merged head before push; if main moves the count, the floor follows the final measurement and A1 is re-quoted.
  R2 "executable per P-OPS-01": P-OPS-01 (ops/lib/check-exec-bits) holds every ops/lib/*.py at 100644 because each is run as an interpreter argument. The demo is a .py under ops/lib, so it ships 100644 and is run as `python3 ops/lib/tree-kill-demo.py`; marking it 100755 would fail the gate.
  R3 where it runs: WSL docker python:3.12-slim (no git in WSL), not a CI step. CI's Linux runner does run check-mutate-only, but no probe there reaches TIMEOUT_S, so killpg never fires in CI; a CI demo would need a workflow file outside touches. The demo is reusable by anyone on Linux/macOS and refuses (exit 2) off POSIX.
  R4 binding: the demo exec()s the SHIPPED file text (ops/lib/check-mutate-only.py) and calls its run_tree() - the function probe_once() calls in production - with only the timeout argument changed (3 s). Mutants are text replacements on that file whose anchors must each occur exactly once, so a refactor that moves an anchor makes the demo refuse rather than go vacuously green. Survival is judged from /proc/<pid>/stat (absent or Z = dead), since a reparented zombie still answers kill(pid, 0).
  R5 no change to check-mutate-only.py: (a) asks for a demonstration of the shipped POSIX branch, not a fix, and it is green as shipped; touches keeps the path in case review finds otherwise.
- 2026-10-15T23:43:10Z (a) POSIX demo, `wsl -e docker run --rm --init -v <worktree>:/w -w /w python:3.12-slim`, ops/lib/tree-kill-demo.py on the uncommitted draft (same text as committed), shipped check-mutate-only.py of 97299cc5:
  `Python 3.12.14`
  `== tree-kill-demo.py `
  `shipped run_tree: exit None after 3.0s, kill: killpg 10 SIGKILL`
  `shipped output: child 10 started grandchild 11`
  `GRANDCHILD KILLED (shipped): pid 11 is gone`
  `EXIT 0`
  `== tree-kill-demo.py --mutant direct-child`
  `mutant direct-child run_tree: exit None after 33.0s, kill: killpg 13 SIGKILL`
  `mutant direct-child output: (the output pipe is still held by a descendant the tree kill missed)`
  `GRANDCHILD SURVIVED (mutant direct-child): pid 14 is still running (state S)`
  `EXIT 1`
  `== tree-kill-demo.py --mutant no-session`
  `mutant no-session run_tree: exit None after 33.0s, kill: killpg 16: no such group`
  `mutant no-session output: (the output pipe is still held by a descendant the tree kill missed)`
  `GRANDCHILD SURVIVED (mutant no-session): pid 17 is still running (state S)`
  `EXIT 1`
  GREEN shipped (exit 0, 3.0 s, grandchild gone); RED on both mutants (exit 1, the grandchild still in state S and the stdout pipe still held after the 30 s drain). The direct-child mutant's kill label still reads `killpg` because only the call was mutated, not the label.
- 2026-10-16T00:06:01Z (b) FLOOR RED on 8921099a + PAIR_FLOOR = 201118 (uncommitted, one above the measured count), bare run 23:58:25Z-00:06:01Z:
  `MUTATE-ONLY OK: 219 of 219 driver runs refused with exit 64 (59 drivers, 101 range probes: 23 digit, 42 name, 36 N-(N+1))`
  `NAME-PAIRS FAILED: 201117 pair tokens over 44 id populations, each refused in process by select_only in 4 modes and by onlyIds (0 calls not refused, floor 201118 tokens)`
  `EXIT 2`
  PAIR_FLOOR then set to the literal 201117; the green run is the A1 run on the final merged head.
