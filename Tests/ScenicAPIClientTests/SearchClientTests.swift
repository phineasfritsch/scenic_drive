import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0359 acceptance A4 (R7): the exact POST /search request - url, method, headers and body bytes by full equality to
/// a written-out literal - with the bias rounded to 2 dp on the device; zero requests for a query or bias the Worker
/// would refuse, at every bound; and one typed outcome per Worker answer after exactly one request. Every case drives
/// `SearchClient.search`, the entry point the app calls.
@Suite("SearchClientTests") struct SearchClientTests {
    static let device = UUID(uuidString: "0F8B6D5E-1A2B-4C3D-8E9F-0123456789AB")!
    static let searchURL = URL(string: "https://scenic-api.test/search")!
    static let headers = ["content-type": "application/json", "x-scenic-device": "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab"]
    static let ok = #"{"results":[]}"#

    static func client(_ fake: CountingPlanTransport) -> SearchClient {
        SearchClient(base: URL(string: "https://scenic-api.test")!, transport: fake, device: device)
    }

    static func reply(_ status: Int, _ body: String) -> CountingPlanTransport {
        CountingPlanTransport(reply: PlanHTTPReply(status: status, body: Data(body.utf8)))
    }

    static func at(_ lat: Double, _ lon: Double) -> Coordinate { Coordinate(latitude: lat, longitude: lon) }

    static let car = "\u{1F697}"

    @Test("POST /search is exactly the content type, the device and the sorted-key body, the bias at 2 dp",
          arguments: [
              ("Mulholland Drive", nil, #"{"q":"Mulholland Drive"}"#),
              ("Mulholland Drive", at(34.13, -118.45), #"{"near":{"lat":34.13,"lon":-118.45},"q":"Mulholland Drive"}"#),
              ("x", at(34.126, -118.454), #"{"near":{"lat":34.13,"lon":-118.45},"q":"x"}"#),
              ("x", at(34.124, -118.446), #"{"near":{"lat":34.12,"lon":-118.45},"q":"x"}"#),
              ("x", at(-0.004, 0.004), #"{"near":{"lat":0,"lon":0},"q":"x"}"#),
              ("x", at(90, -180), #"{"near":{"lat":90,"lon":-180},"q":"x"}"#),
              ("x", at(-90, 180), #"{"near":{"lat":-90,"lon":180},"q":"x"}"#),
              ("x", at(89.996, 179.996), #"{"near":{"lat":90,"lon":180},"q":"x"}"#),
              ("a/b \"c\"", nil, #"{"q":"a/b \"c\""}"#),
              ("a", nil, #"{"q":"a"}"#),
              (String(repeating: "a", count: 100), nil, "{\"q\":\"" + String(repeating: "a", count: 100) + "\"}"),
              (String(repeating: "a", count: 98) + car, nil, "{\"q\":\"" + String(repeating: "a", count: 98) + car + "\"}"),
              (" Topanga ~", nil, #"{"q":" Topanga ~"}"#),
          ] as [(String, Coordinate?, String)])
    func request(_ query: String, _ near: Coordinate?, _ body: String) async {
        let fake = Self.reply(200, Self.ok)
        let outcome = await Self.client(fake).search(query, near: near)
        let expected = PlanHTTPRequest(url: Self.searchURL, method: "POST", headers: Self.headers, body: Data(body.utf8))
        #expect(await fake.requests == [expected])
        #expect(outcome == .results([]))
    }

    @Test("A query or bias the Worker would refuse is refused on the device and nothing is sent",
          arguments: [
              ("", nil), ("   ", nil), ("\u{FEFF}", nil), ("\u{3000}\u{A0}", nil),
              (String(repeating: "a", count: 101), nil), (String(repeating: "a", count: 99) + car, nil),
              ("a\u{1F}b", nil), ("a\u{0}b", nil), ("a\tb", nil), ("a\nb", nil), ("a\u{7F}b", nil),
              ("x", at(90.0001, 0)), ("x", at(-90.0001, 0)), ("x", at(0, 180.0001)), ("x", at(0, -180.0001)),
              ("x", at(.nan, 0)), ("x", at(0, .nan)), ("x", at(.infinity, 0)), ("x", at(0, -.infinity)),
          ] as [(String, Coordinate?)])
    func refused(_ query: String, _ near: Coordinate?) async {
        let fake = Self.reply(200, Self.ok)
        let outcome = await Self.client(fake).search(query, near: near)
        #expect(await fake.count == 0)
        #expect(outcome == .refusedOnDevice)
    }

    static func rows(_ n: Int) -> String {
        "{\"results\":[" + (0..<n).map { "{\"label\":\"Place \($0)\",\"lat\":34,\"lon\":-118.\($0)}" }.joined(separator: ",") + "]}"
    }

    static func places(_ n: Int) -> SearchOutcome {
        .results((0..<n).map { SearchResult(label: "Place \($0)", coordinate: at(34, Double("-118.\($0)")!)) })
    }

    static let answers: [(Int, String, SearchOutcome)] = [
        (200, #"{"results":[{"label":"23500 Mulholland Highway, Calabasas, California","lat":34.12,"lon":-118.66},{"label":"Topanga","lat":34.09,"lon":-118.6,"extra":1}]}"#,
         .results([SearchResult(label: "23500 Mulholland Highway, Calabasas, California", coordinate: at(34.12, -118.66)),
                   SearchResult(label: "Topanga", coordinate: at(34.09, -118.6))])),
        (200, ok, .results([])),
        (200, rows(8), places(8)),
        (200, rows(9), .unreadable),
        (200, #"{"results":[{"label":"N","lat":90,"lon":180},{"label":"S","lat":-90,"lon":-180}]}"#,
         .results([SearchResult(label: "N", coordinate: at(90, 180)), SearchResult(label: "S", coordinate: at(-90, -180))])),
        (200, #"{"results":[{"label":"","lat":34,"lon":-118}]}"#, .unreadable),
        (200, #"{"results":[{"label":" \n","lat":34,"lon":-118}]}"#, .unreadable),
        (200, #"{"results":[{"label":"x","lat":90.0001,"lon":-118}]}"#, .unreadable),
        (200, #"{"results":[{"label":"x","lat":-90.0001,"lon":-118}]}"#, .unreadable),
        (200, #"{"results":[{"label":"x","lat":34,"lon":180.0001}]}"#, .unreadable),
        (200, #"{"results":[{"label":"x","lat":34,"lon":-180.0001}]}"#, .unreadable),
        (200, #"{"results":[{"label":"x","lat":"34","lon":-118}]}"#, .unreadable),
        (200, #"{"results":[{"label":"x","lat":true,"lon":-118}]}"#, .unreadable),
        (200, #"{"results":[{"label":"x","lat":34}]}"#, .unreadable),
        (200, #"{"results":[{"label":7,"lat":34,"lon":-118}]}"#, .unreadable),
        (200, #"{"results":null}"#, .unreadable),
        (200, "{}", .unreadable),
        (200, "not json", .unreadable),
        (400, #"{"error":"invalid_request","detail":"q is only whitespace"}"#, .invalidRequest),
        (401, #"{"error":"session_rejected"}"#, .unauthorized),
        (405, #"{"error":"POST only"}"#, .methodRefused),
        (429, #"{"error":"quota_exhausted","resets_at":"2026-10-11T00:00:00.000Z"}"#, .quotaExhausted),
        (429, #"{"error":"slow_down"}"#, .unexpected(429)),
        (502, #"{"error":"search_failed"}"#, .failed),
        (502, "Bad Gateway", .unexpected(502)),
        (503, #"{"error":"planning_paused"}"#, .paused),
        (503, #"{"error":"search_unavailable"}"#, .unavailable),
        (503, #"{"error":"planning_unavailable"}"#, .unexpected(503)),
        (500, #"{"error":"search_failed"}"#, .unexpected(500)),
        (404, #"{"error":"not found"}"#, .unexpected(404)),
    ]

    @Test("Every Worker answer is one typed outcome after exactly one request - never a retry", arguments: answers)
    func outcome(_ status: Int, _ body: String, _ expected: SearchOutcome) async {
        let fake = Self.reply(status, body)
        let outcome = await Self.client(fake).search("Mulholland Drive", near: Self.at(34.13, -118.45))
        #expect(await fake.count == 1)
        #expect(outcome == expected)
    }

    @Test("A result carries the Worker's lat as its latitude and lon as its longitude, read field by field")
    func coordinate() async {
        let fake = Self.reply(200, #"{"results":[{"label":"Topanga","lat":34.09,"lon":-118.6}]}"#)
        guard case .results(let rows) = await Self.client(fake).search("Topanga", near: nil) else {
            Issue.record("a readable answer was not read as results")
            return
        }
        #expect(rows.map(\.label) == ["Topanga"])
        #expect(rows.map(\.coordinate.latitude) == [34.09])
        #expect(rows.map(\.coordinate.longitude) == [-118.6])
    }

    @Test("No reply at all is offline, after exactly one request")
    func offline() async {
        let fake = CountingPlanTransport.offline()
        let outcome = await Self.client(fake).search("Mulholland Drive", near: nil)
        #expect(await fake.count == 1)
        #expect(outcome == .offline)
    }
}
