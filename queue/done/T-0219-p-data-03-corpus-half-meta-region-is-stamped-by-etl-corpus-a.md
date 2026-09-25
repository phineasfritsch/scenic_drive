---
id: T-0219
title: P-DATA-03 corpus half - meta.region is stamped by etl.corpus and read back by nothing: the reader against the active region, in the same shape as the tiles half (check-pmtiles-provenance.py), red first
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T21:05:25Z
lease_expires_at: 2026-09-20T02:05:25Z
worktree: .worktrees/T-0219
branch: task/T-0219
exclusive: []
touches: [ops/lib/, services/etl/etl/, services/etl/tests/, pins/PINS.yaml]
pins_affected: [P-DATA-03]
reviewer: agent/rv1-pr126
depends_on: [T-0197]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/lib/check-corpus-provenance.py (100644, python; the shape of ops/lib/check-pmtiles-provenance.py): in-process fixtures built by the SHIPPING corpus.build - meta.region == the active region passes; region 'bay' refused by name; region key ABSENT refused naming 'meta.region is None'; built_at older than 30 days refused (P-DATA-03's second clause) - each RED first with the mutant in the shipping checker, then green; SCENIC_LA_CORPUS=<path> adds the real artefact when set (this box: the T-0206 union corpus under services/etl/work/t0206/) and says so when not"
  - "P-DATA-03's pin text loses the 'UNASSERTED and UNOWNED' sentence and names both halves' checks; bash ops/check-pins --source-only bare; check-exec-bits, check-line-cap, queue-check bare"
---
## Brief

rv1/rv2-pr119 (T-0197) both recorded it: etl.corpus stamps meta.region (services/etl/etl/corpus.py, writer.set_meta)
and nothing reads it back against the active region; T-0205 merged as #116 writing meta.surface_coverage instead.
The tiles half of P-DATA-03 is asserted by check-pmtiles-provenance.py since #119; this is the other half.

## Log
- 2026-09-19T16:59:37Z filed by agent/claude-fable-5-1 (orchestrator, from rv1/rv2-pr119's recordables on T-0197). Not started; a harness chore, after #119.
- 2026-09-19T21:05:25Z claimed by agent/claude-opus-5; lease until 2026-09-20T02:05:25Z
- 2026-09-19T21:05:26Z PROMOTED and claimed by agent/claude-fable-5-1 (orchestrator): the 13:13 panel ranked it the next start when #123 merged (#122 landed, its collision gone). T-0208 is live on services/etl/etl/ - this task ADDS files (a check under ops/lib, a test) and edits only the P-DATA-03 text in pins/PINS.yaml; fetch+merge main last. The real artefacts on this box: services/etl/work/t0206/la-union-corpus.sqlite (19,906,560 B, meta.region=la) and window-corpus.sqlite; the shipping stamp is corpus.py:85 'region = region or extract_region' -> writer.set_meta.
- 2026-09-19T21:13:26Z RULINGS by agent/claude-opus-5 (owner), before any code. Every disagreement between the
  filed acceptance, the tiles half and the tree, ruled here.

  R1 WHERE THE CHECKER LIVES, AND WHICH READER IT READS THROUGH. `ops/lib/check-corpus-provenance.py`, 100644,
  python - NOT `services/etl/etl/check_corpus.py`. Measured, not assumed: `MODULE_ROOTS` in
  ops/lib/check-mutate-population.py is `(("services/etl/etl", ".py", True), ("Sources", ".swift", True))`, so
  any .py added under services/etl/etl/ is an ADDED module P-PROC-06 refuses by name unless it ships a
  population under ops/mutate/ or buys an allowlist entry; ops/lib is outside both roots. Shape difference from
  the tiles half, stated rather than implied: check-pmtiles-provenance.py is a HARNESS that subprocesses a
  pre-existing shipping checker (services/tiles/check_pmtiles.py, build-la.sh step 6). No corpus checker exists
  to subprocess - that absence IS the defect - so this one file is BOTH, and the pin's command
  `python ops/lib/check-corpus-provenance.py` is the shipping entry point the pytest binds to.
  THE READER: plain sqlite3 over the meta table, opened READ-ONLY (`file:<quoted posix path>?mode=ro`), which
  is the read shape the shipping code already uses - surfacecoverage.py:199 and corpusmatch.py:66 both spell
  `SELECT value FROM meta WHERE key = ?`. NOT CorpusWriter: it has no read path at all (set_meta only), and
  `CorpusWriter.__init__` does `os.remove(self.path)` on an existing file, so "reading the union corpus through
  corpuswriter" would DELETE 19,906,560 bytes of irreplaceable real artefact. Read-only is enforced by sqlite
  and measured here on this box: an INSERT through the handle raises `OperationalError: attempt to write a
  readonly database`. A provenance check must never be able to mutate the artefact it judges.

  R2 FIXTURES. Built IN-PROCESS by the SHIPPING `corpus.build` over services/etl/tests/fixtures/corpus_extract.json
  (7 ways / 79 segments), which is the path test_corpus_budget.py already uses; `region=` is passed so the stamp
  goes through corpus.py:85 `region = region or extract_region` -> `writer.set_meta("region", region)`. NOT
  committed: a committed corpus carries a frozen built_at that goes stale in thirty days and turns the age limb
  into a calendar (the tiles half's own reason). An ABSENT meta key cannot be built - CorpusWriter.finalize
  refuses a corpus missing any REQUIRED_META_KEY (schema.py:219, which lists both region and built_at) - so the
  two absent-key fixtures are built by the shipping build and then have that ONE meta row DELETED through
  sqlite. Said plainly: the alternative is a second writer, which would no longer be the shipping stamp.

  R3 THE ACTIVE REGION. `--region la` names a DIRECTORY under services/etl/regions/ and the expected value is
  READ from that directory's region.json `"id"`, never typed - the same move check_pmtiles.py main() makes
  (`region["id"]`). NOT the corpus's own manifest or its own meta: a corpus that supplies the expectation it is
  judged against can never fail, which is exactly the failure P-DATA-03 states. Default `la` because
  services/etl/regions/la/region.json is the active region (the owner's region; regions/sfbay is the CI golden
  set). P-DATA-03's text says "meta.region equal to the active region", and this is the only reading of
  "active" that lives outside the artefact.

  R4 THE PIN TEXT. P-DATA-03 loses the "UNASSERTED and UNOWNED" sentence and the "no open task owns it"
  paragraph, names BOTH halves' checks and both commands, and its assertion runs both. No `pending:` key:
  pins.py:126-139 `continue`s past a pending pin, skipping its assertion entirely, which would switch the tiles
  half OFF. ids stay unique (pins.py:113 refuses a duplicate).

  R5 P-PROC-06. No module is added under services/etl/etl/ or Sources/ by this task, so no ops/mutate/
  population and no allowlist entry is due. The mutation evidence lives where the pin can run it instead: the
  checker's own `--prove-red` table.

  R6 FIXTURE COUNT - THE FILED ACCEPTANCE IS ONE SHORT, AND I AM NOT SHRINKING THE CHECK TO MATCH IT. The
  acceptance parenthetical says "four fixtures" and the brief's R2 enumerates four (fresh / 40 days / 'bay' /
  region absent), but R1 of the same brief names FOUR refusals including "built_at absent", and BUILD names a
  mutant "the absent built_at treated as fresh". That mutant SURVIVES any population that never omits built_at:
  with no fifth fixture the prove-red row would be unfalsifiable. Ruled: a fifth fixture, built_at row deleted.

  R7 ONE LIMB NOBODY FILED, TAKEN FROM THE TILES HALF'S OWN RECORDED ROUND. rv1-pr109 R1 is in check_pmtiles.py
  in as many words: "The age limb was one-sided, so built_at in 2099 passed it." The corpus limb is MORE
  exposed, not less - corpus.py:179 makes `--built-at` a REQUIRED operator-typed argument ("An INPUT: no clock
  is read"), so a mistyped year is reachable by hand, not only by a bad host clock. A sixth fixture stamped two
  days ahead and a fifth mutant (the future limb deleted). Consequence carried honestly: the run prints SIX
  fixtures and FIVE mutants, and the final acceptance block is re-quoted with those true counts, not with the
  filed "four".

  R8 `ops/check-pins --source-only` DOES NOT RUN P-DATA-03, AND CANNOT. Its anchor is `artifact`, and
  pins.py:117 skips every pin whose anchor is not `source` under --source-only, before runs_on is ever read. So
  the acceptance's "--source-only (P-DATA-03 now runs the corpus half on linux: quote its line)" is answered in
  two parts rather than with a line that cannot exist: --source-only is run bare (it must stay green, and it
  proves the edited PINS.yaml still parses and no id duplicated), and the corpus half is demonstrated by
  running P-DATA-03's OWN assertion bare, exactly as pins.py would run it - `host_tier()` returns "linux" on
  this Windows box (platform.system() != "Darwin"), so `runs_on: [linux]` does select it under a full
  ops/check-pins, which this task is instructed not to run.
- 2026-09-19T21:36:25Z BUILT, and seen RED BY NAME before green. agent/claude-opus-5.

  R9, ruled during the build and recorded here rather than after the fact: the mutation table does NOT live in
  the checker, it lives in ops/lib/check-corpus-provenance-mutations.py and `--prove-red` runs it. Two
  mechanical reasons, both measured. The checker with the table inside it was 366 lines, then 304 after the
  docstring was cut - over CLAUDE.md's 300-line cap either way (the precedent is check-map-attribution's split
  into -lib and -mutations for exactly this). And a table that QUOTES the code it mutates cannot assert its
  own sites are unique from inside that code: `source.count(old)` counted the table's own copy, and two rows
  share the site `if meta.get("region") != region:`, so the guard that notices a table drifting away from the
  code would have had to be written around itself. From the sibling the guard is plain, and it is armed: a
  site that does not occur exactly once is a FAILURE, not a pass. Split, the checker is 299 lines.

  RED (the record CLAUDE.md asks for: a check never seen red is untested). Five defects, each applied to a
  COPY of the checker, each refused BY NAME - `python ops/lib/check-corpus-provenance.py --prove-red`:
      P-DATA-03 (corpus half): --prove-red 5/5 mutants refused by name:
        the region comparison deleted: exit 1, refused naming "stamped region 'bay'"
        an absent region key defaults to the expected value (T-0197 B4): exit 1, refused naming 'no meta.region at all'
        the 30-day comparison flipped: exit 1, refused naming 'stamped 40 days ago'
        an absent built_at treated as fresh: exit 1, refused naming 'no meta.built_at at all'
        the future-skew limb deleted: exit 1, refused naming 'stamped 2 days in the future'
  R6 AND R7 ARE MEASURED, NOT ARGUED. Both mutants were run against a copy of the checker whose fixture list
  was cut back to the four the acceptance filed, and against the six actually shipped:
      mutant 4 - an absent built_at treated as fresh: over the filed FOUR fixtures -> exit 0 (SURVIVED)
      mutant 5 - the future-skew limb deleted:        over the filed FOUR fixtures -> exit 0 (SURVIVED)
      mutant 4 - an absent built_at treated as fresh: over the shipped SIX fixtures -> exit 1 (caught)
      mutant 5 - the future-skew limb deleted:        over the shipped SIX fixtures -> exit 1 (caught)
  So the fifth and sixth fixtures are not scope creep: without them two of the five prove-red rows would be
  unfalsifiable, and a prove-red table that cannot fail is the thing this repository exists to refuse. (An
  earlier draft of this entry ASSERTED that survival instead of measuring it; the assertion was replaced by
  the run above before the commit, which is the rule, not a favour.)

  GREEN, with the real artefact (the acceptance's real-artefact line):
      P-DATA-03 (corpus half): ops/lib/check-corpus-provenance.py over 6 corpora built in process by etl.corpus.build, against region 'la' read from services/etl/regions/la/region.json:
        a fresh region-la corpus: accepted
        stamped 40 days ago: refused, named 'older than 30 days (P-DATA-03)'
        stamped region 'bay': refused, named "meta.region is 'bay'"
        no meta.region at all: refused, named 'meta.region is None'
        no meta.built_at at all: refused, named 'meta.built_at is missing'
        stamped 2 days in the future: refused, named 'is in the future by more than'
        la-union-corpus.sqlite: accepted - region=la bytes=19906560 built_at=2026-09-18T00:00:00Z
  The real artefact PASSES rather than being refused: its built_at is 2026-09-18T00:00:00Z, one day old today,
  and its region is `la`. Measured read-only off the file, not taken from T-0206's Log. Unset, the same run
  says so in a line of its own; SCENIC_LA_CORPUS naming a file that does not exist is a REFUSAL, demonstrated:
  `SCENIC_LA_CORPUS=/nope/missing.sqlite` exits 1 with "names no file (set and absent is a refusal, never a
  skip)".

  A BOX CONDITION, NOT A FINDING ABOUT THIS CHANGE, recorded because it will bite the reviewer too. Bare, the
  P-DATA-03 assertion fails on this Windows checkout with "P-DATA-03: the tests' PMTiles writer is
  unavailable: No module named 'pytest'" - the TILES half, untouched by this task. `command -v python3` here
  resolves to the WindowsApps 3.14 shim (C:/Users/.../pythoncore-3.14-64/python.exe), which has no pytest,
  while `python` is 3.10 with pytest 9.1.1. The assertion's own `${PYTHON:-...}` hook is the documented way
  round it, so every pin run below is `PYTHON=python`. CI runs one interpreter and does not see this.

  THE DELETED-ROW FIXTURES ARE REAL, not a shortcut: `corpus.build` really built all six, and the two
  absent-key ones then lost exactly one meta row through sqlite (R2). `CorpusWriter.finalize` is what forbids
  building them directly - it refuses a corpus missing any REQUIRED_META_KEY, and schema.py lists both
  `region` and `built_at` there.

  ACCEPTANCE, run bare on this tree (re-run and re-quoted at the final pre-review commit, per the author rule):
    1. python ops/lib/check-corpus-provenance.py                          exit 0, 6 fixtures (quoted above)
    2. SCENIC_LA_CORPUS=<t0206/la-union-corpus.sqlite> ... same command    exit 0, real artefact line quoted above
    3. python ops/lib/check-corpus-provenance.py --prove-red              exit 0, 5/5 refused by name
    4. cd services/etl && python -m pytest tests -rs -o addopts=          1312 passed in 215.53s, 0 skipped
    5. PYTHON=python bash ops/check-pins --source-only                    PINS ok=15 skipped=16 pending=1 expired=0 failed=0 tier=linux source-only (exit 0)
    5b. P-DATA-03's own assertion, bare, exactly as pins.py -c runs it    exit 0; the tiles half prints its 4
        verdicts and now ends "This is the TILES half. The corpus half is ops/lib/check-corpus-provenance.py
        (T-0219) ...", the corpus half prints its 6. (R8: --source-only cannot run an `anchor: artifact` pin,
        so this line is the acceptance's "P-DATA-03 now runs the corpus half on linux", honestly.)
    6. python ops/lib/check-mutate-population.py                          P-PROC-06: 76 modules, 26 covered by 12 populations, 27 allowlisted, 0 added by this branch; floor of 25 holds (exit 0)
    7. bash ops/lib/check-line-cap                                        P-SRC-02: 92 Swift files tracked (Sources=29, Tests=42, apps/ios=21), none over 300 lines (exit 0)
    8. bash ops/lib/check-exec-bits                                       P-OPS-01: 87 files, 23 required present, all modes correct (exit 0)
    9. PYTHON=python bash ops/queue-check                                 QUEUE OK (221 tasks) (exit 0)
   10. wc -l on every touched file: 299 ops/lib/check-corpus-provenance.py, 112 ops/lib/check-corpus-provenance-mutations.py,
       148 ops/lib/check-pmtiles-provenance.py, 132 services/etl/tests/test_corpus_provenance.py, 296 pins/PINS.yaml,
       180 queue/claimed/T-0219-....md  (every one under the 300-line cap; the task file is re-measured at
       the final commit, since this entry is itself part of it)
   11. git ls-files -s: both new ops/lib/*.py at 100644, as P-OPS-01 requires of data files there.

  ONE CORRECTION MADE OUTSIDE THE FILED SCOPE, declared: ops/lib/check-pmtiles-provenance.py printed "The
  corpus half is UNASSERTED and UNOWNED ... a task for it still has to be filed" on every run, and its
  docstring said the same. Both became false the moment this checker landed, and a pin whose own output
  contradicts its text is worse than one that says nothing. The paragraph and the printed line now name
  ops/lib/check-corpus-provenance.py. It is inside touches: [ops/lib/] and its four verdicts are unchanged.
- 2026-09-19T21:44:06Z FINAL PRE-REVIEW COMMIT. `git fetch origin && git merge --no-edit origin/main` ran as
  the LAST step before this entry: origin/main was 89753a1 (T-0229 filed, queue/LOCKS/root-package.lock
  added), the merge is 96ad82b, no conflict and nothing of T-0208's on services/etl/etl/ had landed, so both
  sides are kept as they stand. THE WHOLE ACCEPTANCE BLOCK, RE-RUN BARE ON THE MERGED HEAD (author rule; the
  numbers below are from that head, not carried forward from the pre-merge run):
    1. python ops/lib/check-corpus-provenance.py                       exit 0
         P-DATA-03 (corpus half): ... over 6 corpora built in process by etl.corpus.build, against region 'la'
         read from services/etl/regions/la/region.json:
           a fresh region-la corpus: accepted
           stamped 40 days ago: refused, named 'older than 30 days (P-DATA-03)'
           stamped region 'bay': refused, named "meta.region is 'bay'"
           no meta.region at all: refused, named 'meta.region is None'
           no meta.built_at at all: refused, named 'meta.built_at is missing'
           stamped 2 days in the future: refused, named 'is in the future by more than'
           the real artefact was not checked: $SCENIC_LA_CORPUS is unset (a corpus is a build product and does
           not exist in CI)
    2. the same, SCENIC_LA_CORPUS=services/etl/work/t0206/la-union-corpus.sqlite   exit 0
           la-union-corpus.sqlite: accepted - region=la bytes=19906560 built_at=2026-09-18T00:00:00Z
       The real artefact is ACCEPTED, not refused: one day old, region la, both read read-only off the file.
    3. python ops/lib/check-corpus-provenance.py --prove-red           exit 0, 5/5 mutants refused by name
           the region comparison deleted -> "stamped region 'bay'"
           an absent region key defaults to the expected value (T-0197 B4) -> 'no meta.region at all'
           the 30-day comparison flipped -> 'stamped 40 days ago'
           an absent built_at treated as fresh -> 'no meta.built_at at all'
           the future-skew limb deleted -> 'stamped 2 days in the future'
    4. cd services/etl && python -m pytest tests -rs -o addopts=       1312 passed in 83.38s, ZERO skipped
       (__pycache__ purged under services/etl first)
    5. PYTHON=python bash ops/check-pins --source-only                 exit 0
           PINS ok=15 skipped=16 pending=1 expired=0 failed=0 tier=linux source-only
    5b. P-DATA-03's own assertion, bare, exactly as pins.py -c runs it  exit 0, both halves, ending
           the real artefact was not checked: $SCENIC_LA_CORPUS is unset ...
        (R8 stands: --source-only cannot run an `anchor: artifact` pin, so 5 proves PINS.yaml still parses
        with no duplicate id and 5b is where the corpus half is actually seen running on tier=linux.)
    6. python ops/lib/check-mutate-population.py                       exit 0
           P-PROC-06: every added module is covered or allowlisted; the floor of 25 holds
    7. bash ops/lib/check-line-cap   P-SRC-02: 92 Swift files (Sources=29, Tests=42, apps/ios=21), none over 300
    8. bash ops/lib/check-exec-bits  P-OPS-01: 87 files, 23 required present, all modes correct
    9. PYTHON=python bash ops/queue-check                              QUEUE OK (222 tasks)
   10. wc -l, re-measured on the merged head after the (b) correction below: 299
       ops/lib/check-corpus-provenance.py, 122 ops/lib/check-corpus-provenance-mutations.py, 148
       ops/lib/check-pmtiles-provenance.py, 132 services/etl/tests/test_corpus_provenance.py, 296
       pins/PINS.yaml, 238 queue/claimed/T-0219-....md
       (the task file carries this entry; every source file is under the 300-line cap)
   11. git merge-base --is-ancestor origin/main HEAD                   exit 0
  WHAT A REVIEWER SHOULD PROBE FIRST, said plainly rather than left to be found: (a) `_root()` walks parents
  then the cwd - a mutant copy in a temp directory depends on the cwd limb, and a checkout nested inside
  another repo could in principle resolve the wrong root; it fail-closes when neither carries both markers.
  (b) The prove-red table sits in a sibling and the checker's --prove-red only shells to it; a DELETED sibling
  is a refusal (tested by hand). Writing that sentence exposed a real hole and it was CLOSED rather than
  filed, before the push: a sibling whose MUTANTS tuple was emptied printed "0/0 mutants refused by name" and
  exited 0 - a green over nothing, PR #94's shape - because the table had no floor, the one thing every
  ops/mutate/ population carries. `MUTANT_FLOOR = 5` now guards it, seen RED by cutting a copy of the table to
  two rows: "P-DATA-03 (corpus half): --prove-red carries 2 mutants, below the floor of 5. A table that has
  lost rows must never read as 'every mutant refused'." exit 1; and green again at 5/5. P-DATA-03's text
  names the floor. The acceptance block above was re-run after this correction, since it touches two measured
  files: prove-red 5/5 exit 0, pytest 1312 passed 0 skipped, --source-only PINS ok=15 skipped=16 pending=1
  expired=0 failed=0 exit 0, and ops/lib/check-corpus-provenance-mutations.py is now 122 lines, not 112.
  Everything else in the block is unchanged and was re-confirmed at the same head.
- 2026-09-25T19:31:11Z REVIEW PASS by agent/rv1-pr126 (reviewer; not the owner). PR #126, head 450cae3 ==
  origin/task/T-0219, reviewed in a detached sibling worktree (.worktrees/rv1-pr126, removed after). Round 1,
  no round 2: no BLOCKING finding. NO PRE-REVIEW MUTANT PASS RAN on this branch (it died on a model usage
  limit), so this review ran FIVE mutants of its own, one of them a GATE mutant, in place of the missing one.

  DIFF. 6 files, +772/-13: ops/lib/check-corpus-provenance.py (299, new, 100644),
  ops/lib/check-corpus-provenance-mutations.py (122, new, 100644),
  services/etl/tests/test_corpus_provenance.py (132, new), ops/lib/check-pmtiles-provenance.py (+17/-13,
  the declared out-of-scope correction), pins/PINS.yaml (+6/-2), the task file. `git ls-files -s` shows both
  new ops/lib/*.py at 100644, which is what P-OPS-01 requires of data files there.

  GATES, run bare on 450cae3 in this reviewer's worktree, each quoted:
    python ops/lib/check-corpus-provenance.py                 exit 0, all six verdicts printed, ending "the
      real artefact was not checked: $SCENIC_LA_CORPUS is unset"
    SCENIC_LA_CORPUS=<t0206/la-union-corpus.sqlite> same       exit 0, "la-union-corpus.sqlite: accepted -
      region=la bytes=19906560 built_at=2026-09-18T00:00:00Z". THE 30-DAY ARITHMETIC RE-CHECKED AT TODAY'S
      DATE, not the author's: today is 2026-09-25, the stamp is 7 days old, well inside MAX_AGE_DAYS=30, and
      the file is still 19,906,560 bytes after two reads - the read-only URI did not touch it.
    python ops/lib/check-corpus-provenance.py --prove-red      exit 0, "5/5 mutants refused by name", each
      row printing its exit 1 and the fixture it named
    PYTHON=python bash ops/check-pins --source-only            exit 0, PINS ok=15 skipped=16 pending=1
      expired=0 failed=0 tier=linux source-only
    P-DATA-03's OWN assertion, bare, as pins.py runs it        exit 0 under PYTHON=python; both halves print,
      the tiles half now ending "This is the TILES half. The corpus half is
      ops/lib/check-corpus-provenance.py (T-0219)". "UNASSERTED and UNOWNED" is gone from the tree (grep, 0
      hits under *.py and *.yaml).
    cd services/etl && python -m pytest tests -rs -o addopts=  1312 passed in 458.73s, ZERO skipped
      (__pycache__ purged first)
    python ops/lib/check-mutate-population.py                  exit 0, "76 modules, 26 covered by 12
      populations, 27 allowlisted, 0 added by this branch ... the floor of 25 holds"
    bash ops/lib/check-line-cap                                P-SRC-02: 92 Swift files, none over 300
    bash ops/lib/check-exec-bits                               P-OPS-01: 87 files, 23 required present
    PYTHON=python bash ops/queue-check                         QUEUE OK (222 tasks)
    gh pr checks 126                                           core pass 2m19s, pins-source-only pass 1m14s
    wc -l                                                      299 / 122 / 132, all under the 300-line cap
  PINS.yaml: 32 ids, none duplicated (`grep "^- id:" | sort | uniq -d` empty); P-DATA-03 carries no `pending:`
  key. NO MODULE WAS ADDED under services/etl/etl/ or Sources/, so no ops/mutate/ population is due - the
  author's R1 reasoning VERIFIED against the code and not taken on its word: check-mutate-population.py:65
  reads `MODULE_ROOTS = (("services/etl/etl", ".py", True), ("Sources", ".swift", True))`, and ops/lib is
  under neither; the run itself prints "0 added by this branch".

  BOX CONDITION VERIFIED HONEST, not papered over. The author's entry at 21:13:26Z says the bare assertion
  fails here on the TILES half with "No module named 'pytest'" because `command -v python3` resolves to the
  WindowsApps 3.14 shim. Reproduced exactly: `command -v python3` ->
  /c/Users/.../AppData/Local/Microsoft/WindowsApps/python3, `python3 -c "import sys;print(sys.version)"` ->
  3.14.5, and the bare assertion exits 1 naming the tiles half's writer; with PYTHON=python it exits 0. The
  failure is in check-pmtiles-provenance.py, which this branch did not touch functionally, and the assertion's
  own ${PYTHON:-...} hook is the documented route. CI runs one interpreter (linux-core.yml installs
  python3-pytest from apt) and does not see it.

  THE CORPUS HALF IS ACTUALLY REACHED BY ops/check-pins - checked by reading the code, not the Log.
  ops/lib/pins.py:117-118 is `if source_only and p.get("anchor") != "source": skipped += 1`, and P-DATA-03 is
  `anchor: artifact`, so --source-only SKIPS it; the author's R8 states exactly that and is correct. What runs
  it is the FULL `bash ops/check-pins`, and .github/workflows/linux-core.yml:85-86 runs precisely that inside
  the pinned swift image - so the corpus half executes in CI on every push, and `gh pr checks 126` shows that
  job (core) passing. services/etl/tests/test_corpus_provenance.py is a second, independent route to the same
  command as a subprocess at its real path, including --prove-red.

  FIVE MUTANTS, run by this reviewer on copies or with `git checkout --` restore; `git status --short` was
  empty after each and is empty now.
    M1 GATE - P-DATA-03's command pointed at a region the fixtures do not control. `--region sfbay` (the only
      other regions/ directory; its region.json id is "sfbay"): exit 0 with the fixture table still green,
      because every fixture is BUILT relative to whichever region is active, so the limbs go on deciding. It
      is NOT a silent pass over a wrong-region corpus: with SCENIC_LA_CORPUS set it exits 1 naming "the real
      artefact ... was REFUSED: meta.region is 'la', expected 'sfbay' (P-DATA-03)". NOT BLOCKING - nothing
      wrong-region or stale gets through green - but nothing binds the pin's command string to `la` either;
      RECORDED below.
    M2 THE READ PATH - is meta.region read from the table corpus.build STAMPS, or from one the fixture
      harness writes? Mutated the shipping stamp itself, services/etl/etl/corpus.py:119
      `writer.set_meta("region", region)` -> `"marin"`: the check went RED naming "a fresh region-la corpus:
      REFUSED but must be accepted; it said: meta.region is 'marin', expected 'la'". CAUGHT - the reader is
      bound to the shipping stamp. Restored with `git checkout --`, __pycache__ purged, 1.2 s slept.
    M3 THE AGE LIMB'S CLOCK - does the fixture freeze time or ride the wall clock? Both sides ride it
      (`stamp_days_ago` off `datetime.now(timezone.utc)`, `reference = now or datetime.now(timezone.utc)`),
      so a 40-day-old corpus is refused at the moment the check runs on any day - today's run stamped the
      fresh fixture 2026-09-25T19:26:19Z, six days after the author's, and all six verdicts held. Two mutants
      on copies: `reference = built` (compared against the corpus's OWN built_at) -> exit 1, "stamped 40 days
      ago: accepted", "stamped 2 days in the future: accepted"; `reference` hard-coded to the author's run
      date 2026-09-19 -> exit 1, "a fresh region-la corpus: REFUSED but must be accepted". BOTH CAUGHT.
    M4 THE MUTANT_FLOOR GUARD - copied the table, dropped three of the five rows. With the floor intact:
      exit 1, "--prove-red carries 2 mutants, below the floor of 5. A table that has lost rows must never
      read as 'every mutant refused'." With `if len(MUTANTS) < MUTANT_FLOOR:` disabled: exit 0, "2/2 mutants
      refused by name" - a green over nothing. The guard the 450cae3 correction added is load-bearing and
      present. CAUGHT.
    M5 SCENIC_LA_CORPUS NAMING SOMETHING THAT IS NOT A CORPUS - refusal by name or a traceback? A zero-byte
      file: exit 1, "meta is unreadable (no such table: meta): this is not a corpus". A PMTiles-shaped binary:
      exit 1, "meta is unreadable (file is not a database): this is not a corpus". The same file through
      `--corpus`: exit 1, "CORPUS REFUSED". A path that does not exist: exit 1, "names no file (set and absent
      is a refusal, never a skip)". No traceback in any of the four. CAUGHT.
  ZERO SURVIVORS that let a wrong-region or stale corpus pass green, and no limb that ops/check-pins never
  reaches. NO BLOCKING FINDING.

  RECORDABLE, none blocking, each named with the task that should own it:
    (a) Neither half checks that an artefact's CONTENT is the region it claims - a corpus stamped `la` whose
        ways are all in Marin passes. T-0233 ALREADY OWNS THIS (filed on main as 5df0b35 from this build);
        the checker's own docstring and P-DATA-03's text both name the gap. Nothing to file.
    (b) M1's residue: nothing in the tree binds P-DATA-03's assertion string to `--region la`. The assertion
        passes no --region and the default is `la`, so the shipped form is right, and the pytest exercises
        that default; but an edit to PINS.yaml adding `--region sfbay` is green in CI and only goes red on the
        box that has the artefact. Wants its own task if anyone wants the pin's own argument pinned - it is
        not T-0233's subject.
    (c) ops/lib/check-line-cap counts SWIFT files only ("92 Swift files tracked (Sources=29, Tests=42,
        apps/ios=21)"). CLAUDE.md's 300-line cap is stated for every file, and no gate enforces it over .py -
        which is why ops/lib/check-corpus-provenance.py sitting at 299 is a hand-held margin, not a held one.
        PRE-EXISTING, not this PR's; wants its own task.
    (d) Item 10 of the final acceptance block measures the task file at 238 lines; `wc -l` on the pushed head
        reads 239. A one-line drift on the only self-referential measurement in the block (T-0162's shape,
        which cost a round there). Every other measured number re-checked exactly: 299, 122, 148, 132, 296.
    (e) HEAD is 2 commits behind origin/main (969e082, 5df0b35), so `git merge-base --is-ancestor origin/main
        HEAD` now exits 1 where the author recorded exit 0 at 96ad82b. `git diff HEAD...origin/main` is
        queue/LOCKS/floors.lock and six queue task files ONLY - nothing under pins/, ops/ or .github/ - so
        main's GATE SET has not moved since the merge this sign-off was bought on. The orchestrator merges.

  DISPOSITION: PASS. queue/claimed/ -> queue/done/, reviewer: agent/rv1-pr126, state: done. Not merged here.
