import Foundation
import Testing
@testable import Handoff

/// Two checks on the shipping source text, each named for exactly what it covers.
///
/// The predecessor was called *"no locale is consulted anywhere in the shipping source"* and grepped for two
/// spellings, `String(format:` and `Locale`. A reviewer walked past it with
///
///     let point = NumberFormatter().decimalSeparator ?? "."
///
/// which contains neither, and all 34 tests stayed green. `NumberFormatter`'s separator IS locale-derived on
/// this toolchain (de_DE gives `,`, en_US_POSIX gives `.`), so that is the German-device bug live again: a
/// decimal comma inside a comma-separated pair, which Apple Maps reads as four numbers and drives to the
/// Gulf of Guinea. A deny-list of two spellings, named as though it covered a whole class, is the same
/// defect this module keeps shipping - a check whose stated scope exceeds what it covers - one level up.
///
/// So the load-bearing check here is an ALLOW-list, which is closed where a deny-list is open: every
/// capitalised identifier in `Sources/Handoff` must be one on the list below. `NumberFormatter` is not, and
/// neither is any other type a future edit reaches for without saying so. The deny-list survives only for
/// the lowercase spellings an allow-list of type names cannot see - `String` is allowed, `format:` is an
/// argument label - and its name now claims nothing more than that.
///
/// **What is still not covered, stated rather than implied.** The allow-list is complete for TYPE names: no
/// locale-bearing type can be reached without failing it. The deny-list half is not complete and cannot be,
/// because it is a list of spellings; a locale consulted through a member of an already-allowed type would
/// pass both checks. That residue is small (the allowed types are `Array`, `String`, the numeric types and
/// three URL types) and it is the reason the load-bearing half is the closed one.
///
/// Anchored on identifiers, which CLAUDE.md permits and prefers, and never on a comment: whole-line comments
/// are stripped first, because `AppleMapsDirections.swift` argues about `String(format:)` and `Locale` at
/// length to explain why they are gone.
@Suite("Handoff shipping source")
struct HandoffSourceTests {

    /// `Sources/Handoff/*.swift` as (filename, code with whole-line comments removed).
    static func shippingSource() throws -> [(String, String)] {
        let root = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()      // HandoffTests
            .deletingLastPathComponent()      // Tests
            .deletingLastPathComponent()      // repo root
            .appendingPathComponent("Sources/Handoff")
        let names = try FileManager.default.contentsOfDirectory(atPath: root.path)
            .filter { $0.hasSuffix(".swift") }
            .sorted()
        return try names.map { name in
            let text = try String(contentsOf: root.appendingPathComponent(name), encoding: .utf8)
            let code = text.split(separator: "\n", omittingEmptySubsequences: false)
                .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
                .joined(separator: "\n")
            return (name, code)
        }
    }

    /// Every type this module is allowed to name, transcribed by hand from the two source files.
    ///
    /// Two groups. The Swift value types (`Array`, `Bool`, `Double`, `Int`, `String`, ...) are pre-argued:
    /// none of them consults a locale, and refusing them would only push a normal refactor into editing this
    /// list for no gain. Every FOUNDATION type is here because it was argued for - `URL`, `URLComponents` and
    /// `URLQueryItem` because percent-encoding by hand gets the comma in `lat,lon` wrong in one direction or
    /// the other. Adding to this group is how the next dependency gets argued for, and that is the point of
    /// the list: the check fails first and the argument happens second.
    static let allowedTypes: Set<String> = [
        // declared here
        "AppleMapsDirections", "HandoffError", "Mode",
        // modules
        "Foundation", "ScenicKit",
        // ScenicKit
        "Coordinate",
        // Swift, locale-free by construction
        "Array", "Bool", "Character", "Double", "Int", "Self", "String", "Substring",
        "CaseIterable", "Comparable", "CustomStringConvertible", "Equatable", "Error", "Hashable", "Sendable",
        // Foundation, each one argued for
        "URL", "URLComponents", "URLQueryItem",
    ]

    @Test("every capitalised identifier in the shipping source is on the allow-list")
    func everyTypeNamedIsOnTheAllowList() throws {
        let files = try Self.shippingSource()
        #expect(files.count >= 2, "expected the Handoff sources; found \(files.map(\.0))")
        for (name, code) in files {
            let tokens = code.split(whereSeparator: { !($0.isLetter || $0.isNumber || $0 == "_") })
            for token in tokens where token.first?.isUppercase == true {
                #expect(Self.allowedTypes.contains(String(token)),
                        "\(name) names the type \(token), which is not on the Handoff allow-list")
            }
        }
    }

    @Test("the shipping source uses none of the lowercase locale-sensitive spellings")
    func noLocaleSensitiveSpelling() throws {
        // The allow-list is a list of TYPES and so cannot see any of these: `String` is on it and `format:`
        // is an argument label, `formatted()` and `decimalSeparator` are members, `locale:` is a label.
        let forbidden = ["String(format:", "locale:", ".formatted(", "localizedString", "decimalSeparator"]
        let files = try Self.shippingSource()
        #expect(files.count >= 2, "expected the Handoff sources; found \(files.map(\.0))")
        for (name, code) in files {
            for spelling in forbidden {
                #expect(!code.contains(spelling), "\(name) uses \(spelling) outside a comment")
            }
        }
    }
}
