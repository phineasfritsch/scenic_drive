---
id: T-0211
title: SantaMonicaMountainsRoute - rule the 101/405 middle leg: a surface return (Ventura/Sepulveda to Mulholland), a Malibu Canyon out-and-back, or copy that names the freeway as the price of unpaved Mulholland; pins re-verified
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/Handoff/, Tests/HandoffTests/, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/]
pins_affected: []
reviewer: null
depends_on: [T-0178]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULED in the Log before code with the measured alternatives: the loop today is 'Sunset west, PCH north, Topanga up, the 101 and 405 back over the pass, Mulholland east, down Beverly Glen' (DriveCopy.swift:47) - the owner's freeway baseline sits in the MIDDLE of the scenic drive, the opposite of the plan's 'freeway shoulders, scenic middle'; candidates: (a) Ventura Blvd + Sepulveda Blvd surface return to Mulholland, (b) an out-and-back on Topanga or a Malibu Canyon / Las Virgenes return, (c) keep the freeway and say why in the copy; T-0178's R0 (Mulholland is not continuous from Topanga; Dirt Mulholland's surface unverified) stands unless re-measured"
  - "every changed pin reverse-geocoded by Nominatim (way id + road name beside the literal, 1.1 s apart); the Linux suite's count/order/spacing literals and the straight-line km re-pinned, RED by name first; ios-compile green if Swift under apps/ios moves"
---
## Brief

DRIVER ONE, 03:13 panel (grounded): 'The 405 over the Sepulveda Pass IS my baseline - it is the thing I bought this
app to avoid, sitting in the middle of the loop... I would drive Sunset/PCH/Topanga out and turn around.' The
owner's judgement decides between the candidates; the agent measures them.

## Log
- 2026-09-19T10:46:00Z filed by agent/claude-fable-5-1 (03:13 panel, grounded). Not started; after #115 merges. FOR THE HUMAN: which return would you actually drive?
