import Foundation
import ScenicAPIClient
import Testing

/// T-0394 A1 (R3, R4): APIBaseURL.resolve, the one rule LiveBaseURL.url - the app's only base URL - is built from,
/// over every bound of the parse and of the DEBUG override's precedence, compared by whole `absoluteString`; and the
/// SHIPPED Info.plist value through the same call.
@Suite("APIBaseURLTests") struct APIBaseURLTests {
    static let pilot = "https://scenic-api.phineas-fritsch.workers.dev"

    /// (bundled, override, expected absoluteString or nil)
    static let table: [(String?, String?, String?)] = [
        (nil, nil, nil),
        ("", nil, nil),
        (" ", nil, nil),
        (" \(pilot)", nil, nil),
        ("\(pilot) ", nil, nil),
        ("http://scenic-api.phineas-fritsch.workers.dev", nil, nil),
        ("HTTPS://scenic-api.phineas-fritsch.workers.dev", nil, nil),
        ("ftp://scenic-api.phineas-fritsch.workers.dev", nil, nil),
        ("scenic-api.phineas-fritsch.workers.dev", nil, nil),
        ("https://", nil, nil),
        ("https:///", nil, nil),
        ("https:scenic-api.phineas-fritsch.workers.dev", nil, nil),
        ("$(SCENIC_API_BASE_URL)", nil, nil),
        ("https://exa mple.dev", nil, nil),
        ("\(pilot)?x=1", nil, nil),
        ("\(pilot)#top", nil, nil),
        ("https://me@scenic-api.phineas-fritsch.workers.dev", nil, nil),
        ("https://me:pw@scenic-api.phineas-fritsch.workers.dev", nil, nil),
        ("https://:pw@scenic-api.phineas-fritsch.workers.dev", nil, nil),
        ("https://:443", nil, nil),
        ("https://:443/", nil, nil),
        ("https://@", nil, nil),
        ("https://@:443", nil, nil),
        ("https://a.dev/p q", nil, nil),
        ("https://a.dev/p\tq", nil, nil),
        ("https://a.dev/p\nq", nil, nil),
        ("https://a.dev/p\u{A0}q", nil, nil),
        ("https://a.dev/p", nil, "https://a.dev/p"),
        (pilot, nil, pilot),
        ("\(pilot)/", nil, pilot),
        ("\(pilot)//", nil, pilot),
        ("https://example.dev:8443/api/", nil, "https://example.dev:8443/api"),
        (pilot, "https://dev.example.dev", "https://dev.example.dev"),
        (pilot, "https://dev.example.dev/", "https://dev.example.dev"),
        (pilot, "", nil),
        (pilot, "off", nil),
        (pilot, "http://localhost:8787", nil),
        (nil, "https://dev.example.dev", "https://dev.example.dev"),
        (nil, "off", nil),
        ("", "https://dev.example.dev", "https://dev.example.dev"),
    ]

    @Test func resolveMatchesTheTableRowByRow() {
        for (bundled, override, expected) in Self.table {
            let got = APIBaseURL.resolve(bundled: bundled, override: override)
            #expect(got?.absoluteString == expected,
                    "bundled \(String(describing: bundled)) override \(String(describing: override))")
        }
    }

    @Test func everyAcceptedBaseComposesThePlanPathExactly() {
        for (bundled, override, expected) in Self.table {
            guard let expected else { continue }
            let got = APIBaseURL.resolve(bundled: bundled, override: override)
            #expect(got?.appendingPathComponent("plan").absoluteString == expected + "/plan")
        }
    }

    /// T-0394 rv1 B3: a GENERATED near-miss corpus, so the whitespace rule - not whatever URLComponents happens to
    /// refuse - carries every refusal. Every seed is an ACCEPTED base; every whitespace character is inserted at
    /// every position of every seed, and each result must resolve to nil, as bundled and as override.
    static let seeds = [pilot, pilot + "/", pilot + "/p", "https://example.dev:8443/api/v1"]
    static let whitespace: [String] = [" ", "\t", "\n", "\r", "\r\n", "\u{0B}", "\u{0C}", "\u{85}", "\u{A0}",
                                       "\u{1680}", "\u{2000}", "\u{2009}", "\u{200A}", "\u{2028}", "\u{2029}",
                                       "\u{202F}", "\u{205F}", "\u{3000}"]

    static func nearMisses(of seed: String) -> [String] {
        let chars = Array(seed)
        return whitespace.flatMap { w in
            (0...chars.count).map { i in String(chars[..<i]) + w + String(chars[i...]) }
        }
    }

    @Test func theSeedsAreAcceptedAndEveryWhitespaceIsAWhitespace() {
        for seed in Self.seeds {
            #expect(APIBaseURL.resolve(bundled: seed, override: nil) != nil, "\(seed)")
        }
        for w in Self.whitespace {
            #expect(w.contains(where: { $0.isWhitespace }), "\(w.unicodeScalars.map(\.value))")
        }
        #expect(Self.seeds.allSatisfy { Self.nearMisses(of: $0).count == Self.whitespace.count * ($0.count + 1) })
    }

    @Test func whitespaceInsertedAnywhereInAnAcceptedBaseIsRefused() {
        for seed in Self.seeds {
            for text in Self.nearMisses(of: seed) {
                #expect(APIBaseURL.resolve(bundled: text, override: nil) == nil, "bundled \(text.debugDescription)")
                #expect(APIBaseURL.resolve(bundled: Self.pilot, override: text) == nil,
                        "override \(text.debugDescription)")
            }
        }
    }

    @Test func theKeysAreTheShippedSpellings() {
        #expect(APIBaseURL.infoPlistKey == "SCENIC_API_BASE_URL")
        #expect(APIBaseURL.overrideKey == "plan.base.url")
    }

    /// A TestFlight or home-screen launch passes no override: the value the app ships in its Info.plist alone.
    @Test func shippedInfoPlistResolvesToThePilot() throws {
        let plist = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .deletingLastPathComponent().appendingPathComponent("apps/ios/ScenicDrive/Info.plist")
        let data = try Data(contentsOf: plist)
        let dict = try #require(try PropertyListSerialization.propertyList(from: data, format: nil) as? [String: Any])
        let got = APIBaseURL.resolve(bundled: dict[APIBaseURL.infoPlistKey] as? String, override: nil)
        #expect(got?.absoluteString == Self.pilot)
        #expect(got?.appendingPathComponent("plan").absoluteString == Self.pilot + "/plan")
    }
}
