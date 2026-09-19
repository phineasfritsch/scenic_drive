---
id: T-0218
title: ScenicKit - the class ceiling reaches the app: SegmentScore over corpus terms_* is UNCAPPED while the router's band is capped by assemble.CLASS_SCORE_CEILING; rule ONE owner before M4's explanation and hazard strip read both, and name what the P-PROD-01 differential compares
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, services/etl/etl/, services/etl/tests/, pins/PINS.yaml]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: [T-0207]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULED in the Log before code, from the measurement: the corpus carries no score column (schema.py rule 6 - 'computed from terms_* at query time'); the tagged PBF carries the quantised, CAPPED integer (assemble.scored_row applies CLASS_SCORE_CEILING after score_record; residential/living_street 0.6499, service 0.0); ScenicKit's SegmentScore over the same terms is uncapped, so a hillside residential the router bands at 6 reads 0.80 in the app. Rule ONE owner: (a) the corpus ships a per-way class cap the app applies (a column or the class table), or (b) ScenicKit carries the same ceiling table keyed on the same class strings, or (c) the differential is defined PRE-ceiling and every app surface that shows a number says which it shows - and say what P-PROD-01's 1e-6 differential compares (pre- or post-ceiling) in the pin text"
  - "the shared scoring fixture (services/etl/tests/test_score_contract.py <-> Tests/ScenicKitTests/SegmentScoreContractTests.swift) gains capped-class rows whose EXPECTED value is the ruled one, RED by name first on the side that disagrees, then green on both; the ETL suite count line and 'swift test --filter ScenicKitTests' (through CI linux-core if no local toolchain) quoted"
  - "python ops/lib/check-mutate-population.py (any new module populated or allowlisted with a reason), check-line-cap, check-exec-bits, queue-check bare"
---
## Brief

From the 06:13 panel (CODE lens; fable-grounded on assemble.py:119/:234-236, schema.py:24-25, PINS.yaml:121 and
T-0207's Log R1 :102-110): T-0207 ruled the ceiling ETL-only with the parity fixture compared PRE-ceiling, and left
the app half 'STILL OPEN'. T-0149/T-0012 own P-PROD-01's assertion (still TODO) but not this question. Nothing is
wrong until M4 puts a number on a screen; rule it before then, not after.

## Log
- 2026-09-19T16:40:26Z filed by agent/claude-fable-5-1 (06:13 panel, CODE lens, fable-grounded on assemble.py:141-150 / schema.py). Not started; after the routed LA drive (T-0209), before M4's route preview.
