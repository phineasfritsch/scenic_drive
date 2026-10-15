import Foundation
import ScenicAPIClient
import Testing

/// T-0356 A4 (R6): the note Settings shows after a deletion attempt, by full equality for every AccountOutcome. A
/// success never hides what it did not do (the subscription, the saved drives, a pending Apple revocation or plan
/// sweep); a failure never claims a deletion.
@Suite("AccountDeletionCopyTests") struct AccountDeletionCopyTests {
    static let deleted = "Your Scenic Drive account is deleted. Your subscription is billed by Apple: cancel it in "
        + "Manage Subscription if you no longer want it. Saved drives stay on this iPhone until you delete the app."
    static let revoke = " Apple has not confirmed the Sign in with Apple disconnect yet; you can remove Scenic Drive "
        + "yourself in the Settings app, under your name, Sign in with Apple."
    static let plans = " A route remembered for rerouting can last up to 12 hours before it expires."
    static let notDeleted = "Scenic Drive couldn't delete your account right now. Your account was not deleted. "
        + "Try again later."

    static let rows: [(AccountOutcome, String)] = [
        (.deleted(revokePending: false, plansPending: false), deleted),
        (.deleted(revokePending: true, plansPending: false), deleted + revoke),
        (.deleted(revokePending: false, plansPending: true), deleted + plans),
        (.deleted(revokePending: true, plansPending: true), deleted + revoke + plans),
        (.offline, "Couldn't reach Scenic Drive, so nothing was deleted. Check your connection and try again."),
        (.noSession, "Couldn't start a secure connection to Scenic Drive, so nothing was deleted. "
            + "Check your connection and try again."),
        (.unreadable, "Scenic Drive answered, but the deletion couldn't be confirmed. Try again - deleting twice is safe."),
        (.unauthorized, notDeleted),
        (.methodRefused, notDeleted),
        (.authUnavailable, notDeleted),
        (.accountUnavailable, notDeleted),
        (.unexpected(500), notDeleted),
        (.unexpected(429), notDeleted),
    ]

    @Test("Every outcome's note, by full equality")
    func everyNote() {
        for (outcome, note) in Self.rows {
            #expect(AccountDeletionCopy.note(for: outcome) == note, "\(outcome)")
        }
    }
}
