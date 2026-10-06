---
id: T-0283
title: Surprise picks stop clustering at the edge of the time budget - the time-fit term peaks inside the dial (measured over the bundled LA corpus), and scenic classes outrank cafes when quality is unknown
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T21:12:21Z
lease_expires_at: 2026-10-07T11:12:21Z
worktree: .worktrees/T-0283
branch: task/T-0283
exclusive: []
touches: [Sources/ScenicKit/Surprise/, Tests/ScenicKitTests/, Tests/Fixtures/surprise/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PROD-02]
reviewer: null
depends_on: [T-0253, T-0273]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE FIRST: over the committed fallback corpus (apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite) with the T-0273 offline reach from Westwood at dials 30/60/90/120, quote the distribution of picked round-trip minutes / budget for seeds 0..99 and the class mix of the picks, BEFORE changing any weight (T-0273 stillOpen 5: picks land at the far edge, e.g. Calas Park at exactly 120)"
  - "RULE a time-fit term that peaks at a ruled fraction of the budget (e.g. 0.6-0.75) and a class prior (viewpoint/peak/waterfall/beach/trailhead/garden above park/museum/town above cafe) consistent with the owner's taste memory (winding back roads, scenery over the obvious; 'calm adventure'); re-measure and quote the new distribution; the Python oracle (Tests/Fixtures/surprise/model.py) and Swift agree on the whole permutation by full equality"
  - "P-PROD-02 reproducibility and >= 90% distinct still hold; existing filter tests unchanged; population entries for the new terms with a literal floor"
---
## Brief

T-0273 stillOpen 5: 'The pick tends to land at the far edge of the 120-min budget (Calas Park at exactly 120), because
every place has quality 50 and the selector's minutes/budget term wins.' A Surprise for someone with time to kill
should land comfortably inside it. Product taste: memory owner-route-intent.

## Log
- 2026-10-06T16:04:49Z filed by agent/claude-opus-5 (orchestrator) from T-0273's open item.
- 2026-10-06T21:12:21Z claimed by agent/claude-opus-5; lease until 2026-10-07T11:12:21Z
- 2026-10-06T21:18:36Z MEASURED, then RULINGS before code (agent/claude-opus-5, owner). Read: Sources/ScenicKit/Surprise/*
  (Surprise.score R4, SurpriseOfflineReach, SurprisePlaceMapping, SurprisePlaceClass), Tests/Fixtures/surprise/model.py,
  ops/mutate/surprise*.py, queue/done/T-0253 (R4: timeFit = minutes * 100 / max(budget, 1)) and T-0273 (R3: quality 50
  for every place), memory owner-route-intent ("calm adventure"; winding back roads and scenery over the obvious).
  MEASURE FIRST (acceptance 1), Tests/Fixtures/surprise/corpus_measure.py --before (read-only sqlite3 over
  apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite: 1334 places, all named, all ten classes; T-0273's mapping and
  offline reach from Westwood; model.sequence for user on-device, 2026-10-06, depart 600; picks = the first 100 of the
  permutation = seeds 0..99), T-0253's rule, quoted whole:
    dial= 30 eligible=  74 picks= 74 distinct= 74  rt/budget min=0.07 p25=0.37 median=0.77 p75=0.90 max=1.00
              bins [0,.2) [.2,.4) [.4,.6) [.6,.8) [.8,1]: [11, 10, 9, 12, 32]  at-exactly-budget=5  seed0=Broad Contemporary Art Museum museum 30 min
              classes: park 24, garden 17, museum 12, viewpoint 9, cafe 4, town 4, trailhead 4
    dial= 60 eligible= 263 picks=100 distinct=100  rt/budget min=0.03 p25=0.80 median=0.88 p75=0.95 max=1.00
              bins [0,.2) [.2,.4) [.4,.6) [.6,.8) [.8,1]: [2, 3, 7, 11, 77]  at-exactly-budget=8  seed0=Travel Town Museum museum 60 min
              classes: park 22, museum 15, viewpoint 15, peak 14, trailhead 12, cafe 9, garden 5, beach 5, town 2, waterfall 1
    dial= 90 eligible= 465 picks=100 distinct=100  rt/budget min=0.02 p25=0.84 median=0.92 p75=0.97 max=1.00
              bins [0,.2) [.2,.4) [.4,.6) [.6,.8) [.8,1]: [1, 7, 4, 7, 81]  at-exactly-budget=4  seed0=South Park park 90 min
              classes: park 34, museum 15, town 12, garden 11, peak 8, trailhead 7, viewpoint 5, beach 5, cafe 3
    dial=120 eligible= 695 picks=100 distinct=100  rt/budget min=0.02 p25=0.93 median=0.97 p75=0.97 max=1.00
              bins [0,.2) [.2,.4) [.4,.6) [.6,.8) [.8,1]: [2, 5, 5, 7, 81]  at-exactly-budget=3  seed0=Calas Park park 120 min
              classes: park 25, trailhead 13, peak 12, garden 12, museum 10, town 9, viewpoint 8, cafe 4, beach 4, waterfall 3
  The stillOpen is real: at 60/90/120 77-81 of 100 picks sit in the last fifth of the dial, seed 0 at 120 is Calas Park
  at exactly 120, and parks/museums/towns (flat quality 50) are 44-61 of the picks. At dial 30 only 74 places are
  eligible, so seeds 0..99 run the whole population and no ranking rule changes its distribution (it wraps; R5).
  Explored before ruling (same script, time-fit and prior varied): peak 65/70 x slope 2/3 with prior 70/55/40, then
  peak 70 slope 2 with prior 80/50/30, 75/50/25, 90/50/20 - a wider prior gap moves the class mix toward scenery and
  lets a scenic place far from the peak beat a park at it (the [.8,1] bin at 120: 10 / 26 / 22 / 25).
  R1 TIME-FIT. timeFit = max(0, 100 - timeFitSlope * |pct - timeFitPeakPercent|), pct = minutes * 100 / max(budget, 1)
  (Int, truncating; the dial's budget, as T-0253 R4), Surprise.timeFitPeakPercent = 70, Surprise.timeFitSlope = 2:
  100 at 70% of the dial, 40 at the dial's edge, 0 at or under 20%. Within the brief's 0.6-0.75: a Surprise for someone
  with time to kill lands comfortably inside it and still uses most of it (calm, not a quick errand). The clamp keeps
  every term 0-100 like the other three.
  R2 CLASS PRIOR. SurprisePlaceClass.priorQuality: viewpoint, peak, waterfall, beach, trailhead, garden 75; park,
  museum, town 50; cafe 25. SurprisePlaceMapping's flat `quality = 50` goes; a mapped candidate's quality is its
  class's prior (the corpus carries no notability signal - T-0270 open item 2 - so the class is the only taste we
  have: scenery over the obvious, a cafe is the last resort). The middle tier keeps T-0273's 50 and the outer tiers sit
  25 either side. It lives in the MAPPING, not in Surprise.score: SurpriseCategory folds peak into viewpoint and
  waterfall into trailhead, and a curated candidate's quality (the synthetic fixture's) is a real score the prior must
  not overwrite - the prior is the stand-in for an unknown quality only.
  R3 ORACLE AND PARITY. model.py's time_fit carries R1 (sequences.tsv regenerated). corpus_measure.py additionally
  writes Tests/Fixtures/surprise/corpus.tsv (every named place row: place_id, cls, name, lon_e7, lat_e7, read-only
  from the committed corpus, which the app already ships) and corpus_sequences.tsv (dial, seed, id: the first 100
  picks at dials 30/60/90/120, user on-device, 2026-10-06, depart 600, offset -420), computing quality by R2 and the
  reach by T-0273 R2 independently in Python; it REFUSES to write if any round trip's unrounded minutes lie within
  1e-6 of an integer (a last-bit libm difference could flip a ceiling). A new Swift suite feeds every row through
  SurprisePlaceMapping.candidate and SurpriseOfflineReach.reach - the card's chain - into Surprise.pick and compares
  the whole 100-pick sequence per dial by full equality, plus a defect-named test over the 120 dial's picks with
  bounds written from the re-measurement (R1+R2) below.
  R4 TESTS THAT CHANGE AND WHY. SurpriseFilterTests unchanged byte for byte (set-valued over every eligible pick).
  SurpriseRankTests.permutation reads the regenerated sequences.tsv; reasons() and SurpriseFeedbackTests pin the
  seed-0 / seed-3 / next picks as literals, which are ORACLE OUTPUTS (model.py prints them) - they move to the new
  oracle's printout with every assertion's shape unchanged. SurprisePlaceMappingTests' expected candidate carries
  quality from a second, typed-in prior table. P-PROD-02's four bound tests keep their names.
  R5 POPULATION. New entries in ops/mutate/surprise_fit_mutations.py appended to MUTATIONS (the offline file's shape):
  peak and slope each moved both ways, the clamp dropped, the absolute value dropped, the T-0253 linear fit restored,
  each prior tier moved, a scenic class demoted to the middle tier, cafe promoted; the two existing entries whose
  `old` text names the score (32 time-fit dropped) or the flat quality (106) are re-targeted to the new text; the
  floor is raised to the new count, literal.
  R6 SCOPE. P-PROD-02's prose gets a dated sentence appended (pins/PINS.yaml added to touches for that line only); no
  card or app code changes (the deck already calls SurprisePlaceMapping.candidate).
- 2026-10-06T21:35:00Z RED then GREEN (agent/claude-opus-5). Oracle first: model.py time_fit = R1 (FIT_PEAK 70,
  FIT_SLOPE 2) and sequences.tsv regenerated - model.py prints P0=sgc-05 cat=park rt=132, next picks seed0
  {tooFar, notMyThing, beenThere, wrongTime} all griffith-02, wrongTime next day seed0=sgc-05, A[0..5]=['sgc-05',
  'griffith-02', 'malibu-04', 'pv-02', 'simi-00', 'griffith-07'], distinct over seeds 0..99 A=100, witnesses wrongly
  present=[]. corpus_measure.py --write: corpus.tsv 1334 rows + corpus_sequences.tsv 374 picks, no ULP refusal.
  RE-MEASURED with R1+R2 (acceptance 2), corpus_measure.py, quoted whole:
    dial= 30 eligible=  74 picks= 74 distinct= 74  rt/budget min=0.07 p25=0.37 median=0.77 p75=0.90 max=1.00
              bins [0,.2) [.2,.4) [.4,.6) [.6,.8) [.8,1]: [11, 10, 9, 12, 32]  at-exactly-budget=5  seed0=Kenter Fire Trail trailhead 22 min
              classes: park 24, garden 17, museum 12, viewpoint 9, trailhead 4, town 4, cafe 4
    dial= 60 eligible= 263 picks=100 distinct=100  rt/budget min=0.05 p25=0.62 median=0.68 p75=0.77 max=0.98
              bins [0,.2) [.2,.4) [.4,.6) [.6,.8) [.8,1]: [3, 2, 15, 59, 21]  at-exactly-budget=0  seed0=Castle Rock Beach beach 43 min
              classes: park 22, viewpoint 21, trailhead 14, museum 12, garden 11, peak 11, beach 5, cafe 2, waterfall 1, town 1
    dial= 90 eligible= 465 picks=100 distinct=100  rt/budget min=0.03 p25=0.62 median=0.70 p75=0.73 max=0.97
              bins [0,.2) [.2,.4) [.4,.6) [.6,.8) [.8,1]: [2, 5, 8, 80, 5]  at-exactly-budget=0  seed0=Van Nuys Airport Public Observation Area viewpoint 63 min
              classes: garden 33, peak 17, viewpoint 16, park 12, beach 7, trailhead 5, museum 5, cafe 4, waterfall 1
    dial=120 eligible= 695 picks=100 distinct=100  rt/budget min=0.17 p25=0.62 median=0.71 p75=0.79 max=0.97
              bins [0,.2) [.2,.4) [.4,.6) [.6,.8) [.8,1]: [1, 6, 16, 55, 22]  at-exactly-budget=0  seed0=Tongva Peak peak 84 min
              classes: peak 24, garden 17, park 13, trailhead 13, viewpoint 12, beach 12, museum 4, town 3, cafe 2
  Last fifth of the dial 77/81/81 -> 21/5/22; medians 0.88/0.92/0.97 -> 0.68/0.70/0.71; none at exactly the dial at
  60/90/120 (was 8/4/3); scenic classes at 120 52 -> 78, cafes 4 -> 2; seed 0 at 120 Calas Park (park, 120 min) ->
  Tongva Peak (peak, 84 min). Dial 30 unchanged as a distribution (all 74 eligible run, R0), its order changes.
  The defect test's bounds are written from this measurement: at 120, none at exactly 120, <= 25 in [0.8, 1] (22),
  median in [0.6, 0.8] (0.71), >= 70 scenic (78), <= 5 cafes (2), >= 90 distinct (100).
  RED by name, swift test --scratch-path .build-t0283/swift --filter Surprise with the tests and oracle changed and
  Sources/ScenicKit untouched: FAILED "every corpus class maps to its ruled candidate, field for field (R3)" (7
  issues: the seven classes whose prior is not 50), "the WHY: three picks pinned whole - hook, round trip and the
  golden-hour line from Solar", "not this - too far: ...", "not this - been there: ...", "not this - wrong time: ...",
  "the whole pick permutation equals the oracle's: driver-a, driver-c and driver-b with history", "the card's picks
  for seeds 0..99 at dials 30, 60, 90 and 120 equal the oracle's, by full equality" (4 issues, every dial) and "at a
  120-min dial the picks for seeds 0..99 land inside the dial, not at its edge, and mostly scenery" (4 issues);
  every filter test and P-PROD-02's reproducible() and distinct() green. GREEN after Surprise.timeFit
  (timeFitPeakPercent 70, timeFitSlope 2), SurprisePlaceClass.priorQuality and the mapping reading it: "Test run with
  38 tests in 8 suites passed". SurpriseFilterTests.swift: git diff empty. Line counts: Surprise.swift 160,
  SurprisePlaceClass.swift 95, SurprisePlaceMapping.swift 36, SurpriseCorpusFitTests.swift 60, corpus_measure.py 144.
