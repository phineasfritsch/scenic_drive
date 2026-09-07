---
id: T-0001
title: Repo skeleton: root package, ScenicKit, LF normalization, preflight, pre-commit hook
state: done
owner: agent/claude-opus-5
owner_session: 01RJHHJcZtZChD9eMb275urx
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Package.swift, Sources/, Tests/, CLAUDE.md, README.md, .gitattributes, .gitignore, ops/agent-preflight, .githooks/pre-commit]
pins_affected: []
reviewer: agent/reviewer-1
depends_on: []
verify: [ops/test, ops/check-pins, ops/queue-check]
acceptance:
  - "swift test --parallel -> Test run with 3 tests in 1 suite passed, on Windows AND in swift:6.1-noble (Linux)"
  - "bash ops/agent-preflight -> PREFLIGHT OK (hooksPath=.githooks, autocrlf=false, no CRLF files)"
  - "RED: staging a file containing sk.<20+ chars> and running git commit -> pre-commit: secret-looking content, exit 1, HEAD unchanged"
---
## Brief

Root SPM package with the first Foundation-only target (ScenicKit: Coordinate, Geo haversine/bearing) and a real
Swift Testing suite; .gitattributes eol=lf; CLAUDE.md fleet rules; ops/agent-preflight; .githooks/pre-commit
(CRLF, secrets, touches:). The thin .xcodeproj shell needs a Mac and is split out as T-0010.
Do NOT add Apple-only targets to the root package - they go in apps/ios/Packages/ScenicApp (T-0010).

## Log
- 2026-09-07 swift test: Windows 3/3 (Swift 6.3.3); Linux swift:6.1-noble 3/3 via WSL2 Docker; spm-junit.xml + spm-junit-swift-testing.xml produced
- 2026-09-07 hook RED demo: sk. token refused, exit 1, HEAD stayed 6c18be0. CRLF check not reachable because .gitattributes normalizes on add (intended)
- 2026-09-07 awaiting reviewer != owner
- 2026-09-07T03:14:00Z reviewed by agent/reviewer-1: FAIL — work files (Package.swift, Sources/, Tests/, ops/agent-preflight, .githooks/pre-commit, etc.) exist in working directory as untracked files but are not committed to git; git ls-files shows only .gitattributes. The skeleton repository state does not exist in git history.
- 2026-09-07T03:14:00Z reviewed by agent/reviewer-1: FAIL — work files (Package.swift, Sources/, Tests/, ops/agent-preflight, .githooks/pre-commit, etc.) exist in working directory as untracked files but are not committed to git; git ls-files shows only .gitattributes. The skeleton repository state does not exist in git history.
- 2026-09-07T03:30:00Z reviewed by agent/reviewer-1: PASS — swift test 3/3 passed; ops/agent-preflight OK with eol=lf check; pre-commit secret detection RED demo confirmed.
