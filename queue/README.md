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
4. **Work** in `git worktree add ../wt/T-0007 -b task/T-0007`, touching only the paths in `touches:`
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
   `git worktree add ../wt/demo-<task> -b tmp/demo-<task>` ... `git worktree remove --force ../wt/demo-<task>`.
   Never on the main checkout, never `git commit -a`, never `git stash`/`git restore`/`git clean` there. On 2026-09-07 a
   throwaway-branch `commit -a` in the main checkout swept a modified `.gitattributes` into the demo commit and the
   checkout back to main silently reverted it.
9. **Crash recovery**: `ops/queue-sweep` returns tasks whose `lease_expires_at` has passed to `ready/` and releases
   their locks. Run it first thing every session and on a cron.

## Exclusive resources (declare in `exclusive:` before touching)

`package-swift` (either Package.swift) · `pbxproj` · `spm-resolve` (Package.resolved) · `ios-simulator` ·
`routing-profiles` (services/routing/profiles, config.yml) · `scenic-index` (ETL, graph import, tiles, corpus publish) ·
`curated` (curated.yaml) · `floors` (pins/floor_*.txt) · `prod` (deploys, publishes, ASC build number, device builds).

## Task file

See `_schema/task.md`. `touches:` is a flow list of path prefixes. `acceptance:` is the list of demonstrations the
reviewer will re-run. `## Log` is append-only.
