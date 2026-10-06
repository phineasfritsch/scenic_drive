---
id: T-0284
title: ops/funnel prints the plan -> preview -> drive -> answer funnel and W1/W4 return from Analytics Engine telemetry rows (offline over a recorded fixture; live via the AE SQL API when the owner supplies a read token)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T16:12:52Z
lease_expires_at: 2026-10-07T02:12:52Z
worktree: .worktrees/T-0284
branch: task/T-0284
exclusive: []
touches: [ops/funnel, ops/lib/, Tests/Fixtures/t0284/, ops/mutate/]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0265, T-0279]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/funnel --fixture <file> reads rows in the exact Analytics Engine SQL API response shape for the T-0279 dataset (blob1 = event name, blob2 = label, blob3 = cell, double1/2, timestamp, index1; quote Cloudflare's documented response format in the Log) and prints, for a ruled window: plan_requested -> preview_shown -> drive_started -> post_drive_answer counts and step conversion, prettier share, and W1/W4 return rate keyed by the ONLY per-device key the dataset carries (rule it - if none, say W1/W4 cannot be computed and print that, never invent a key); the whole printed output is pinned by exact equality over a committed synthetic fixture"
  - "--live reads ACCOUNT_ID and an AE read token from the environment only (never argv, never the tree; refuse with a named exit code when absent); the SQL is a fixed literal; tested with a stubbed HTTP layer; no coordinates are ever read or printed (P-PRIV-05)"
  - "committed executable (git update-index --chmod=+x); a mutation population with a literal floor for the arithmetic"
---
## Brief

Plan Telemetry: 'ops/funnel prints plan->preview->drive->answer and W1/W4 return'. T-0265 encodes, T-0279 ingests;
nothing reads. Success metric from the plan: W1/W4 return and the post-drive 'prettier than your usual way?' answer.

## Log
- 2026-10-06T16:11:39Z filed by agent/claude-opus-5 (orchestrator) after PR #169 (T-0279) merged.
- 2026-10-06T16:12:52Z claimed by agent/claude-opus-5; lease until 2026-10-07T02:12:52Z
- 2026-10-06T16:18:02Z RULINGS (agent/claude-opus-5, owner), before any code:
  - R1 The per-device key: THERE IS NONE. T-0279 R2 writes exactly the T-0265 point, rebuilt by services/api/src/telemetryPoint.ts as `{ blobs: [name, label, cell], doubles: [v1, v2], indexes: [name] }`; src/telemetry.ts calls identifyCaller only for the quota bucket and passes `parsed.points` straight to `writeDataPoint` - the caller's identity is never written. So index1 = blob1 = the event name, blob2 = a closed-enum label, blob3 = an H3 res-5 cell (a place, shared by every device in ~250 km2, never a device), double1/2 = whole numbers. W1/W4 return CANNOT be computed from this dataset; ops/funnel prints exactly that for each and invents no key (not the cell, not a timestamp cluster). Adding a key is a privacy decision for the owner (a rotating per-install salt, say) and its own task, not this one.
  - R2 The response shape. Fetched once, developers.cloudflare.com/analytics/analytics-engine/sql-api/: "`POST https://api.cloudflare.com/client/v4/accounts/<account_id>/analytics_engine/sql`", "`Authorization: Bearer <token>`", the table holds "`dataset`, `timestamp`, `_sample_interval`, `index1`, `blob1` through `blob20` (strings), and `double1` through `double20` (doubles)", and "The format of the data returned can be selected using the FORMAT option in your query". That page shows no response body, so the SQL names `FORMAT JSON` explicitly rather than lean on a default: ClickHouse's JSON output `{"meta": [{"name", "type"}...], "data": [{column: value}...], "rows": n, "rows_before_limit_at_least": n}` with timestamp a `YYYY-MM-DD HH:MM:SS` string, strings as strings, Float64 doubles and the UInt32 `_sample_interval` as JSON numbers. The reader is a WHITELIST over that shape: top-level keys exactly {meta, data, rows} plus optional rows_before_limit_at_least/statistics, meta names exactly the SQL's column list in order, each data row exactly those keys, rows == len(data); anything else exits 4 (RESPONSE_REFUSED) naming the first fault. A live response that does not match is refused, never guessed at.
  - R3 The SQL, a fixed literal: `SELECT timestamp, index1, blob1, blob2, double1, double2, _sample_interval FROM scenic_telemetry WHERE timestamp > NOW() - INTERVAL '28' DAY ORDER BY timestamp FORMAT JSON`. blob3 (the cell) is NOT selected: the funnel needs no place, so the reader never holds one (P-PRIV-05 - nothing location-like is read, let alone printed); a response carrying blob3 or any column outside the list is refused by R2. The acceptance names blob3 as the dataset layout, which this respects; the response shape is the shape of THIS query. The fixture is that response.
  - R4 The window: the last 28 days before the query (the SQL's NOW(), server clock) - 28 because W4 is the longest horizon the plan names. ops/funnel prints the ruled window and the first and last row timestamps it saw; it does not re-filter client-side (the fixture is the recorded answer to the same SQL, so a second clock would only disagree with the first).
  - R5 Step definitions. Each row counts its `_sample_interval` (AE's sampling weight, an integer >= 1; a row with 0, a fraction or a non-number is refused). Steps are event TOTALS in the window: plan_requested -> preview_shown -> drive_started -> post_drive_answer. With no device or session key (R1) they are not per-user and a step may exceed 100%; conversion is printed as is. Conversion = this step / the previous step, as a percent to one decimal rounded half up in integer arithmetic (tenths = (200*1000*num + den) // (2*den) form), `n/a` when the previous step is 0. Prettier share = prettier / (prettier + not_prettier) over post_drive_answer rows, same rounding, `n/a` when both are 0. A post_drive_answer label outside {prettier, not_prettier}, a funnel-step label that is not "" where T-0279 R3 writes "", an event name outside T-0279's fifteen, or index1 != blob1 is refused (exit 4). The other eleven names are counted on one line, `other events`.
  - R6 --live reads ACCOUNT_ID and AE_READ_TOKEN from the environment only; there is no argv option for either (argparse refuses one as usage, exit 2), they are never written to the tree, never printed. Either absent or empty -> exit 3 (CREDENTIALS_ABSENT) naming which. The HTTP layer is one injected callable (url, headers, body) -> (status, bytes); tests pass a stub and assert the exact url, headers and body; a non-200 is exit 5 (HTTP_FAILED) with the status only. No test touches the network.
  - R7 Population. P-PROC-06 (ops/lib/check-mutate-population.py) reads MODULE_ROOTS = services/etl/etl and Sources only, and DRIVERS refuses any runnable ops/mutate/*.py whose SUBJECT_MODULES names a module outside those roots, so ops/lib/funnel_math.py cannot be a registered DRIVER and the gate does not see it. Widening that gate is out of scope. The population is therefore ops/mutate/funnel_mutations.py (a data table with a literal MIN_MUTATIONS, no `__main__`, so the DRIVERS whitelist is not tripped) run by ops/lib/funnel_mutate.py, whose floor arm refuses a table shorter than the literal. The test is ops/lib/funnel_test.py (unittest, `python ops/lib/funnel_test.py`); neither ops/test nor CI runs it today - pins/PINS.yaml and the workflows are outside touches - recorded as the remaining gap.
  - R8 Exit codes: 0 printed; 2 usage; 3 credentials absent; 4 response refused; 5 HTTP failed.
