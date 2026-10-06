---
id: T-0284
title: ops/funnel prints the plan -> preview -> drive -> answer funnel and W1/W4 return from Analytics Engine telemetry rows (offline over a recorded fixture; live via the AE SQL API when the owner supplies a read token)
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
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
