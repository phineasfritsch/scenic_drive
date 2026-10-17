import Foundation
import ScenicAPIClient

/// What Settings' Delete Account confirmation runs (T-0356 R7): ScenicAPIClient `AccountDeletion` over the launch's
/// ONE session store and the deployed Worker (`plan.base.url`, https only), erasing through `DeviceAccountEraser`,
/// answered as `AccountDeletionCopy`'s note. Without a base URL or a session store there is no session to send:
/// the note is the no-session one and nothing is requested or erased.
public enum LiveAccountDeletion {
    public static func run() async -> String {
        guard let base = LiveBaseURL.url, let store = LiveSession.store
        else { return AccountDeletionCopy.note(for: .noSession) }
        let client = AccountClient(base: base, transport: URLSessionPlanTransport(), session: store)
        let outcome = await AccountDeletion(client: client, eraser: DeviceAccountEraser()).run()
        return AccountDeletionCopy.note(for: outcome)
    }
}
