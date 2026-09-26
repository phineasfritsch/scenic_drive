import Foundation
import Handoff
import Testing

/// THE DRAWN LINE IS CREDITED ON THE SURFACE (rv1-t0236 B1).
///
/// Binds the shipping entry point - `CreditLine.composed(basemap:routeData:)`, the one call the home screen hands
/// `AttributionFooter` (P-ATTR-01's check whitelists that form) - over every drive's shipping
/// `routeGeometryCredit`, against the two basemap credits READ from MapStyle.swift's approved declarations by
/// identifier. The app target cannot run on Linux, but its credit strings can be read where they are declared, so
/// this suite cannot hold a stale copy of either.
@Suite("CreditLine")
struct CreditLineTests {
    static let mapStyleSource = URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        .appendingPathComponent("apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapStyle.swift")

    /// The string literal of `public static let <name> = "..."` in MapStyle.swift, found by its identifier.
    static func declaredCredit(_ name: String) throws -> String {
        let source = try String(contentsOf: mapStyleSource, encoding: .utf8)
        let marker = "public static let \(name) = \""
        let lines = source.components(separatedBy: "\n").filter { $0.contains(marker) }
        #expect(lines.count == 1, "\(name) is declared \(lines.count) time(s) in MapStyle.swift")
        let line = try #require(lines.first)
        let tail = line.components(separatedBy: marker)[1]
        return try #require(tail.components(separatedBy: "\"").first)
    }

    static func occurrences(of needle: String, in text: String) -> Int {
        text.components(separatedBy: needle).count - 1
    }

    @Test("over the demo tiles the Saddle Peak pill names OpenStreetMap after the basemap's own credit")
    func demoTilesUnderTheLineNameOpenStreetMap() throws {
        let demo = try Self.declaredCredit("demoAttribution")
        #expect(!demo.contains("OpenStreetMap"), "the demo credit itself never names OpenStreetMap: \(demo)")
        let pill = CreditLine.composed(basemap: demo, routeData: HandoffDrive.saddlePeak.routeGeometryCredit)
        #expect(pill.contains("OpenStreetMap contributors"), "\(pill)")
        #expect(pill.hasPrefix(demo + CreditLine.separator), "the basemap's credit stays first and whole: \(pill)")
        #expect(pill == "© MapLibre · Natural Earth · © OpenStreetMap contributors")
    }

    @Test("over the LA Protomaps tiles the Saddle Peak pill names OpenStreetMap exactly once")
    func laTilesNameOpenStreetMapOnce() throws {
        let la = try Self.declaredCredit("protomapsAttribution")
        let pill = CreditLine.composed(basemap: la, routeData: HandoffDrive.saddlePeak.routeGeometryCredit)
        #expect(Self.occurrences(of: "OpenStreetMap", in: pill) == 1, "\(pill)")
        #expect(pill == la, "the plan's string stands unchanged: \(pill)")
    }

    @Test("a drive that draws no line shows each style's credit unchanged")
    func noLineLeavesTheStyleCreditUnchanged() throws {
        let credits = [try Self.declaredCredit("demoAttribution"), try Self.declaredCredit("protomapsAttribution")]
        let lineless = HandoffDrive.allCases.filter { $0.routeGeometryResource == nil }
        #expect(Set(lineless) == Set([HandoffDrive.skyline, .santaMonicaMountains]))
        for drive in lineless {
            for credit in credits {
                let pill = CreditLine.composed(basemap: credit, routeData: drive.routeGeometryCredit)
                #expect(pill == credit, "\(drive): \(pill)")
            }
        }
    }

    @Test("a drive has a data credit exactly when it draws a line, and that credit names OpenStreetMap")
    func everyDrawnLineCarriesItsCredit() {
        for drive in HandoffDrive.allCases {
            #expect((drive.routeGeometryCredit == nil) == (drive.routeGeometryResource == nil), "\(drive)")
            if let credit = drive.routeGeometryCredit {
                #expect(credit.contains("OpenStreetMap contributors"), "\(drive): \(credit)")
            }
        }
    }
}
