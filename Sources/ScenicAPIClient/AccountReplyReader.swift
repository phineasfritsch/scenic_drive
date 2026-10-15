import Foundation

/// One DELETE /account reply to one `AccountOutcome` (T-0356 R2), fail closed: a 200 is `deleted` only when its body
/// is a JSON object of exactly the keys deleted (true), revoke_pending and plans_pending (JSON booleans - the
/// decoder refuses a number or a string for a Bool).
enum AccountReplyReader {
    static let deletedKeys: Set<String> = ["deleted", "plans_pending", "revoke_pending"]

    private struct Deleted: Decodable {
        let deleted: Bool
        let revoke_pending: Bool
        let plans_pending: Bool
    }

    private struct Failure: Decodable {
        let error: String
    }

    static func read(_ reply: PlanHTTPReply) -> AccountOutcome {
        switch reply.status {
        case 200: return deleted(reply.body) ?? .unreadable
        case 401: return .unauthorized
        case 405: return .methodRefused
        case 503:
            switch (try? JSONDecoder().decode(Failure.self, from: reply.body))?.error {
            case "auth_unavailable": return .authUnavailable
            case "account_unavailable": return .accountUnavailable
            default: return .unexpected(503)
            }
        default: return .unexpected(reply.status)
        }
    }

    private static func deleted(_ body: Data) -> AccountOutcome? {
        guard let object = (try? JSONSerialization.jsonObject(with: body)) as? [String: Any],
              Set(object.keys) == deletedKeys,
              let wire = try? JSONDecoder().decode(Deleted.self, from: body), wire.deleted
        else { return nil }
        return .deleted(revokePending: wire.revoke_pending, plansPending: wire.plans_pending)
    }
}
