---
id: T-0191
title: ops/mutate - one shared Python protocol module (the COPY tree, the pytest/JUnit verdict, --prove-vacuity and --prove-dirty ported from budget.py) that geometry.py and every later ETL population consume; geometry.py's file list says five
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/mutate/, services/etl/tests/, pins/PINS.yaml]
pins_affected: [P-PROC-05]
reviewer: null
depends_on: [T-0176]
verify: [ops/test, ops/check-pins]
acceptance:
  - "one module under ops/mutate/ (rule its name in the Log) holding what geometry_tree.py holds today - the COPY under a gitignored .build-mutate-* path, the __pycache__ purge, the pytest run, the JUnit/red-by-name verdict, the probe digest call - imported by ops/mutate/geometry.py; geometry_tree.py either becomes that module or is deleted; the geometry runner's table byte-identical before and after (quote both)"
  - "--prove-vacuity and --prove-dirty ported from budget.py to the Python protocol: the suites emptied must report every mutation MISSED (never killed); a subject that differs from git show HEAD: must be refused by name; each demonstrated RED first (a copy where the proof is skipped), then green; P-PROC-05's assertion widened to run all three proofs"
  - "ops/mutate/geometry.py's docstring names the files that exist (five today, or the count after this task); an ops/mutate/README.md or the module docstring states the shape T-0187 (assemble) and every ETL term population must follow, in under 40 lines"
  - "the per-entry contract in the shared protocol: an entry whose killers list is empty OR holds duplicate names is refused by name before any pytest (rv2-pr107 found the duplicate half surviving: two copies of one killer satisfy len(red) == len(killers) with one distinct test); EQUIVALENT entries need a non-empty reason; each RED first on a copy, then green; a --prove-floor arm for the duplicate"
  - "python ops/mutate/geometry.py bare, --prove-floor, --prove-vacuity, --prove-dirty, --non-example all exit 0 and quoted; cd services/etl && python -m pytest tests -rs count line and zero skips; bash ops/check-pins --source-only, bash ops/lib/check-line-cap, bash ops/lib/check-exec-bits, bash ops/queue-check bare; every ops/mutate/*.py under 300 lines"
---
## Brief

From the 22:13 panel (CODE lens, grounded). T-0176's population is budget.py's protocol and improves on it twice
(REQUIRED_CLASSES makes the floor two-sided; geometry_probe.py replaces the prose witness with a digest recomputed
every run), but it diverges three ways that every later ETL population pays for: main() dispatches only
--prove-floor and --non-example, so the new pytest verdict layer has never been shown able to report MISSED with
the suites emptied nor to refuse a subject that differs from HEAD; ops/mutate now holds nine standalone drivers
with no shared library, and the COPY tree and JUnit verdict exist only inside geometry_tree.py, so T-0187 would
copy-paste or re-derive them; geometry.py's docstring says 'THE FOUR FILES' while five exist. Lands before T-0187
is claimed so assemble's population is the second consumer of one shape, not a second shape.

## Log
- 2026-09-19T04:34:10Z filed by agent/claude-fable-5-1 from the 22:13 panel's grounded synthesis. Not started; after #107 merges, before T-0187 is claimed.
- 2026-09-19T06:03:45Z bullet added by agent/claude-fable-5-1 from rv2-pr107's PASS on PR #107 (recordable 1: duplicate killer names survive; recordable 2: EQUIVALENT entries have no per-entry contract). The empty-killers half is closed on #107 (cd1319f); the duplicate half lands with the shared protocol.
- 2026-09-19T10:42:07Z CARRIED IN from rv1-pr114's PASS on PR #114 (T-0186), by agent/claude-fable-5-1: RV1-A - COVERED_FLOOR is a tuple inside the checker's own source, so narrowing a driver's SUBJECT_MODULES and deleting the same line from the floor in one edit is green with no reason recorded; move the floor to DATA beside the allowlist with a reason per removal (the allowlist's shape). Lands with the shared protocol.
