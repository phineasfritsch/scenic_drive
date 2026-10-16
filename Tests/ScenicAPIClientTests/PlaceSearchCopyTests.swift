import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0362 A5 (R1, R5, R8): every SearchOutcome -> its exact PlaceSearchAnswer, and the reader's `place` field through
/// SearchClient.search, the entry point the app calls: the Worker's id spelling only, anything else unreadable.
@Suite("PlaceSearchCopyTests") struct PlaceSearchCopyTests {
    static let at = Coordinate(latitude: 34.13, longitude: -118.45)
    static let label = "Mulholland Drive, Los Angeles, California"
    static let row = SearchResult(label: label, coordinate: at, place: -42)
    static let bare = SearchResult(label: "Topanga, California", coordinate: at, place: nil)

    static let table: [(SearchOutcome, PlaceSearchAnswer)] = [
        (.results([row, bare]), .places([PlanPlace(id: -42, name: label, coordinate: at)])),
        (.results([]), .notice("No address matched. Try a street and a city.")),
        (.results([bare]), .notice("Address search found places but can't plan to them right now.")),
        (.refusedOnDevice, .notice("That search can't be sent. Shorten it and try again.")),
        (.invalidRequest, .notice("That search wasn't accepted. Edit it and try again.")),
        (.unauthorized, .notice("Your session has expired. Try the search again.")),
        (.methodRefused, .notice("Address search needs a newer version of the app.")),
        (.quotaExhausted, .notice("You've used today's address searches. Named places still work.")),
        (.paused, .notice("Search is paused right now. Named places still work.")),
        (.unavailable, .notice("Address search isn't available yet. Named places still work.")),
        (.failed, .notice("Address search didn't answer. Try again in a moment.")),
        (.unreadable, .notice("Address search sent an answer this app can't read. Try again in a moment.")),
        (.unexpected(418), .notice("Address search answered unexpectedly (HTTP 418). Try again in a moment.")),
        (.offline, .notice("You're offline. Named places still work.")),
    ]

    @Test("every SearchOutcome case has its own exact answer, and no two non-result cases share copy")
    func everyOutcome() {
        #expect(Self.table.map { PlaceSearchCopy.answer($0.0) } == Self.table.map(\.1))
        let notices = Self.table.dropFirst(1).map { "\($0.1)" }
        #expect(Set(notices).count == notices.count)
        #expect(Self.table.count == 14)
    }

    static func read(_ place: String) async -> SearchOutcome {
        let body = #"{"results":[{"label":"Mulholland Drive","lat":34.13,"lon":-118.45,"place":"# + place + "}]}"
        let fake = CountingPlanTransport(reply: PlanHTTPReply(status: 200, body: Data(body.utf8)))
        let client = SearchClient(base: URL(string: "https://scenic-api.test")!, transport: fake,
                                  installID: FixedInstallID("0F8B6D5E-1A2B-4C3D-8E9F-0123456789AB"),
                                  accountToken: nil, session: nil)
        return await client.search("Mulholland Drive", near: nil)
    }

    static func one(_ place: Int64?) -> SearchOutcome {
        .results([SearchResult(label: "Mulholland Drive", coordinate: at, place: place)])
    }

    @Test("the Worker's id spellings are read as that Int64; every near-miss makes the answer unreadable")
    func placeField() async {
        let rows: [(String, SearchOutcome)] = [
            (#""-1""#, Self.one(-1)),
            (#""-9007199254740991""#, Self.one(-9_007_199_254_740_991)),
            (#""-42""#, Self.one(-42)),
            (#""-9007199254740992""#, .unreadable),
            (#""0""#, .unreadable), (#""-0""#, .unreadable), (#""1""#, .unreadable), (#""-01""#, .unreadable),
            (#""+1""#, .unreadable), (#"" -1""#, .unreadable), (#""-1 ""#, .unreadable), (#""""#, .unreadable),
            ("-42", .unreadable), ("true", .unreadable), ("null", .unreadable),
        ]
        var answered: [SearchOutcome] = []
        for (place, _) in rows { answered.append(await Self.read(place)) }
        #expect(answered == rows.map(\.1))
    }
}
