import Foundation
import ScenicAPIClient

/// Production's session today (T-0307 R2): none. No Swift code holds a Worker session yet - no attest or Sign in
/// with Apple client exists - so the ledger is never called and the Surprise history stays on the device. The
/// session client replaces this conformer; nothing else changes.
struct NoLedgerSession: LedgerSessionProvider {
    func sessionToken() -> String? { nil }
}
