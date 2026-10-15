import Foundation

/// The note Settings shows after a deletion attempt (T-0356 R6). A success says what it did not do - the
/// subscription is Apple's, saved drives stay on the iPhone, a pending Apple revocation or plan sweep - and a failure
/// never claims a deletion; an unconfirmed one says a retry is safe (DELETE /account is idempotent).
public enum AccountDeletionCopy {
    static let deleted = "Your Scenic Drive account is deleted. Your subscription is billed by Apple: cancel it in "
        + "Manage Subscription if you no longer want it. Saved drives stay on this iPhone until you delete the app."
    static let revokePending = " Apple has not confirmed the Sign in with Apple disconnect yet; you can remove "
        + "Scenic Drive yourself in the Settings app, under your name, Sign in with Apple."
    /// A plan the sweep missed lives to its KV TTL, <= 43200 s (P-PRIV-04, T-0326 R8).
    static let plansPending = " A route remembered for rerouting can last up to 12 hours before it expires."
    static let notDeleted = "Scenic Drive couldn't delete your account right now. Your account was not deleted. "
        + "Try again later."

    public static func note(for outcome: AccountOutcome) -> String {
        switch outcome {
        case .deleted(let revoke, let plans):
            return deleted + (revoke ? revokePending : "") + (plans ? plansPending : "")
        case .offline:
            return "Couldn't reach Scenic Drive, so nothing was deleted. Check your connection and try again."
        case .noSession:
            return "Couldn't start a secure connection to Scenic Drive, so nothing was deleted. "
                + "Check your connection and try again."
        case .unreadable:
            return "Scenic Drive answered, but the deletion couldn't be confirmed. Try again - deleting twice is safe."
        case .unauthorized, .methodRefused, .authUnavailable, .accountUnavailable, .unexpected:
            return notDeleted
        }
    }
}
