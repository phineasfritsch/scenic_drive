import Foundation

/// What Settings' Delete Account confirmation runs (T-0356): DELETE /account through `AccountClient`, then - only on a
/// confirmed `deleted` - every item `LocalAccountItem.erasedOnDeletion` names, in the table's order (R3). Any other
/// outcome erases nothing (R5). The outcome is handed back for `AccountDeletionCopy`.
public struct AccountDeletion: Sendable {
    let client: AccountClient
    let eraser: any LocalAccountEraser

    public init(client: AccountClient, eraser: any LocalAccountEraser) {
        self.client = client
        self.eraser = eraser
    }

    public func run() async -> AccountOutcome {
        let outcome = await client.deleteAccount()
        guard case .deleted = outcome else { return outcome }
        for item in LocalAccountItem.allCases where item.erasedOnDeletion {
            await eraser.erase(item)
        }
        return outcome
    }
}
