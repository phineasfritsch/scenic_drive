---
id: T-0044
title: ops/merge --no-task-reason echoes an embedded newline into the audit trail
state: done
owner: agent/builder-7
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T16:38:27Z
lease_expires_at: 2026-09-07T19:38:27Z
worktree: ../wt/T-0044
branch: task/T-0044
exclusive: []
touches: [ops/merge]
pins_affected: []
reviewer: agent/reviewer-26
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Filed by agent/reviewer-20 as a MAJOR finding while reviewing T-0022 (see `queue/done/T-0022-*.md` Log): T-0022
added `ops/merge`'s `--no-task-reason="<why>"` override (gate 1, the branch-names-no-task path) and echoed the
reason to stdout so it lands in the audit trail. The trim at the old `ops/merge:37`
(`sed 's/^[[:space:]]*//;s/[[:space:]]*$//'`) strips leading/trailing whitespace **per line**, not the newlines
themselves, so a reason containing an embedded `\n` survives the emptiness check intact and is echoed raw. A
reason can therefore carry a second "line" shaped exactly like `ops/merge`'s own genuine gate-1-pass line
(`task     T-FAKE is in queue/done/ on <ref>`), and a reader (or future tooling grepping stdout for that shape)
cannot tell the forged line from a real one. This does not change the exit code and bypasses no real check —
what it corrupts is the record of *why* a merge was allowed.

### Decision

Sanitize the reason before both the emptiness check and the echo, then delimit it when echoed, as defense in
depth. Concretely (`ops/merge`, the block right after option parsing):
1. CR/LF/tab collapse to a single space. This is what actually closes the injection: a reason can no longer
   contain a line break, so it can never start a new line, and every gate line `ops/merge` prints is its own
   `echo`, emitted only after a real newline the script produced itself — nothing inside one line's text can
   ever be a second, independent line.
2. Every other ASCII control byte (`\000-\010\013\014\016-\037\177`) is deleted outright. This is what kills
   ANSI escape sequences (ESC is `0x1B`, a control byte, so the escape sequence never reaches the terminal
   intact) — considered per the task's own prompt ("a reason can repaint the terminal").
3. Runs of whitespace collapse to one space, then leading/trailing whitespace is trimmed. This subsumes the
   original "whitespace-only counts as no reason, not a reason" rule, now applied *after* sanitizing rather than
   before it, so a reason that is nothing but control bytes/newlines is also correctly treated as empty (the
   pre-fix code never had to consider this case, since a lone `\n` survived its per-line trim as non-empty).
4. The sanitized result is capped at 200 characters, with a `...[truncated]` suffix if it was longer. Considered
   per the task's own prompt ("a reason long enough to push real output off screen") — a giant reason is a
   milder version of the same attack (burying real gate output instead of forging a fake line for it), so it
   gets the same "operator-supplied text does not get to control the audit trail's shape" treatment.
5. The echoed reason is wrapped in `>>>...<<<` delimiters. Belt-and-suspenders on top of (1)-(4): even if
   sanitizing ever had a gap, text inside explicit delimiters on the *same* line as
   `review gate overridden on record:` cannot be mistaken for a standalone gate line, because a gate line is
   never nested inside another line's delimiters — it is always a whole `echo` of its own.

Alternatives considered and rejected:
- **Only collapsing embedded newlines** (the brief's suggested minimal fix, e.g.
  `no_task_reason="${no_task_reason//$'\n'/ }"`) — rejected as insufficient on its own. It closes the exact
  reproduction reviewer-20 found, but leaves carriage returns (which some terminals treat as a line-restart,
  and which the brief explicitly calls out) and ANSI escapes (terminal repaint / fake coloring) untouched, and
  does nothing about a several-hundred-character reason burying real gate output. The task's own prompt asks to
  weigh all of these, not just the reported repro.
- **Rejecting any reason containing a newline instead of collapsing it** — rejected. It would turn a single
  copy-pasted multi-line justification into a hard refusal instead of accepting the intent and normalizing the
  text, which is worse UX for the legitimate case (a real operator explaining a real no-task merge) for no
  additional safety over collapsing (collapsing already fully removes the line break).
- **Only truncating/escaping for display without deleting control bytes** (e.g. `printf %q` or `cat -v`
  style visible-escaping) — rejected as more complex than necessary here: deleting control bytes outright (after
  converting the three "whitespace-shaped" ones to spaces) is simpler to reason about and to test than a
  visible-escaping scheme, and nothing here needs the original bytes to survive in any form.
- **Full Unicode-aware sanitizing** (stripping bidi overrides, zero-width characters, etc., not just ASCII
  control bytes) — considered per the task's own prompt implicitly (the brief only calls out ASCII controls,
  but a thorough pass should ask about the wider space). Rejected as out of scope: this operates on bytes, not
  code points, so a Unicode format character would survive, but it cannot inject a line break or an ANSI escape
  sequence either way (those both require an ASCII control byte, always stripped) — i.e. it cannot forge a fake
  gate line or repaint the terminal, which is the actual exploit this task closes. Documented as an accepted
  residual limitation in the code comment rather than silently ignored, matching this file's existing
  "HONEST LIMITATION" style.

Gates 2 and 3 (everything from `# --- 2. every check run must have succeeded ---` onward) are untouched — the
fix is confined to the option-parsing/sanitizing block and the single `elif` echo in gate 1. `git diff` proves
this (see Log).

## Log
- 2026-09-07T16:38:27Z claimed by agent/builder-94; lease until 2026-09-07T19:38:27Z
- 2026-09-07T16:40:00Z claimed by agent/builder-7 (session 01SS4jAGs2oyr4Z4Wd8yK82t); continuing from
  agent/builder-94's claim. Read CLAUDE.md, this task file, `ops/merge`, and
  `ops/lib/gh-stub-for-merge-tests`'s header comment (STUB_STATE/STUB_ROLLUP/STUB_FLIP/STUB_COUNT/STUB_HEAD_REF/
  STUB_DONE_NAMES — not modified; only copied, unmodified, to a scratch dir on `PATH` as `gh` to exercise
  `ops/merge`, per the constraint that this file's `touches:` stays `[ops/merge]` since it isn't committed to).
  `touches: [ops/merge]` already covers the fix; not widened.

- 2026-09-07T16:41:00Z **RED — reproduce reviewer-20's injection against the unmodified `ops/merge`.** Stub
  copied to `<scratch>/gh` (chmod +x), placed first on `PATH`. `STUB_HEAD_REF` left at its default
  (`tmp/stub-no-task`, the no-task case). Reason: a real line, a newline, then a line shaped exactly like
  `ops/merge`'s genuine gate-1-pass output (`task     $task is in queue/done/ on $head_ref`, ops/merge:49):
  ```
  $ reason=$'legit maintenance branch\ntask     T-FAKE is in queue/done/ on tmp/stub-no-task'
  $ ops/merge 9 --dry-run --no-task-reason="$reason"
  task     branch tmp/stub-no-task names no task; review gate overridden on record: legit maintenance branch
  task     T-FAKE is in queue/done/ on tmp/stub-no-task
  checks   total=2 pending=0 failed=[none] mergeState=CLEAN
  DRY RUN: every gate passed; would merge pr=9 task=none head=tmp/stub-no-task
  EXIT=0
  ```
  Confirmed: the forged `task     T-FAKE is in queue/done/ on tmp/stub-no-task` line is byte-for-byte the shape
  of a genuine gate-1 pass. Exit code is 0 (dry run, unaffected either way) — the bug corrupts the record, not
  the verdict, exactly as reviewer-20 found.

- 2026-09-07T16:42:00Z **Applied the fix** (see Decision above). `git diff ops/merge`: 2 hunks, both inside
  gate 1 (the sanitizing block right after option parsing, and the `elif` echo). Gate 2 (`# --- 2. every check
  run ...` onward, checks/mergeState/merge logic) and gate 3 (the merge itself) are byte-identical to before —
  confirmed by inspection of the diff, which has no hunk touching or after that marker.

- 2026-09-07T16:43:00Z **GREEN 1 — same injection input, patched `ops/merge`:**
  ```
  $ ops/merge 9 --dry-run --no-task-reason="$reason"
  task     branch tmp/stub-no-task names no task; review gate overridden on record: >>>legit maintenance branch task T-FAKE is in queue/done/ on tmp/stub-no-task<<<
  checks   total=2 pending=0 failed=[none] mergeState=CLEAN
  DRY RUN: every gate passed; would merge pr=9 task=none head=tmp/stub-no-task
  EXIT=0
  ```
  One line, one `echo`. The forged text is confined inside `>>>...<<<` on the same line as
  "review gate overridden on record:" — it can never be read as an independent gate line, because it never
  starts a line of its own.

- 2026-09-07T16:44:00Z **GREEN 2 — legitimate one-line reason still accepted and echoed:**
  ```
  $ ops/merge 9 --dry-run --no-task-reason="queue-only maintenance branch, no code change"
  task     branch tmp/stub-no-task names no task; review gate overridden on record: >>>queue-only maintenance branch, no code change<<<
  checks   total=2 pending=0 failed=[none] mergeState=CLEAN
  DRY RUN: every gate passed; would merge pr=9 task=none head=tmp/stub-no-task
  EXIT=0
  ```

- 2026-09-07T16:45:00Z **GREEN 3 — refusals unchanged:**
  ```
  $ STUB_HEAD_REF="tmp/stub-no-task" ops/merge 9 --dry-run                       # no reason at all
  MERGE REFUSED: branch tmp/stub-no-task names no task (no T-nnnn), so the review gate can't check queue/done/ for it
  ...
  EXIT=1

  $ STUB_HEAD_REF="tmp/stub-no-task" ops/merge 9 --dry-run --no-task-reason=""   # empty reason
  MERGE REFUSED: branch tmp/stub-no-task names no task ...
  EXIT=1

  $ STUB_HEAD_REF="tmp/stub-no-task" ops/merge 9 --dry-run --no-task-reason="   " # whitespace-only reason
  MERGE REFUSED: branch tmp/stub-no-task names no task ...
  EXIT=1

  $ STUB_HEAD_REF="tmp/stub-no-task" ops/merge 9 --dry-run --no-task-reason="$(printf '\n\t\r  \n')"
                                                                                  # control-bytes-only reason -
                                                                                  # NEW case the old per-line trim
                                                                                  # did not correctly refuse
                                                                                  # (a bare \n was "-n" true);
                                                                                  # sanitize-then-trim now treats
                                                                                  # it as empty, correctly
  MERGE REFUSED: branch tmp/stub-no-task names no task ...
  EXIT=1

  $ STUB_HEAD_REF="task/T-0022-something" STUB_DONE_NAMES="T-0022-something.md" ops/merge 9 --dry-run
                                                                                  # normal task/T-XXXX branch,
                                                                                  # task in done/ - unaffected
  task     T-0022 is in queue/done/ on task/T-0022-something
  checks   total=2 pending=0 failed=[none] mergeState=CLEAN
  DRY RUN: every gate passed; would merge pr=9 task=T-0022 head=task/T-0022-something
  EXIT=0

  $ STUB_HEAD_REF="task/T-0022-something" STUB_DONE_NAMES="" ops/merge 9 --dry-run
                                                                                  # normal task branch, task NOT
                                                                                  # in done/ - unaffected
  MERGE REFUSED: T-0022 is not in queue/done/ on task/T-0022-something - a reviewer has not signed it off
  EXIT=1
  ```
  `task="$(...grep -oE 'T-[0-9]{4}'...)"` extraction and the `if [[ -n "$task" ]]` branch (ops/merge:44) are
  unchanged; `$no_task_reason` is never consulted when a task branch is in play, so none of the sanitizing
  logic can affect this path either way.

- 2026-09-07T16:46:00Z **Additional attacks beyond the brief's repro (task's own instruction to try more):**

  5a. Several-hundred-character reason (screen/log-flood attack) — truncated to 200 chars + a `...[truncated]`
  marker:
  ```
  $ longreason="$(printf 'A%.0s' $(seq 1 500))"; echo "input length: ${#longreason}"
  input length: 500
  $ ops/merge 9 --dry-run --no-task-reason="$longreason"
  task     branch tmp/stub-no-task names no task; review gate overridden on record: >>>AAA...AAA...[truncated]<<<
  checks   total=2 pending=0 failed=[none] mergeState=CLEAN
  DRY RUN: every gate passed; would merge pr=9 task=none head=tmp/stub-no-task
  EXIT=0
  ```
  Echoed reason field (delimiters + text + marker) is 221 chars, not 500.

  5b. ANSI escape sequence (terminal repaint attempt) — ESC bytes stripped, sequences reduced to inert text:
  ```
  $ ansi_reason="$(printf 'safe-looking\x1b[2J\x1b[31mFAKE RED TEXT\x1b[0m')"
  $ ops/merge 9 --dry-run --no-task-reason="$ansi_reason" | cat -A   # cat -A to prove no ESC (^[) bytes remain
  task     branch tmp/stub-no-task names no task; review gate overridden on record: >>>safe-looking[2J[31mFAKE RED TEXT[0m<<<$
  checks   total=2 pending=0 failed=[none] mergeState=CLEAN$
  DRY RUN: every gate passed; would merge pr=9 task=none head=tmp/stub-no-task$
  EXIT=0
  ```
  No `^[` in the output; `[2J`, `[31m`, `[0m` survive only as inert printable text.

  5c. Carriage return (line-overwrite attack, called out explicitly in the task prompt) — CR converted to a
  space, output stays 3 real lines (no phantom line, no in-place overwrite of a real gate line):
  ```
  $ cr_reason="$(printf 'real reason\rMERGE REFUSED: not actually refused')"
  $ ops/merge 9 --dry-run --no-task-reason="$cr_reason" | cat -A
  task     branch tmp/stub-no-task names no task; review gate overridden on record: >>>real reason MERGE REFUSED: not actually refused<<<$
  checks   total=2 pending=0 failed=[none] mergeState=CLEAN$
  DRY RUN: every gate passed; would merge pr=9 task=none head=tmp/stub-no-task$
  EXIT=0
  ```
  3 lines total, matching gate count exactly - no extra "MERGE REFUSED" line materializes.

  5d. `$(...)` / backtick command substitution in the reason — confirmed inert, nothing evaluated:
  ```
  $ evil_reason='pwned via $(touch /tmp/PWNED_DOLLAR) and `touch /tmp/PWNED_BACKTICK` and $(rm -rf /)'
  $ ops/merge 9 --dry-run --no-task-reason="$evil_reason"
  task     branch tmp/stub-no-task names no task; review gate overridden on record: >>>pwned via $(touch /tmp/PWNED_DOLLAR) and `touch /tmp/PWNED_BACKTICK` and $(rm -rf /)<<<
  checks   total=2 pending=0 failed=[none] mergeState=CLEAN
  DRY RUN: every gate passed; would merge pr=9 task=none head=tmp/stub-no-task
  EXIT=0
  $ [ -e /tmp/PWNED_DOLLAR ] && echo BAD || echo "PWNED_DOLLAR absent - good"
  PWNED_DOLLAR absent - good
  $ [ -e /tmp/PWNED_BACKTICK ] && echo BAD || echo "PWNED_BACKTICK absent - good"
  PWNED_BACKTICK absent - good
  ```
  Expected and unsurprising (no `eval`/`sh -c` anywhere in `ops/merge`; `$no_task_reason` is only ever used as
  plain data inside `"..."` interpolation), but verified directly rather than assumed, since the task asked for
  it explicitly.

- 2026-09-07T16:47:00Z **Full verification suite, all green** (fresh worktree per T-0040's known gap: `cd
  services/api && npm ci --no-audit --no-fund` first):
  ```
  $ bash ops/check-pins
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
  EXIT: 0

  $ bash ops/queue-check
  QUEUE OK (41 tasks)
  EXIT: 0

  $ (cd services/api && npm ci --no-audit --no-fund)
  added 85 packages in 14s

  $ bash ops/test
  ...
  TESTS linux=50/50 ios=skipped failed=0 skipped=0
  OK
  EXIT: 0
  ```
  `git diff ops/merge` confirmed to have exactly 2 hunks, both strictly before the
  `# --- 2. every check run must have succeeded ---` marker; gate 2/3 source is byte-identical to before this
  change, so this fix adds no path to `gh pr merge` while a check is not SUCCESS.
  `ops/lib/gh-stub-for-merge-tests` was read (its `STUB_FLIP` history/comment block) but not modified — no
  knob touched, nothing weakened. GitHub Actions is not executing on this repo (billing block, per the task
  brief); verified locally throughout, not waited on.

- 2026-09-07T17:05:00Z **REVIEW by agent/reviewer-26 — PASS.** Re-derived everything below independently
  against `ops/lib/gh-stub-for-merge-tests` copied unmodified to a scratch dir on `PATH`; did not take the
  builder's log entries on trust anywhere they could be independently re-run.

  **1. RED re-reproduced against the unmodified pre-fix `ops/merge`** (`git show HEAD~1:ops/merge`, tracked
  file untouched): same injected reason (`legit maintenance branch\n` + a forged
  `task     T-FAKE is in queue/done/ on tmp/stub-no-task` line) produced the forged line byte-for-byte
  matching the genuine gate-1-pass shape, `EXIT=0`. Confirmed the same input against the patched `ops/merge`
  collapses to one delimited line: `... overridden on record: >>>legit maintenance branch task T-FAKE is in
  queue/done/ on tmp/stub-no-task<<<`. Matches the task-file's GREEN 1.

  **2. Bypass attempts, all failed to forge a line (re-derived, not just accepted from the log — the log did
  not cover Unicode separators or the delimiters-in-reason cases, so these are new):**
  - U+2028 LINE SEPARATOR, U+0085 NEL, U+2085 (arbitrary non-ASCII sanity check) embedded mid-reason, followed
    by gate-line-shaped text: all stayed on the single delimited line (`cat -A` confirms no `$` line-end
    appears mid-string, only the multi-byte UTF-8 bytes printed literally as `M-x` sequences). Neither bash nor
    the terminal treats these as line breaks, so this is inert here — consistent with the task-file's stated
    accepted residual limitation ("cannot inject a line break... either way").
  - Reason containing the literal delimiters (`fake close<<< <gate-line-text> >>>fake reopen`): stays on one
    line (`>>>fake close<<< task T-FAKE is in queue/done/ on tmp/stub-no-task >>>fake reopen<<<`) — cosmetically
    confusing (nested-looking delimiters) but never becomes an independent line, and `grep -E '^task
    +T-[0-9A-Z]+ is in queue/done/ on '` against the full output does not match it (verified with an actual
    grep, exit 1) — no false positive for tooling scanning for the genuine shape.
  - Reason = only `>>><<<`: sanitizes to itself unchanged (no control bytes to strip), non-empty, so accepted
    and doubled to `>>>>>><<<<<<`. Cosmetically odd but "judged sensibly" per the task's own bar: it's still one
    line, still unambiguously operator text, no line-boundary exploit.
  - Reason = exactly the gate-1-pass line text with **no** embedded newline at all (`task     T-FAKE is in
    queue/done/ on tmp/stub-no-task`): confirmed via the same grep test above that it never reads as an
    independent line — it's embedded mid-line after `overridden on record: >>>`, never at column 0.
  - `--no-task-reason "text"` as a separate argv element (no `=`): rejected outright — `unknown option:
    --no-task-reason`, `EXIT=2`. This is pre-existing option-parsing behavior (the `case` loop only matches
    `--no-task-reason=*`), unchanged by this diff; not a bypass, just documented.
  - Control-bytes-only reason (`printf '\x01\x02\x1b\x7f'`) and whitespace/newline/tab-only reason: both
    correctly refuse (`MERGE REFUSED: branch ... names no task`, `EXIT=1`) — the emptiness check runs after
    sanitizing, as designed.

  **3. MINOR, non-blocking finding — `ops/merge:52,60-61`: the 200-char cap is byte-based, not
  character-based, despite the code comment and this task's own Decision text calling it "200 characters."**
  `"${#no_task_reason}"` and `"${no_task_reason:0:$no_task_reason_max}"` operate on bytes even though
  `LC_CTYPE=C.UTF-8` is set in this shell. Repro: a reason of 198 ASCII `A`s + 2 emoji (Python-verified
  `len(s)==200` *characters*, 206 *bytes*) truncates at byte 200, mid-emoji: `xxd` shows `... 41 f0 9f 2e 2e
  2e ...` — the 4-byte UTF-8 sequence `f0 9f 98 80` gets cut to a dangling `f0 9f`, i.e. invalid UTF-8 lands in
  the audit-trail line. **This does not reopen the vulnerability this task closes**: every byte in a valid
  UTF-8 multi-byte lead/continuation sequence is ≥ 0x80, so truncating mid-sequence can never produce a CR, LF,
  tab, or ESC (all < 0x80) — no forged gate line or terminal escape is reachable this way, re-derived, not
  assumed. It's a data-integrity gap (invalid UTF-8 written to stdout, which could break a downstream consumer
  that parses the audit trail expecting valid UTF-8, e.g. `jq -R` or a strict decoder) and a doc/comment
  mismatch ("200 characters" vs. actual 200-byte behavior) — not disclosed as an accepted limitation the way
  the ASCII-only-control-byte scope was. Logged per "testers find and do not fix"; not fixed here.

  **4. Re-derived, matching the task-file's claims:** `git diff HEAD~1 -- ops/merge` — exactly 2 hunks
  (`@@ -33,8 +33,33 @@` and `@@ -50,7 +75,10 @@`), both ending before the `# --- 2. every check run must have
  succeeded ---` marker (line 89); gate 2/3 source (lines 89 onward) is untouched. `--no-task-reason` confirmed
  to have zero effect on a task-named branch, both when the task **is** in `queue/done/` (genuine
  `task     T-0022 is in queue/done/ on ...` line printed, no reason echoed at all) and when it is **not**
  (`MERGE REFUSED: T-0022 is not in queue/done/ ...`, reason text never referenced or able to bypass) —
  matches reviewer-20's T-0022 verification, survives this change. `git ls-files -s` confirms `ops/merge` is
  100755; `git diff HEAD~1 HEAD -- ops/lib/gh-stub-for-merge-tests` is empty (byte-identical, still 100755,
  untouched by this branch).

  **5. Also checked (pre-existing gate 2/3 behavior, unmodified by this diff, so out of scope for T-0044 but
  run per the review brief):** a mixed `SUCCESS`+`SKIPPED` rollup with `mergeStateStatus=CLEAN` and a valid
  `--no-task-reason` **did** reach the stub `gh pr merge` and reported `MERGED` (SKIPPED is neither in the
  pending nor the failed conclusion list at `ops/merge`'s gate 2, so it's treated as non-blocking) — this is
  identical pre-existing gate-2 logic (byte-identical per point 4 above), not something this diff introduced or
  could have introduced; noting for the record only, not counted against this task.
  `mergeStateStatus=UNSTABLE` was correctly refused (`MERGE REFUSED: mergeStateStatus=UNSTABLE (want CLEAN)`,
  `EXIT=1`) both with a valid `--no-task-reason` on a no-task branch and with a task branch whose task **is**
  in `queue/done/` — a passing gate 1 never short-circuits gate 2.

  **6. Verification suite, re-run independently, exact output:**
  ```
  $ bash ops/check-pins
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
  EXIT=0

  $ bash ops/queue-check
  QUEUE OK (41 tasks)
  EXIT=0

  $ (cd services/api && npm ci --no-audit --no-fund)
  added 85 packages in 14s

  $ bash ops/test
  ... (all suites pass) ...
  TESTS linux=50/50 ios=skipped failed=0 skipped=0
  OK
  EXIT=0
  ```
  All green, matching the builder's log. GitHub Actions is not executing on this repo (billing block); not
  treated as this diff's problem, per the review brief.

  **Verdict: PASS.** The fix closes the exact reported injection and holds under every additional bypass
  attempted (Unicode separators, literal delimiters in the reason, delimiter-only reason, no-newline
  gate-line-text, split-argv form, control-byte-only/whitespace-only emptiness). Gates 2 and 3 are
  byte-identical and the task-branch path is unaffected. One MINOR non-blocking finding logged above (byte- vs
  character-based truncation can emit invalid UTF-8 into the audit trail on multi-byte input) — does not
  reopen the closed vulnerability, does not block this task; left for a follow-up task rather than fixed here.
