---
id: T-0260
title: ScenicAPIClient sends the install UUID as x-scenic-device on every Worker call, so each install gets its own quota bucket instead of sharing device:unidentified
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T16:33:17Z
lease_expires_at: 2026-10-06T04:33:17Z
worktree: .worktrees/T-0260
branch: task/T-0260
exclusive: []
touches: [Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/]
pins_affected: [P-COST-01, P-PRIV-05]
reviewer: null
depends_on: [T-0251, T-0256]
verify: [ops/test, ops/check-pins]
acceptance:
  - "every request ScenicAPIClient builds carries x-scenic-device equal to an injected install-id provider's lowercased RFC 4122 UUID, asserted on the recorded request by EXACT equality of the whole header set; the id is generated once per install and never derived from location, and no other identifying header is added (P-PRIV-05)"
  - "a request built with no provider is refused at build time (a typed error), never sent without the header - RED by name"
---
## Brief

T-0256 (PR #147) R2: until App Attest exists, the Worker keys quota by the app's install UUID from the
x-scenic-device header; a missing or malformed header lands in one shared device:unidentified bucket, so every
install would share 3 anon plans a day. The keychain-backed provider itself lives in the Apple package (M6); this
task is the root-package half: the header and the provider protocol.

## Log
- 2026-10-05T14:31:22Z filed by agent/claude-opus-5 (orchestrator) from T-0256's stillOpen (e).
- 2026-10-05T16:31:14Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): dependencies merged (T-0175 #142, T-0251 #148, T-0256 #147).
- 2026-10-05T16:33:17Z claimed by agent/claude-opus-5; lease until 2026-10-06T04:33:17Z
