import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0307 acceptance 2 (R2-R4): the exact GET and POST /ledger requests, the rows parsed by full equality to the
/// rows the body was built from, one typed outcome per Worker answer, at most one request per call - a 429 or a 401
/// is never retried - and zero requests without a session or for an entry the Worker would refuse. Every case
/// drives `LedgerClient.record` or `LedgerClient.read`, the entry points the app calls.
@Suite("LedgerClientTests") struct LedgerClientTests {
    static let token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ4In0.c2ln"
    static let cellA = "85283473fffffff"
    static let cellB = "850dab63fffffff"
    static let ledgerURL = URL(string: "https://scenic-api.test/ledger")!

    static func client(_ fake: CountingPlanTransport, token: String? = token) -> LedgerClient {
        LedgerClient(base: URL(string: "https://scenic-api.test")!, transport: fake,
                     session: FixedLedgerSession(token: token))
    }

    static func reply(_ status: Int, _ body: String) -> CountingPlanTransport {
        CountingPlanTransport(reply: PlanHTTPReply(status: status, body: Data(body.utf8)))
    }

    static func wire(_ row: LedgerRow) -> String {
        let day = String(format: "%04d-%02d-%02d", row.day.year, row.day.month, row.day.day)
        return "{\"place_id\":\"\(row.placeId)\",\"cell\":\"\(row.cell)\",\"day\":\"\(day)\"}"
    }

    @Test("POST /ledger is exactly the bearer, the content type and {cell, place_id}",
          arguments: [("1", cellA), ("9223372036854775807", cellB), ("1234567890123", cellA)])
    func postRequest(_ placeId: String, _ cell: String) async {
        let fake = Self.reply(200, #"{"recorded":true}"#)
        let outcome = await Self.client(fake).record(placeId: placeId, cell: cell)
        let expected = PlanHTTPRequest(url: Self.ledgerURL, method: "POST",
                                       headers: ["authorization": "Bearer \(Self.token)",
                                                 "content-type": "application/json"],
                                       body: Data("{\"cell\":\"\(cell)\",\"place_id\":\"\(placeId)\"}".utf8))
        #expect(await fake.requests == [expected])
        #expect(outcome == .recorded)
    }

    @Test("GET /ledger is exactly the bearer, no body, and its rows parse to the rows the body was built from")
    func getRequestAndRows() async {
        let rows = [LedgerRow(placeId: "42", cell: Self.cellA, day: CivilDate(year: 2026, month: 12, day: 31)),
                    LedgerRow(placeId: "9223372036854775807", cell: Self.cellB,
                              day: CivilDate(year: 2026, month: 1, day: 1)),
                    LedgerRow(placeId: "7", cell: Self.cellA, day: CivilDate(year: 2024, month: 2, day: 29)),
                    LedgerRow(placeId: "8", cell: Self.cellB, day: CivilDate(year: 2000, month: 2, day: 29))]
        let fake = Self.reply(200, "{\"places\":[" + rows.map(Self.wire).joined(separator: ",") + "]}")
        let outcome = await Self.client(fake).read()
        #expect(await fake.requests == [PlanHTTPRequest(url: Self.ledgerURL, method: "GET",
                                                        headers: ["authorization": "Bearer \(Self.token)"],
                                                        body: Data())])
        #expect(outcome == .places(rows))
    }

    @Test("A GET body that is not {places: [{place_id, cell, day}]} with real days is unreadable", arguments: [
        #"{"places":[{"place_id":"1","cell":"85283473fffffff","day":"2026-13-01"}]}"#,
        #"{"places":[{"place_id":"1","cell":"85283473fffffff","day":"2026-00-10"}]}"#,
        #"{"places":[{"place_id":"1","cell":"85283473fffffff","day":"2026-02-29"}]}"#,
        #"{"places":[{"place_id":"1","cell":"85283473fffffff","day":"2100-02-29"}]}"#,
        #"{"places":[{"place_id":"1","cell":"85283473fffffff","day":"2026x10-01"}]}"#,
        #"{"places":[{"place_id":"1","cell":"85283473fffffff","day":"2026-04-31"}]}"#,
        #"{"places":[{"place_id":"1","cell":"85283473fffffff","day":"2026-10-00"}]}"#,
        #"{"places":[{"place_id":"1","cell":"85283473fffffff","day":"2026-1-011"}]}"#,
        #"{"places":[{"place_id":"1","cell":"85283473fffffff","day":"2026-10-1"}]}"#,
        #"{"places":[{"place_id":"1","cell":"85283473fffffff","day":"+026-10-01"}]}"#,
        #"{"places":[{"place_id":"1","day":"2026-10-01"}]}"#,
        #"{"places":{}}"#, #"{}"#, "not json",
    ])
    func unreadableRows(_ body: String) async {
        let fake = Self.reply(200, body)
        #expect(await Self.client(fake).read() == .unreadable)
        #expect(await fake.count == 1)
    }

    struct Answer: Sendable {
        let read: Bool
        let status: Int
        let body: String
        let outcome: LedgerOutcome
    }

    static let answers: [Answer] = [
        Answer(read: false, status: 200, body: #"{"recorded":true}"#, outcome: .recorded),
        Answer(read: false, status: 200, body: #"{"recorded":false}"#, outcome: .unreadable),
        Answer(read: false, status: 200, body: #"{"places":[]}"#, outcome: .unreadable),
        Answer(read: true, status: 200, body: #"{"places":[]}"#, outcome: .places([])),
        Answer(read: true, status: 200, body: #"{"recorded":true}"#, outcome: .unreadable),
        Answer(read: false, status: 400, body: #"{"error":"invalid_request","detail":"x"}"#, outcome: .invalidRequest),
        Answer(read: false, status: 401, body: #"{"error":"unauthorized"}"#, outcome: .unauthorized),
        Answer(read: true, status: 401, body: #"{"error":"unauthorized"}"#, outcome: .unauthorized),
        Answer(read: false, status: 405, body: #"{"error":"GET or POST only"}"#, outcome: .methodRefused),
        Answer(read: true, status: 405, body: #"{"error":"GET or POST only"}"#, outcome: .methodRefused),
        Answer(read: false, status: 429, body: #"{"error":"ledger_daily_cap"}"#, outcome: .dailyCap),
        Answer(read: false, status: 429, body: #"{"error":"rate_limited"}"#, outcome: .unexpected(429)),
        Answer(read: false, status: 429, body: "", outcome: .unexpected(429)),
        Answer(read: false, status: 503, body: #"{"error":"ledger_unavailable"}"#, outcome: .unavailable),
        Answer(read: true, status: 503, body: #"{"error":"auth_unavailable"}"#, outcome: .unavailable),
        Answer(read: false, status: 500, body: "", outcome: .unexpected(500)),
        Answer(read: true, status: 404, body: "", outcome: .unexpected(404)),
        Answer(read: false, status: 201, body: #"{"recorded":true}"#, outcome: .unexpected(201)),
    ]

    @Test("Every Worker answer is one typed outcome after exactly one request - never a retry",
          arguments: answers.indices)
    func answerTable(_ i: Int) async {
        let row = Self.answers[i]
        let fake = Self.reply(row.status, row.body)
        let client = Self.client(fake)
        let outcome = row.read ? await client.read() : await client.record(placeId: "5", cell: Self.cellA)
        #expect(outcome == row.outcome, "\(row.status) \(row.body)")
        #expect(await fake.count == 1, "\(row.status) \(row.body)")
    }

    @Test("No reply at all is offline, after exactly one request")
    func offline() async {
        let fake = CountingPlanTransport.offline()
        #expect(await Self.client(fake).record(placeId: "5", cell: Self.cellA) == .offline)
        #expect(await Self.client(fake).read() == .offline)
        #expect(await fake.count == 2)
    }

    @Test("Without a session nothing is sent", arguments: [nil, ""] as [String?])
    func noSession(_ token: String?) async {
        let fake = Self.reply(200, #"{"recorded":true}"#)
        #expect(await Self.client(fake, token: token).record(placeId: "5", cell: Self.cellA) == .noSession)
        #expect(await Self.client(fake, token: token).read() == .noSession)
        #expect(await fake.count == 0)
    }

    @Test("A place id or cell the Worker would refuse is refused on the device and nothing is sent", arguments: [
        ("0", cellA), ("01", cellA), ("-1", cellA), ("+1", cellA), ("", cellA), ("12a", cellA), (" 1", cellA),
        ("9223372036854775808", cellA), ("10000000000000000000", cellA), ("\u{0661}", cellA),
        ("5", "85283473FFFFFFF"), ("5", "85283473ffffff"), ("5", "85283473fffffff0"), ("5", ""),
        ("5", "85283473fffffg"), ("5", "8528347 fffffff"),
    ])
    func refusedOnDevice(_ placeId: String, _ cell: String) async {
        let fake = Self.reply(200, #"{"recorded":true}"#)
        #expect(await Self.client(fake).record(placeId: placeId, cell: cell) == .refusedOnDevice, "\(placeId) \(cell)")
        #expect(await fake.count == 0)
    }

    /// Both bounds of both classes and their outside neighbours ('/' 47, '0' 48, '9' 57, ':' 58, '`' 96, 'a' 97,
    /// 'f' 102, 'g' 103) and uppercase ('@' 64, 'A', 'F', 'G' 71), each put at every one of the 15 positions of a
    /// valid cell. Whether the cell is sent is a function of the character alone.
    static let cellCharacters: [(Character, Bool)] = [
        ("/", false), ("0", true), ("9", true), (":", false), ("`", false), ("a", true), ("f", true), ("g", false),
        ("@", false), ("A", false), ("F", false), ("G", false),
    ]
    static let cellCases: [(String, Bool)] = (0..<15).flatMap { position in
        cellCharacters.map { character, admitted in
            var cell = Array(cellA)
            cell[position] = character
            return (String(cell), admitted)
        }
    }

    @Test("Every cell position admits exactly 0-9 and a-f, at both bounds of each class", arguments: cellCases)
    func cellCharacterClass(_ cell: String, _ admitted: Bool) async {
        let fake = Self.reply(200, #"{"recorded":true}"#)
        let outcome = await Self.client(fake).record(placeId: "5", cell: cell)
        #expect(outcome == (admitted ? .recorded : .refusedOnDevice), "\(cell)")
        #expect(await fake.count == (admitted ? 1 : 0), "\(cell)")
    }

    /// The place id's digit class at both bounds ('0' 48, '9' 57) and just outside ('/' 47, ':' 58), each put at
    /// every one of the 19 positions of a valid id; '0' is refused at the first position alone (no leading zero).
    static let placeIdCharacters: [(Character, Bool)] = [("/", false), ("0", true), ("9", true), (":", false)]
    static let placeIdCases: [(String, Bool)] = (0..<19).flatMap { position in
        placeIdCharacters.map { character, admitted in
            var id = Array("1111111111111111111")
            id[position] = character
            return (String(id), admitted && !(position == 0 && character == "0"))
        }
    }

    @Test("Every place id position admits exactly 0-9 at both bounds, and a leading 0 nowhere",
          arguments: placeIdCases)
    func placeIdCharacterClass(_ placeId: String, _ admitted: Bool) async {
        let fake = Self.reply(200, #"{"recorded":true}"#)
        let outcome = await Self.client(fake).record(placeId: placeId, cell: Self.cellA)
        #expect(outcome == (admitted ? .recorded : .refusedOnDevice), "\(placeId)")
        #expect(await fake.count == (admitted ? 1 : 0), "\(placeId)")
    }

    /// Every position of a valid day given each character just outside its class: at the two separators the
    /// neighbours of '-' (',' 44, '.' 46), digits at both bounds and other punctuation; at the eight digit positions
    /// the neighbours of 0-9 ('/' 47, ':' 58), '-', a letter and a space.
    static let dayRefusals: [String] = (0..<10).flatMap { position -> [String] in
        let swaps: [Character] = position == 4 || position == 7
            ? [",", ".", "/", "0", "9", ":", "x", " "] : ["/", ":", "-", "x", " "]
        return swaps.map { character in
            var day = Array("2026-10-01")
            day[position] = character
            return String(day)
        }
    }

    static func dayBody(_ day: String) -> String {
        #"{"places":[{"place_id":"1","cell":"85283473fffffff","day":"\#(day)"}]}"#
    }

    @Test("Every day separator and digit position refuses its out-of-class neighbours", arguments: dayRefusals)
    func dayCharacterClass(_ day: String) async {
        let fake = Self.reply(200, Self.dayBody(day))
        #expect(await Self.client(fake).read() == .unreadable, "\(day)")
        #expect(await fake.count == 1)
    }

    /// '0' at every digit position and '9' at every digit position that can hold one in a real day (not the month's
    /// or the day's tens).
    @Test("A day with 0 or 9 at each digit position that can hold one is read as that day", arguments: [
        ("0000-01-01", 0, 1, 1), ("9999-12-31", 9999, 12, 31), ("2026-09-19", 2026, 9, 19),
        ("2026-10-10", 2026, 10, 10),
    ])
    func dayDigitBounds(_ day: String, _ year: Int, _ month: Int, _ date: Int) async {
        let fake = Self.reply(200, Self.dayBody(day))
        let row = LedgerRow(placeId: "1", cell: Self.cellA, day: CivilDate(year: year, month: month, day: date))
        #expect(await Self.client(fake).read() == .places([row]), "\(day)")
        #expect(await fake.count == 1)
    }
}
