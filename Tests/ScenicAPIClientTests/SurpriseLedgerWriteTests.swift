import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0310 acceptance 3 (R7, R8, P-PRIV-05): the card's step - `SurpriseShowing.recording`, then
/// `LedgerSurpriseSource.recordShown` - over {no session, session, ledger 429, ledger 401}: the device history and
/// the WHOLE request list by full equality. The cell sent is the PLACE's: the cell function answers only for a, b
/// and c's own coordinates, so any other coordinate sends nothing and the request list differs; d has no cell at all,
/// so it is in the device history and never posted - shown between a and b, so the 401 row sees it too.
@Suite("SurpriseLedgerWriteTests") struct SurpriseLedgerWriteTests {
    static let day = CivilDate(year: 2026, month: 10, day: 7)

    static func place(_ id: String, _ category: SurpriseCategory, _ corridor: String, _ lat: Double,
                      _ lon: Double) -> SurpriseCandidate {
        SurpriseCandidate(id: id, name: "Place \(id)", hook: "A hook.", category: category, corridor: corridor,
                          brand: nil, coordinate: Coordinate(latitude: lat, longitude: lon), quality: 3,
                          approachScore: 3, dwellMinutes: 30, opensMinute: nil, closesMinute: nil, hoursExempt: true,
                          lit: false, unpaved: false, privateApproach: false)
    }

    static let a = place("1234567", .viewpoint, "pch", 34.0901, -118.6012)
    static let b = place("7654321", .park, "topanga", 34.1102, -118.7203)
    static let c = place("42", .trailhead, "mulholland", 34.1303, -118.7504)
    static let d = place("31337", .viewpoint, "decker", 34.1504, -118.8105)
    static let cells: [Coordinate: String] = [a.coordinate: "85283473fffffff", b.coordinate: "850dab63fffffff",
                                              c.coordinate: "852a1073fffffff"]
    /// The card's showings in order: a, a again (a re-render), d (no cell), b, c.
    static let shownOrder = [a, a, d, b, c]

    static func shown(_ p: SurpriseCandidate) -> SurpriseHistory.Shown {
        SurpriseHistory.Shown(candidateId: p.id, category: p.category, corridor: p.corridor, date: day)
    }

    struct Row: Sendable, CustomTestStringConvertible {
        let label: String
        let stored: KeychainRead<SessionRecord>
        let supported: Bool
        let ledger: PlanHTTPReply
        let requests: [PlanHTTPRequest]
        var testDescription: String { label }
    }

    static let live = KeychainRead.valid(AttestWire.stored(1800))
    static let recorded = AttestWire.reply(200, "{\"recorded\":true}")
    static let capped = AttestWire.reply(429, "{\"error\":\"ledger_daily_cap\"}")
    static let unauthorized = AttestWire.reply(401, "{\"error\":\"unauthorized\"}")

    static func posts(_ token: String, _ places: [SurpriseCandidate]) -> [PlanHTTPRequest] {
        places.map { AttestWire.ledgerPost(token, $0.id, cells[$0.coordinate]!) }
    }

    static let rows: [Row] = [
        Row(label: "no session", stored: .absent, supported: false, ledger: recorded, requests: []),
        Row(label: "session", stored: live, supported: true, ledger: recorded,
            requests: posts(AttestWire.oldToken, [a, b, c])),
        Row(label: "ledger 429", stored: live, supported: true, ledger: capped,
            requests: posts(AttestWire.oldToken, [a, b, c])),
        Row(label: "ledger 401", stored: live, supported: true, ledger: unauthorized,
            requests: posts(AttestWire.oldToken, [a]) + [AttestWire.challengeRequest(),
                                                          AttestWire.renewRequest(AttestWire.oldKey)]
                + posts(AttestWire.newToken, [b])),
    ]

    static func source(_ row: Row) -> (LedgerSurpriseSource, ScriptedTransport) {
        let transport = ScriptedTransport(["POST /attest/challenge": [AttestWire.challengeReply],
                                           "POST /attest/assert": [AttestWire.sessionReply],
                                           "POST /ledger": [row.ledger],
                                           "GET /ledger": [AttestWire.reply(200, "{\"places\":[]}")]])
        let session = SessionStore(client: AttestWire.client(transport),
                                   attester: FakeAttester(isSupported: row.supported),
                                   storage: MemorySessionStorage(row.stored), now: { AttestWire.now })
        let cells = Self.cells
        return (LedgerSurpriseSource(client: LedgerClient(base: AttestWire.base, transport: transport, session: session),
                                     cellOf: { cells[$0] }), transport)
    }

    @Test("Each shown place is in the device history once, and posted with its own cell as the session allows",
          arguments: rows)
    func showings(_ row: Row) async {
        let (source, transport) = Self.source(row)
        var history = SurpriseHistory(feedback: [])
        for place in Self.shownOrder {
            guard let next = SurpriseShowing.recording(place, on: Self.day, in: history) else { continue }
            history = next
            await source.recordShown(place)
        }
        #expect(history == SurpriseHistory(shown: [Self.shown(Self.a), Self.shown(Self.d), Self.shown(Self.b),
                                                   Self.shown(Self.c)]))
        #expect(await transport.requests == row.requests)
    }

    @Test("The ledger's rows become the card's ledger places, in the Worker's order; any other answer is nil")
    func ledgerPlaces() async {
        let body = "{\"places\":[{\"place_id\":\"7654321\",\"cell\":\"850dab63fffffff\",\"day\":\"2026-10-06\"},"
            + "{\"place_id\":\"1234567\",\"cell\":\"85283473fffffff\",\"day\":\"2026-06-10\"}]}"
        let transport = CountingPlanTransport(reply: AttestWire.reply(200, body))
        let source = LedgerSurpriseSource(client: LedgerClient(base: AttestWire.base, transport: transport,
                                                               session: FixedLedgerSession(token: AttestWire.oldToken)),
                                          cellOf: { _ in nil })
        #expect(await source.ledgerPlaces() == [
            SurpriseLedgerPlace(candidateId: "7654321", date: CivilDate(year: 2026, month: 10, day: 6)),
            SurpriseLedgerPlace(candidateId: "1234567", date: CivilDate(year: 2026, month: 6, day: 10)),
        ])
        let refused = LedgerSurpriseSource(client: LedgerClient(base: AttestWire.base,
                                                                transport: CountingPlanTransport(reply: Self.unauthorized),
                                                                session: FixedLedgerSession(token: AttestWire.oldToken)),
                                           cellOf: { _ in nil })
        #expect(await refused.ledgerPlaces() == nil)
    }
}
