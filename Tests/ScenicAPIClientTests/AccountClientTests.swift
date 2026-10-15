import Foundation
import ScenicAPIClient
import Testing

/// T-0356 A1, A2 (R2, R4): the one DELETE /account request by exact equality to a literal, every answer account.ts
/// can give mapped to one AccountOutcome by full equality, zero requests without a session, and at most one renewed
/// retry after a 401. Every case drives `AccountClient.deleteAccount()`, the entry point `AccountDeletion.run()` calls.
@Suite("AccountClientTests") struct AccountClientTests {
    static let base = URL(string: "https://scenic-api.test")!
    static let first = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhIn0.Zmlyc3Q"
    static let second = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJiIn0.c2Vjb25k"

    static func request(_ token: String) -> PlanHTTPRequest {
        PlanHTTPRequest(url: URL(string: "https://scenic-api.test/account")!, method: "DELETE",
                        headers: ["authorization": "Bearer " + token], body: Data())
    }

    static func reply(_ status: Int, _ body: String) -> PlanHTTPReply {
        PlanHTTPReply(status: status, body: Data(body.utf8))
    }

    static func run(_ replies: [PlanHTTPReply], tokens: [String?] = [first])
        async -> (AccountOutcome, [PlanHTTPRequest], [String]) {
        let transport = ScriptedTransport(replies.isEmpty ? [:] : ["DELETE /account": replies])
        let session = ScriptedAccountSession(tokens)
        let outcome = await AccountClient(base: base, transport: transport, session: session).deleteAccount()
        return (outcome, await transport.requests, await session.rejected)
    }

    @Test("DELETE /account is exactly the Bearer and nothing else: no body, no device header, no content type")
    func exactRequest() async {
        let (outcome, requests, rejected) = await Self.run([Self.reply(200,
            #"{"deleted":true,"revoke_pending":false,"plans_pending":false}"#)])
        #expect(requests == [Self.request(Self.first)])
        #expect(outcome == .deleted(revokePending: false, plansPending: false))
        #expect(rejected == [])
    }

    @Test("No session token is noSession with zero requests", arguments: [[String?](), [nil], [""]])
    func noSession(_ tokens: [String?]) async {
        let (outcome, requests, _) = await Self.run([Self.reply(200, "{}")], tokens: tokens)
        #expect(outcome == .noSession)
        #expect(requests == [])
    }

    struct AnswerRow: Sendable, CustomTestStringConvertible {
        let status: Int
        let body: String
        let outcome: AccountOutcome
        var testDescription: String { "\(status) \(body)" }
    }

    static let answers: [AnswerRow] = [
        AnswerRow(status: 200, body: #"{"deleted":true,"revoke_pending":false,"plans_pending":false}"#,
                  outcome: .deleted(revokePending: false, plansPending: false)),
        AnswerRow(status: 200, body: #"{"deleted":true,"revoke_pending":true,"plans_pending":false}"#,
                  outcome: .deleted(revokePending: true, plansPending: false)),
        AnswerRow(status: 200, body: #"{"deleted":true,"revoke_pending":false,"plans_pending":true}"#,
                  outcome: .deleted(revokePending: false, plansPending: true)),
        AnswerRow(status: 200, body: #"{"plans_pending":true,"revoke_pending":true,"deleted":true}"#,
                  outcome: .deleted(revokePending: true, plansPending: true)),
        AnswerRow(status: 200, body: "not json", outcome: .unreadable),
        AnswerRow(status: 200, body: "", outcome: .unreadable),
        AnswerRow(status: 200, body: #"[{"deleted":true,"revoke_pending":false,"plans_pending":false}]"#,
                  outcome: .unreadable),
        AnswerRow(status: 200, body: #"{"deleted":false,"revoke_pending":false,"plans_pending":false}"#,
                  outcome: .unreadable),
        AnswerRow(status: 200, body: #"{"revoke_pending":false,"plans_pending":false}"#, outcome: .unreadable),
        AnswerRow(status: 200, body: #"{"deleted":true,"plans_pending":false}"#, outcome: .unreadable),
        AnswerRow(status: 200, body: #"{"deleted":true,"revoke_pending":false}"#, outcome: .unreadable),
        AnswerRow(status: 200, body: #"{"deleted":1,"revoke_pending":false,"plans_pending":false}"#,
                  outcome: .unreadable),
        AnswerRow(status: 200, body: #"{"deleted":"true","revoke_pending":false,"plans_pending":false}"#,
                  outcome: .unreadable),
        AnswerRow(status: 200, body: #"{"deleted":true,"revoke_pending":0,"plans_pending":false}"#,
                  outcome: .unreadable),
        AnswerRow(status: 200, body: #"{"deleted":true,"revoke_pending":false,"plans_pending":null}"#,
                  outcome: .unreadable),
        AnswerRow(status: 200, body: #"{"deleted":true,"revoke_pending":false,"plans_pending":false,"x":1}"#,
                  outcome: .unreadable),
        AnswerRow(status: 405, body: #"{"error":"DELETE only"}"#, outcome: .methodRefused),
        AnswerRow(status: 503, body: #"{"error":"auth_unavailable"}"#, outcome: .authUnavailable),
        AnswerRow(status: 503, body: #"{"error":"account_unavailable"}"#, outcome: .accountUnavailable),
        AnswerRow(status: 503, body: #"{"error":"planning_paused"}"#, outcome: .unexpected(503)),
        AnswerRow(status: 503, body: "", outcome: .unexpected(503)),
        AnswerRow(status: 400, body: #"{"error":"invalid_request"}"#, outcome: .unexpected(400)),
        AnswerRow(status: 404, body: #"{"error":"not found"}"#, outcome: .unexpected(404)),
        AnswerRow(status: 429, body: #"{"error":"quota_exhausted"}"#, outcome: .unexpected(429)),
        AnswerRow(status: 500, body: "", outcome: .unexpected(500)),
        AnswerRow(status: 201, body: #"{"deleted":true,"revoke_pending":false,"plans_pending":false}"#,
                  outcome: .unexpected(201)),
    ]

    @Test("Every answer is one outcome after exactly one request", arguments: answers)
    func everyAnswer(_ row: AnswerRow) async {
        let (outcome, requests, rejected) = await Self.run([Self.reply(row.status, row.body)])
        #expect(outcome == row.outcome)
        #expect(requests == [Self.request(Self.first)])
        #expect(rejected == [])
    }

    @Test("No reply at all is offline after one request")
    func offline() async {
        let (outcome, requests, _) = await Self.run([])
        #expect(outcome == .offline)
        #expect(requests == [Self.request(Self.first)])
    }

    @Test("A 401 hands the token back and retries ONCE with the renewed token; its answer is the outcome")
    func renewedOnce() async {
        let deleted = Self.reply(200, #"{"deleted":true,"revoke_pending":false,"plans_pending":false}"#)
        let (outcome, requests, rejected) = await Self.run([Self.reply(401, #"{"error":"unauthorized"}"#), deleted],
                                                           tokens: [Self.first, Self.second])
        #expect(outcome == .deleted(revokePending: false, plansPending: false))
        #expect(requests == [Self.request(Self.first), Self.request(Self.second)])
        #expect(rejected == [Self.first])
    }

    @Test("A second 401 is unauthorized after two requests, both tokens handed back")
    func secondUnauthorized() async {
        let (outcome, requests, rejected) = await Self.run([Self.reply(401, #"{"error":"unauthorized"}"#)],
                                                           tokens: [Self.first, Self.second])
        #expect(outcome == .unauthorized)
        #expect(requests == [Self.request(Self.first), Self.request(Self.second)])
        #expect(rejected == [Self.first, Self.second])
    }

    @Test("A 401 whose renewal yields no token or the same token is unauthorized after one request",
          arguments: [[first, nil], [first, first], [first, ""]])
    func noRenewal(_ tokens: [String?]) async {
        let (outcome, requests, rejected) = await Self.run([Self.reply(401, #"{"error":"unauthorized"}"#)],
                                                           tokens: tokens)
        #expect(outcome == .unauthorized)
        #expect(requests == [Self.request(Self.first)])
        #expect(rejected == [Self.first])
    }
}
