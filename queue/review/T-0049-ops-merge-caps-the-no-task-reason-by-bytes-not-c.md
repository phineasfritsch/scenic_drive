---
id: T-0049
title: ops/merge caps the no-task reason by bytes, not characters, and can split a UTF-8 sequence
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T21:35:40Z
lease_expires_at: 2026-09-07T23:35:40Z
worktree: ../wt/T-0049
branch: task/T-0049
exclusive: []
touches: [ops/merge, ops/lib/check-merge-reason-cap, ops/lib/merge_reason_cap_assert.py, pins/PINS.yaml]
pins_affected: [P-OPS-02]
reviewer: agent/reviewer-39
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/merge:52,60-61` caps the sanitised `--no-task-reason` at "200 characters" using `${#no_task_reason}` and
`${no_task_reason:0:200}`, which count BYTES in this shell even under `LC_CTYPE=C.UTF-8`. agent/reviewer-26
reproduced it while reviewing T-0044: 198 ASCII characters plus two emoji is 200 characters and 206 bytes, so
the truncation lands mid-sequence and splits a 4-byte UTF-8 character - `xxd` shows `41 f0 9f 2e 2e`, with
`f0 9f` orphaned - putting invalid UTF-8 into the audit line.

This does NOT reopen the injection T-0044 closed: every UTF-8 lead and continuation byte is >= 0x80, so no CR,
LF or ESC can ever fall out of a split. It is a data-integrity and documentation-mismatch defect, and the
audit trail is the one thing on that code path that has to be trustworthy.

- Count characters, or truncate on a character boundary, or say "bytes" in the message and the comment. Any of
  the three is defensible; pick one and argue it in the log.
- Demonstrate red with reviewer-26's exact construction (198 ASCII + 2 emoji) and check the bytes with `xxd`
  rather than eyeballing the terminal, which will happily render a mangled sequence as a replacement glyph.
- Confirm the injection defences T-0044 added still hold afterwards: newline, CR, ESC, U+2028, U+0085, and the
  `>>>`/`<<<` delimiters.

## Log
- 2026-09-07T21:35:40Z claimed by agent/claude-opus-5 (session 01SS4jAGs2oyr4Z4Wd8yK82t); lease until 2026-09-07T23:35:40Z.
  Branching from task/T-0044, not main: ops/merge's --no-task-reason handling exists only there (T-0021/T-0022/T-0044
  all have open PRs against ops/merge; `git log --oneline task/T-0021 task/T-0022 task/T-0044 -- ops/merge` puts
  9a18891 on task/T-0044 newest). touches: extended past the seeded [ops/merge] because the fix is being anchored
  on a new pin assertion (P-OPS-02) rather than on a comment - see the decision entry below.
- 2026-09-07T22:06:34Z agent/claude-opus-5: fix + P-OPS-02; state -> review, reviewer agent/reviewer-39.

### Decision: cap by CHARACTERS (option 1 of the three the brief offered)

All three were live. The argument, since the brief asks for one rather than a patch:

**Chosen - count characters.** The cap exists for the reason T-0044 gave it: a giant reason is the mild version
of the forgery attack, burying real gate output instead of faking it. That is a *display* concern, and code
points approximate display width enormously better than bytes do. Under a byte cap, 200 bytes buys an English
operator 200 glyphs, a Japanese one 66, and an emoji one 50. Rationing an audit annotation by the script its
author happens to write in is a data-loss defect of its own, and a worse one than the bug being fixed here,
because it is silent and permanent rather than visible in a hexdump. Counting characters also makes the code
finally mean what the comment and this task's own title already claimed.

**Rejected - cap by bytes, back off to a character boundary.** It fixes the invalid-UTF-8 defect and keeps a
hard byte bound on the line. But that bound protects nothing here: steps 1-3 of the sanitizer already guarantee
the reason is a single line with no control bytes, so extra bytes on that line cost some wrapped terminal rows
and nothing else. It keeps the non-Latin rationing above, and it would force the comment to be reworded to say
"bytes" - trading a documentation mismatch for a worse product. 200 characters of emoji is ~814 bytes on one
line, about 4 wrapped rows at 120 columns; that is nowhere near burying the two gate lines that follow it.

**Rejected - refuse an over-long reason.** The most tempting of the three, and worth stating why not: a
truncated reason is a half-truth on the permanent record, `...[truncated]` says the record is incomplete with
no way to recover the rest, and refusing would keep the audit trail whole. It loses on contract. `ops/merge`
gate 1 currently has exactly one refusal - "this branch names no task and you gave no reason" - and every one
of its refusals is about whether the merge is *safe*. Adding a refusal whose only cause is operator verbosity
turns "your annotation was too long" into "your merge did not happen", at precisely the moment (a revert, a
hotfix) when you least want the tool to stop for a cosmetic reason. An operator who needs more than 200
characters should be writing them in the PR body, which is unbounded and also permanent. Note too that this
option does not dodge the work: deciding "over-long" consistently still requires counting characters, so it
would contain this fix rather than replace it.

**Consequence a reviewer should expect:** reviewer-26's exact construction (198 ASCII + 2 emoji) is exactly 200
characters, so after this change it is **not truncated at all**. That is correct for a character cap, not a
missed case. The truncation-boundary behaviour is demonstrated by the 201- and 250-character cases instead.

Implementation: the cap moved out of `${#s}` / `${s:0:n}` and into a `$PY` filter at the end of the existing
sanitizing pipeline. It had to leave bash: `${#s}` counts bytes with no locale set, and - measured, not assumed
- counts **UTF-16 code units** under `LC_ALL=C.UTF-8` on this Cygwin bash (198 A + 2 emoji reports 202, not
200), so the bug cannot be fixed in the language it lives in. T-0044's four sanitizing steps are untouched; this
is a fifth stage appended after them. Decoding with `errors="replace"` additionally repairs a reason that
arrived from argv as invalid bytes, so the audit line is now always valid UTF-8 whatever the operator types.
Two smaller riders, both consequences of the above rather than scope creep: `$PY` is now checked for emptiness
at the top (it is used earlier than before, and an absent python otherwise surfaces mid-gate as
`"" -c: command not found`, which reads like a gate failure), and if the filter fails the reason comes out
empty and gate 1 refuses - fail-closed.

### RED, against the unfixed ops/merge

`ops/` has no test tier at all (`ops/test` runs swift, vitest and pytest), so the fix is anchored on a new pin,
**P-OPS-02**, whose assertion drives the real `ops/merge` against the committed `ops/lib/gh-stub-for-merge-tests`
and inspects raw stdout bytes. Nothing is anchored on a comment: the inputs are argv, the assertions are on
emitted bytes, and the two anti-vacuity greps are on a `case` arm and an assignment.

Reproduction of reviewer-26's finding through the real script, bytes via `xxd`, not the terminal:

    $ head -1 out.txt | tail -c 24 | xxd
    00000000: 4141 4141 f09f 2e2e 2e5b 7472 756e 6361  AAAA.....[trunca
    00000010: 7465 645d 3c3c 3c0a                      ted]<<<.
    reason bytes: 214 / body bytes: 200 / body is NOT valid UTF-8: unexpected end of data
    last 6 bytes of body: 41 41 41 41 f0 9f

`41 f0 9f 2e 2e` with `f0 9f` orphaned, exactly as filed. The new check, run against that same unfixed script:

    $ bash ops/lib/check-merge-reason-cap ; echo EXIT=$?
    P-OPS-02: ops/merge's --no-task-reason cap is not character-safe:
      at-cap-198A-2emoji: ops/merge emitted invalid UTF-8 (invalid continuation byte at byte 283); bytes around the split: 41 41 41 41 f0 9f 2e 2e
      over-by-1-198A-3emoji: ops/merge emitted invalid UTF-8 (invalid continuation byte at byte 283); bytes around the split: 41 41 41 41 f0 9f 2e 2e
      over-by-1-199A-2han: ops/merge emitted invalid UTF-8 (invalid continuation byte at byte 284); bytes around the split: 41 41 41 41 e6 2e 2e 2e
      wide-250han: ops/merge emitted invalid UTF-8 (invalid continuation byte at byte 283); bytes around the split: a2 e6 bc a2 e6 bc 2e 2e
    EXIT=1

### GREEN, after the fix

    $ bash ops/lib/check-merge-reason-cap ; echo EXIT=$?
    P-OPS-02: ops/merge caps --no-task-reason at 200 characters on a character boundary (8 cases: 4 straddling byte 200, 2 forgery attempts; every override line valid UTF-8 and a single line)
    EXIT=0

Same reviewer-26 input, same `xxd` window, after the fix - both 4-byte sequences now whole, nothing truncated:

    00000000: 4141 4141 4141 4141 4141 4141 f09f 9880  AAAAAAAAAAAA....
    00000010: f09f 9880 3c3c 3c0a                      ....<<<.
    stdout decodes as valid UTF-8 / reason bytes: 206 chars: 200 / truncation marker present: False

### T-0044's injection defences, re-confirmed after the change

Byte-level audit of the override line (not the rendered terminal), all 8 cases exit 0 with stdout = 3 lines and
exactly 1 override line, 0 forged gate lines:

    1 embedded newline    -> collapsed to a space; override-lines=1 forged-gate-lines=0
    2 carriage return     -> collapsed to a space; override-lines=1 forged-gate-lines=0
    3 ESC / ANSI          -> body='why [2J[1;31mRED'; bytes present: none of ESC/U+2028/U+0085/U+202E/CR/LF
    4 U+2028 LINE SEP     -> body='why  FORGED'; U+2028 survives as bytes; still one line
    5 U+0085 NEL          -> body='why \x85FORGED';   U+0085 survives as bytes; still one line
    9 U+202E RLO bidi     -> body='why ‮FORGED'; U+202E survives as bytes; still one line
    6 literal >>> <<<     -> nested, not promoted to a gate line; override-lines=1 forged-gate-lines=0
    7 control-only reason -> treated as empty; MERGE REFUSED, exit=1

Cases 4, 5 and 9 are unchanged from T-0044, which documented surviving non-ASCII format characters as an
accepted residual; my change neither improves nor regresses them, and none of them starts a line. Case 3 was
verified by probing for the byte `0x1b` rather than by reading the screen - an earlier `xxd | grep` probe of
mine gave a false negative because xxd groups bytes in pairs, and I re-did it in python before believing it.

### Mutation testing - what I broke on purpose, and what survived

Every trial restored the file from a pristine copy and asserted sha256 byte-identical afterwards; the harness
aborts if a restore fails. Final `ops/merge` sha256 `ac51e6d0a2e3878f28c0f3432ccc9f80253f9962dbc2564c78c424b0523e98de`,
identical to the pre-mutation snapshot.

    CAUGHT    M1  revert to the byte cap (the original T-0049 defect)
    CAUGHT    M2  byte cap that backs off to a character boundary   -> kept 198 chars, expected 200
    CAUGHT    M3  cap by UTF-16 code units (what Cygwin bash counts) -> kept 199 chars, expected 200
    CAUGHT    M4  off-by-one: >= instead of >
    CAUGHT    M5  cap silently raised to 300
    CAUGHT    M6  drop the ...[truncated] marker
    CAUGHT    M7  drop errors=replace (invalid input bytes echoed back raw)
    CAUGHT    M8  drop the >>> <<< delimiters T-0044 added
    CAUGHT    M9  drop T-0044's newline collapse
    CAUGHT    M10 collapse only LF, leaving CR (T-0044's rejected minimal fix)
    CAUGHT    C1  every case made ASCII-only        -> straddling guard refuses to certify
    CAUGHT    C2  cases array left malformed        -> odd-length guard refuses
    CAUGHT    C4  cases cut from 8 to 5             -> "only 5 case(s) ran, expected at least 6"
    CAUGHT    C3+M1  comparison disabled, byte-cap defect present  -> strict UTF-8 decode still bites
    CAUGHT    C5+M1  strict-decode tooth removed, defect present   -> length comparison still bites
    CAUGHT    C3+M7  comparison disabled, raw invalid bytes echoed
    SURVIVED  C3+C5+M1  BOTH teeth removed, defect present

**Three things survived on the first pass and the check is different because of them. This is the part worth
reading.**

1. **M7 survived.** No case fed argv that was invalid UTF-8 to begin with, so "the audit line is always valid
   UTF-8" was an untested half of the claim - `errors="replace"` could have been deleted and nothing would have
   noticed. Added the `invalid-input-bytes` case (`bad \xf0\x9f end`); M7 is now caught.
2. **M9 was never even runnable on the first pass** (bad anchor), and when fixed it showed that *no case
   contained a line break at all*. The pin claims "always exactly one line" and nothing tested it; T-0044's own
   newline collapse had no automated guard anywhere in the repo, only a manual demonstration in its task log.
   Since T-0049 inserts python into that same pipeline, that is exactly the property this change could break.
   Added two `forgery-` cases carrying a `T-FAKE` sentinel shaped like a real gate-1-pass line; M9 and M10 are
   now caught, and the assertion refuses to run without at least one such case.
3. **M8 caught the defect but destroyed the message.** The failure diagnostic quotes the reason, which is full
   of emoji, and this script's stdout is cp1252 on Windows - so it died with a `UnicodeEncodeError` traceback
   instead of printing what was wrong. Exit code was still non-zero, so a CI-shaped consumer would have been
   fine and a human would have been left guessing. Every message is now ASCII by construction (`ascii()` on the
   one interpolation that can carry the reason) plus `sys.stdout.reconfigure(errors="backslashreplace")` as the
   belt for the braces. This is a bug the mutation found in my own check, not in `ops/merge`.

**The one survivor I am leaving.** `C3+C5+M1`: deleting *both* the content comparison and the strict decode
lets the original defect through. That is honest and expected - those are the two teeth, they are independently
sufficient (either alone catches M1), and no third redundant assertion would make deleting the first two
detectable. It is recorded so the next reader knows the check's teeth are exactly two lines and where they are.

Also fixed while mutating: the driver used to die with `rc.0: No such file or directory` on a malformed cases
array, and the straddling counter mis-counted a short invalid-UTF-8 reason as "straddling the cap".

### Verification (all local - there is NO CI signal)

GitHub Actions is disabled repo-wide because the account's spending limit is exhausted (see
`queue/backlog/T-0053`). Nothing below ran on a runner; every number is from this worktree, and the PR will
show no checks. `ops/merge` gate 2 would refuse this PR for exactly that reason, which is correct behaviour.

    $ bash ops/test
    TESTS linux=50/50 ios=skipped failed=0 skipped=0
    OK
    ($ cd services/api && npm ci  was needed first - node_modules is absent in a fresh worktree)

    $ bash ops/check-pins
    PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux      (was ok=9; P-OPS-02 is the tenth)

    $ bash ops/queue-check
    QUEUE OK (42 tasks)

    $ bash ops/sane
    SANE OK

P-OPS-02 costs ~9s (8 ops/merge runs, parallelised; serial was 10.8s for 5 cases). It is `anchor: artifact`, so
`ops/check-pins --source-only` - the cheap push gate - skips it and only a full `ops/check-pins` pays. Both new
files are committed 100755 via `git update-index --chmod=+x`, per P-OPS-01.

Branch note: stacked on `task/T-0044`, not `main`. `--no-task-reason` exists only there
(`git log --oneline task/T-0021 task/T-0022 task/T-0044 -- ops/merge` puts 9a18891 on task/T-0044 newest), so
the PR targets `task/T-0044` and must merge after it. `pins/PINS.yaml` and `ops/lib/` were added to `touches:`
before being staged.

### What to attack, reviewer

1. **The decision itself.** If you think refusing an over-long reason is right, say so - it is a genuinely
   different product and I argued it down rather than proved it wrong. Same for the byte-cap-with-backoff.
2. **Is 200 code points of emoji actually acceptable on one line?** I claim ~814 bytes / ~4 wrapped rows does
   not bury the two gate lines after it. I did not measure this on a narrow terminal.
3. **`errors="replace"` changes behaviour for input that was never valid UTF-8** - it now silently substitutes
   U+FFFD instead of passing bytes through. I think that is strictly better for an audit line and it cannot
   inject (U+FFFD is not a control character), but it is a behaviour change beyond the brief's letter.
4. **Grapheme clusters are still splittable.** A ZWJ emoji sequence or a stranded combining mark survives as
   valid UTF-8 that renders as a different glyph. Documented as an accepted residual, not fixed. Argue if that
   is the wrong line to draw.
5. **The check's teeth are two lines** (`if got != want` and `out.decode("utf-8")` in
   `merge_reason_cap_assert.py`); `C3+C5+M1` above shows removing both is undetectable. Is that acceptable?
6. **The pin depends on `ops/lib/gh-stub-for-merge-tests`**, which only exists on `task/T-0044`. If T-0044 is
   abandoned rather than merged, P-OPS-02 fails on main. That is a stacking risk, not a code risk, but it is
   real and it is mine.
7. **The forgery cases are arguably T-0044's scope, not T-0049's.** I added them because my change puts python
   into T-0044's pipeline and because the property had no guard anywhere. Push back if that is over-reach.
8. **Re-derive RED independently.** `git stash`-ing my `ops/merge` and running the check should give the four
   invalid-UTF-8 lines above verbatim; if it does not, the check is anchored on something I did not intend.
9. **The `$PY` emptiness guard is new behaviour** (`exit 2` where `ops/merge` previously limped to gate 2). It
   is a rider on this fix, not part of it.
