# Work queue

State **is** the directory. One file per task, YAML front matter + markdown body. Every transition is a git commit;
a claim is also a push. Sessions die mid-task — whatever is not in here is gone.

```
queue/backlog/   not ready (missing a dependency or a decision)
queue/ready/     claimable
queue/claimed/   owned, leased; work happens in the task's worktree on branch task/T-XXXX
queue/review/    PR open; reviewer set; reviewer != owner
queue/blocked/   cannot finish; says why in ## Log
queue/done/      merged; reviewer moved it here
queue/LOCKS/     one file per exclusive resource: "<task-id> <owner> <iso-time>"
```

## Protocol (mechanical — `ops/queue-check` exits non-zero on violations)

1. **Preflight**: `ops/agent-preflight && ops/queue-sweep && ops/queue-check`.
2. **Pick**: `ops/queue-next` prints the next `ready/` task whose `depends_on` are all `done/`.
3. **Claim**: `ops/claim T-0007 --owner agent/<name> --session <id> --hours 2` moves it to `claimed/`, sets the
   lease, and creates `LOCKS/<resource>.lock` for each `exclusive:` entry. Then
   `git add queue/ && git commit -m "claim T-0007" && git push`. **A rejected push means someone else claimed it:
   `git reset --hard origin/main` and pick another.** Push-to-claim is the compare-and-swap; git is the lock.
4. **Work** in `git worktree add .worktrees/T-0007 -b task/T-0007`, touching only the paths in `touches:`
   (`.githooks/pre-commit` enforces this). Stage explicit paths. Never `git add -A`.
   If you add a resource to `exclusive:` **after** claiming, `claim` never saw it and no lock exists — run
   `ops/lock T-0007 --owner agent/<you>` to acquire it. It refuses if another task holds the lock, and
   `ops/queue-check` fails until it is held. (The T-0011 case: the lock is what prevents a concurrent write, so
   acquiring it late beats never, but declaring it before you claim beats both.)
5. **Verify** with every command in `verify:`; paste the output into `## Log`, including the **red** run that proves
   the new check can fail. Green that has never been red is untested.
6. **Review**: open a PR, set `reviewer:` to someone who is not you, `git mv` the file to `review/`. The reviewer
   has no write access to `Sources/`; they run `verify:`, read the artifact (not just the diff), and either move the
   task to `done/` or back to `claimed/` with a `## Log` line saying what is wrong.
7. **Merge with `ops/merge <pr>`**, never `gh pr merge`. It refuses unless the branch names a task and that task
   is in `done/` on the PR head, every check has concluded green, `mergeStateStatus` is CLEAN, and CI actually
   reported. A branch with no `T-nnnn` in its name is refused too — not skipped — unless you pass
   `--no-task-reason="<why>"`, which overrides the queue/done check on the record with that reason (for a
   `queue:`-only maintenance branch, a revert, or a hotfix with no task yet). `--wait` polls; `--dry-run` reports
   the verdict without merging. On 2026-09-07 `main` was broken by merging a PR that `gh` reported as UNSTABLE;
   GitHub-side branch protection would stop that but is 403 on a private free-plan repo ("Upgrade to GitHub Pro
   or make this repository public"). This gate is client-side and therefore bypassable — it makes the safe path
   the easy path, nothing more.
8. **Demos that need a commit** (hook red/green, floor guard) run in a SEPARATE worktree:
   `git worktree add .worktrees/demo-<task> -b tmp/demo-<task>` ... `git worktree remove --force .worktrees/demo-<task>`.
   Never on the main checkout, never `git commit -a`, never `git stash`/`git restore`/`git clean` there. On 2026-09-07 a
   throwaway-branch `commit -a` in the main checkout swept a modified `.gitattributes` into the demo commit and the
   checkout back to main silently reverted it.
9. **Crash recovery**: `ops/queue-sweep` returns tasks whose `lease_expires_at` has passed to `ready/` and releases
   their locks. Run it first thing every session and on a cron.

   **An expired lease is not abandoned work, and the sweeper is the one command here that destroys state** —
   it sets `owner: null`, the state `ops/review` then refuses as undecidable, and leaves `main` saying
   `ready/<id>` while the branch says `review/`. On 2026-09-15 **all 67** claimed tasks had an expired lease
   and **39 had an open PR**. So it sweeps a task only when that task **never named a branch**:

   | state of `branch:` | sweeper |
   |---|---|
   | ref found (`origin/<branch>` or local) | **kept** — finished work waiting to merge |
   | named, but no ref in this checkout | **kept** — it does no fetch, so "I cannot see it" is not "it does not exist" |
   | `null` / absent | **swept** to `ready/`, locks released |
   | git cannot read the repo | **refuses**, exit 2, moves nothing |

   Leases are 2–4 hours and the work is routinely longer, so expiry mostly measures the wrong thing; the
   branch is the evidence that matters. `ops/lib/check-sweep.py` asserts all four rows — pin P-PROC-03 runs
   the cases, P-PROC-04 runs `--variants`, which is what proves the cases can fail — and it reads what the
   sweeper *said* about that task, not only where the file ended up. Four of its seven cases are must-KEEP
   (1, 2, 6, 7) and each asserts the sentence naming its own branch, which is printed only when that task
   was considered; case 4 (an unexpired lease) asserts the summary line instead, because the sweeper says
   nothing per task about a lease that has not expired. A sweeper that exits non-zero before its loop fails
   every case on exit code; one that exits 0 without looping fails 1, 2, 3, 6 and 7 and passes 4 and 5. The **locks released** clause of row 3 is
   the one part no case covers, because every fixture task declares `exclusive: []`.

   **A kept task keeps its locks, and that is the cost of the rule above.** Sweeping is what used to release
   an `exclusive:` lock, so a task that names a branch now holds `scenic-index` or `prod` until somebody
   moves it — and `ops/queue-check` reports an orphaned lock as an error for *every* agent in *every*
   worktree, not just its owner's. That is deliberate: a stuck lock is recoverable, 39 discarded branches are
   not. Two things release it, and neither needs the original owner: `ops/review <id> --reviewer agent/<name>`
   (which releases the task's own locks as it moves it), or deleting `queue/LOCKS/<resource>.lock` by hand
   once you have checked what holds it.

   **A finished task whose owner is gone is not stuck**: `ops/review <id> --reviewer agent/<name>` makes the
   `claimed → review` transition from any session. It is not the owner's private door — it checks that the
   owner exists and is comparable, that `reviewer != owner`, and that merging the branch would not duplicate
   the task file, then releases the `exclusive:` locks. What it cannot check is that the reviewer is not the
   *same session* under another name; `owner_session:` is recorded and compared by nothing (T-0131 item 3).

## Exclusive resources (declare in `exclusive:` before touching)

`package-swift` (either Package.swift) · `pbxproj` · `spm-resolve` (Package.resolved) · `ios-simulator` ·
`routing-profiles` (services/routing/profiles, config.yml) · `scenic-index` (ETL, graph import, tiles, corpus publish) ·
`curated` (curated.yaml) · `floors` (pins/floor_*.txt) · `prod` (deploys, publishes, ASC build number, device builds).

## ETL inputs live in ONE directory, outside `.worktrees/`

`services/etl/etl/fetch.py` used to put the fetched payloads in `<this checkout>/services/etl/inputs`, so every
worktree had its own copy and `git worktree remove --force` deleted it. T-0169 fetched and verified the California
extract into `.worktrees/T-0169/services/etl/inputs/` and lost it the hour PR #99 merged; the payloads are
gitignored, so git could not give them back. `fetch.resolve_inputs_dir` decides the directory now:

| where you are | inputs directory |
|---|---|
| `SCENIC_ETL_INPUTS` set (any checkout) | that path, verbatim |
| `<root>/.worktrees/<name>/services/etl` | `<root>/services/etl/inputs` — the **main checkout's** |
| a plain checkout | its own `services/etl/inputs` |

Not a symlink farm: nothing is created or linked, the resolver only computes a path. Both are gitignored
(`.gitignore`: `services/etl/inputs/*`), so a payload that lands in the main checkout never shows up in
`git status` there. Only the payloads are shared — `manifest.yaml` is tracked and stays in **your** checkout, so
a task that edits its own manifest fetches against that edit.

`ops/etl-fetch-inputs --verify-only` prints `inputs directory: <path>` as its first line, then, for each input
that is on disk and passes, `verified NAME bytes=N retrieved=DATE MODE ok`; an input that is absent prints
`not on disk at <path>` and the run exits 1. That run is the acceptance for any task that consumes an input:
quote the line, do not re-download. It never downloads and never deletes.

Still per-worktree: `etl/extract.py`, `etl/dem.py`, `etl/landcover.py` and `etl/oracle.py` each compute their own
`ROOT / "inputs"`, and `ops/etl-extract` execs `etl.extract` inside the current checkout. `SCENIC_ETL_INPUTS`
reaches `etl.fetch` only. Until those modules move to the resolver, name the shared copy on the command line —
`ops/etl-extract --input <main checkout>/services/etl/inputs/california-osm.pbf`.

## Task file

See `_schema/task.md`. `touches:` is a flow list of path prefixes. `acceptance:` is the list of demonstrations the
reviewer will re-run. `## Log` is append-only.
