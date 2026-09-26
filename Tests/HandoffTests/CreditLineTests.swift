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
///
/// The pill's WORDS are compared as they are read aloud - `spoken(_:)`, a non-breaking space read as a space - and
/// the pill's LINE BREAKS are bound by name in `noPartyBreaksAcrossLines` (T-0237).
@Suite("CreditLine")
struct CreditLineTests {
    static let mapStyleSource = URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        .appendingPathComponent("apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapStyle.swift")

    static let noBreakSpace = "\u{00A0}"

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

    /// The pill as a screen reader says it: a non-breaking space is a space.
    static func spoken(_ pill: String) -> String {
        pill.replacingOccurrences(of: noBreakSpace, with: " ")
    }

    @Test("over the demo tiles the Saddle Peak pill names OpenStreetMap after the basemap's own credit")
    func demoTilesUnderTheLineNameOpenStreetMap() throws {
        let demo = try Self.declaredCredit("demoAttribution")
        #expect(!demo.contains("OpenStreetMap"), "the demo credit itself never names OpenStreetMap: \(demo)")
        let pill = Self.spoken(CreditLine.composed(basemap: demo, routeData: HandoffDrive.saddlePeak.routeGeometryCredit))
        #expect(pill.contains("OpenStreetMap contributors"), "\(pill)")
        #expect(pill.hasPrefix(demo + CreditLine.separator), "the basemap's credit stays first and whole: \(pill)")
        #expect(pill == "© MapLibre · Natural Earth · © OpenStreetMap contributors")
    }

    @Test("over the LA Protomaps tiles the Saddle Peak pill names OpenStreetMap exactly once")
    func laTilesNameOpenStreetMapOnce() throws {
        let la = try Self.declaredCredit("protomapsAttribution")
        let pill = Self.spoken(CreditLine.composed(basemap: la, routeData: HandoffDrive.saddlePeak.routeGeometryCredit))
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
                let pill = Self.spoken(CreditLine.composed(basemap: credit, routeData: drive.routeGeometryCredit))
                #expect(pill == credit, "\(drive): \(pill)")
            }
        }
    }

    /// T-0236 round 2's pill wrapped '... Natural Earth · ©' / 'OpenStreetMap contributors': the copyright sign on
    /// one line and the party it credits on the next. A line may break only at a space, so every space INSIDE a
    /// party is non-breaking and the separator's two are the only breakable ones - over every drive and both
    /// basemaps, through the entry point the footer is handed.
    @Test("the credit pill never breaks a party across lines: every space inside a party is non-breaking")
    func noPartyBreaksAcrossLines() throws {
        let credits = [try Self.declaredCredit("demoAttribution"), try Self.declaredCredit("protomapsAttribution")]
        for drive in HandoffDrive.allCases {
            for credit in credits {
                let pill = CreditLine.composed(basemap: credit, routeData: drive.routeGeometryCredit)
                let parties = pill.components(separatedBy: CreditLine.separator)
                #expect(parties.count >= 2, "\(drive): \(pill)")
                for party in parties {
                    #expect(!party.contains(" "), "\(drive): a breakable space inside the party '\(party)'")
                    #expect(!party.isEmpty, "\(drive): an empty party in \(pill)")
                }
                #expect(Self.occurrences(of: "©", in: pill) == Self.occurrences(of: "©" + Self.noBreakSpace, in: pill),
                        "\(drive): a copyright sign not glued to its party: \(pill)")
            }
        }
        let r2 = CreditLine.composed(basemap: try Self.declaredCredit("demoAttribution"),
                                     routeData: HandoffDrive.saddlePeak.routeGeometryCredit)
        let nb = Self.noBreakSpace
        #expect(r2 == "©\(nb)MapLibre · Natural\(nb)Earth · ©\(nb)OpenStreetMap\(nb)contributors")
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
