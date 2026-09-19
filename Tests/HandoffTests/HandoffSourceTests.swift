import Foundation
import Testing
@testable import Handoff

/// Three checks on the shipping source text, each named for exactly what it covers.
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
/// capitalised identifier under `Sources/Handoff` must be one on the list below.
///
/// ## Why the walk recurses, and why a third test exists to prove it does
///
/// The first version read the directory with `contentsOfDirectory(atPath:)`, which lists ONE directory,
/// while `Package.swift:33` declares `path: "Sources/Handoff"` and SwiftPM compiles that tree RECURSIVELY.
/// A reviewer put the identical `NumberFormatter().decimalSeparator` helper in
/// `Sources/Handoff/Fmt/point.swift`, called it from `decimal(_:)`, and all 41 tests stayed green - while
/// the same helper in a top-level file went red on both checks. So the allow-list was closed over the files
/// it happened to see, and its own doc claimed it was closed over the module. Third recurrence of this
/// file's own subject, inside the file written to end it.
///
/// That layout is not hypothetical: `Sources/ScenicKit/Geo`, `.../Model` and `.../Solar` are the house shape
/// for a target declared exactly this way, and CLAUDE.md's one-type-per-file plus 300-line cap is what
/// produces them.
///
/// The old completeness guard, `files.count >= 2`, could not see it either - both top-level files were still
/// there, so the count still passed with a whole directory skipped. Two things replace it:
///
///   * `scanIsRecursive` builds a throwaway tree in the temp directory with a file one level down and
///     asserts the walk returns it. That fires on every run, whatever `Sources/Handoff` happens to contain
///     today, which a count floor cannot do;
///   * both checks below assert the scanned file set EQUALS what an independent hand-written walk finds
///     under the real root. A directory skipped there breaks an equality rather than surviving a `>=`.
///
/// **What is still not covered, stated rather than implied.** The allow-list is complete for TYPE names
/// written under `Sources/Handoff`. The deny-list half is not complete and cannot be, because it is a list
/// of spellings; a locale consulted through a member of an already-allowed type would pass both. That
/// residue is small (the allowed types are `Array`, `String`, the numeric types and three URL types) and it
/// is the reason the load-bearing half is the closed one. Nothing here claims anything about `ScenicKit`,
/// which is a different target with its own tests.
///
/// Anchored on identifiers, which CLAUDE.md permits and prefers, and never on a comment: whole-line comments
/// are stripped first, because `AppleMapsDirections.swift` argues about `String(format:)` and `Locale` at
/// length to explain why they are gone.
@Suite("Handoff shipping source")
struct HandoffSourceTests {

    /// The directory `Package.swift` hands SwiftPM as the Handoff target's `path:`.
    static var sourceRoot: URL {
        URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()      // HandoffTests
            .deletingLastPathComponent()      // Tests
            .deletingLastPathComponent()      // repo root
            .appendingPathComponent("Sources/Handoff")
    }

    /// Every `.swift` file under `root` AND ITS SUBDIRECTORIES, as (path relative to `root`, code with
    /// whole-line comments removed).
    static func shippingSource(under root: URL) throws -> [(String, String)] {
        let names = try FileManager.default.subpathsOfDirectory(atPath: root.path)
            .map { $0.replacingOccurrences(of: "\\", with: "/") }
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

    /// The same tree, walked by hand instead of by `subpathsOfDirectory`, so the two can disagree.
    ///
    /// Deliberately a SECOND mechanism. A guard that recursed the way the scan does would agree with it by
    /// construction and would have waved the reviewer's subdirectory helper through exactly as
    /// `files.count >= 2` did - an expectation computed from the thing it checks.
    static func swiftFilesByHand(under root: URL) throws -> Set<String> {
        let fm = FileManager.default
        var found: Set<String> = []
        var pending: [(URL, String)] = [(root, "")]
        while let (dir, prefix) = pending.popLast() {
            for entry in try fm.contentsOfDirectory(at: dir, includingPropertiesForKeys: [.isDirectoryKey]) {
                let name = entry.lastPathComponent
                let rel = prefix.isEmpty ? name : prefix + "/" + name
                if try entry.resourceValues(forKeys: [.isDirectoryKey]).isDirectory == true {
                    pending.append((entry, rel))
                } else if name.hasSuffix(".swift") {
                    found.insert(rel)
                }
            }
        }
        return found
    }

    /// The line with every `"…"` string literal emptied, so the allow-list reads CODE and not prose.
    ///
    /// RULED 2026-09-19 (T-0202/T-0210, the pre-review mutant pass). `HandoffDrive` now owns the two
    /// sentences the screens render - the home surface's `timingSentence` and the failure card's
    /// `failureTimingSentence` - because the Apple-only target that used to own them has no test bundle
    /// and a number typed into a literal there ships with every gate green (M3a). Those sentences are
    /// English: "Plan an afternoon…", "Apple Maps gives you the real time when it opens." Tokenising them
    /// made this check red on `Plan`, `Apple` and `Maps` (linux-core run 35456872113, four issues), which
    /// is this check doing exactly what it says - and saying the wrong thing, because none of the three is
    /// a type this module depends on.
    ///
    /// A capitalised word inside a double-quoted literal is DATA. What the list exists to close is the set
    /// of types the shipping source NAMES, and the one way a string reaches a type - by name, through
    /// `NSClassFromString` or a `Bundle` lookup - still spells a capitalised identifier in the code, where
    /// this scan still sees it. Every string in this module before today was a lowercase URL component
    /// (`maps.apple.com`, `waypoint`, `driving`), so nothing that was ever covered stops being covered.
    ///
    /// Per LINE, and quote by quote: `shippingSource` strips whole-line comments only, so a trailing
    /// comment carrying an odd `"` would otherwise swallow the next line of real code. Blind to a `"""`
    /// multi-line literal, of which this module has none; `stringLiteralsAreNotTypeReferences` is what
    /// holds the code half of this rule.
    static func outsideStringLiterals(_ code: String) -> String {
        var out = ""
        for line in code.split(separator: "\n", omittingEmptySubsequences: false) {
            var inString = false
            var escaped = false
            for character in line {
                if escaped {
                    escaped = false
                    continue
                }
                if inString && character == "\\" {
                    escaped = true
                    continue
                }
                if character == "\"" {
                    inString = !inString
                    continue
                }
                if inString == false {
                    out.append(character)
                }
            }
            out.append("\n")
        }
        return out
    }

    /// Every type this module is allowed to name, transcribed by hand from the source files.
    ///
    /// Two groups. The Swift value types (`Array`, `Bool`, `Double`, `Int`, `String`, ...) are pre-argued:
    /// none of them consults a locale, and refusing them would only push a normal refactor into editing this
    /// list for no gain. Every FOUNDATION type is here because it was argued for - `URL`, `URLComponents` and
    /// `URLQueryItem` because percent-encoding by hand gets the comma in `lat,lon` wrong in one direction or
    /// the other. Adding to this group is how the next dependency gets argued for, and that is the point of
    /// the list: the check fails first and the argument happens second.
    static let allowedTypes: Set<String> = [
        // declared here
        //
        // `SkylineRoute` is the hard-coded Skyline drive's coordinates, moved in from the Apple-only
        // feature target by T-0151 so that the spacing of its pins could be tested at all. It names no
        // type this list did not already allow: `Coordinate` and the numeric literals, nothing else.
        // This check went red on the move, by name, which is the list doing its job - the argument for
        // the new file happened here before the suite went green again.
        //
        // `StraightLineDistance` is T-0170's chain arithmetic: the drive's pins summed with
        // `ScenicKit.Geo`, floored to whole kilometres, so the home screen can show one measured
        // number. It names `Coordinate`, `Geo`, `SkylineRoute`, `Array`, `Double` and `Int` and
        // nothing else. This check went red on it by name, along with `Geo` below, which is the list
        // doing its job a second time.
        //
        // `SantaMonicaMountainsRoute` is T-0178's LA drive - the owner's loop, Sunset to PCH to
        // Topanga to Mulholland to Westwood - held the way `SkylineRoute` holds the Bay Area one. It
        // names `Coordinate` and numeric literals and nothing else. `HandoffDrive` is which of the
        // two the screen is showing; it names both route types, `Coordinate`, `Array`, `String`,
        // `CaseIterable` and `Sendable`. This check went red on both by name before it went green.
        "AppleMapsDirections", "HandoffDrive", "HandoffError", "Mode", "SantaMonicaMountainsRoute",
        "SkylineRoute", "StraightLineDistance",
        // modules
        "Foundation", "ScenicKit",
        // ScenicKit
        //
        // `Geo` is the great-circle arithmetic (`distanceMeters`, `initialBearingDegrees`). It is
        // pure `Foundation` trigonometry on `Double`s with no locale and no formatting anywhere in
        // it, which is the property this list exists to protect.
        "Coordinate", "Geo",
        // Swift, locale-free by construction
        "Array", "Bool", "Character", "Double", "Int", "Self", "String", "Substring",
        "CaseIterable", "Comparable", "CustomStringConvertible", "Equatable", "Error", "Hashable", "Sendable",
        // Foundation, each one argued for
        "URL", "URLComponents", "URLQueryItem",
    ]

    @Test("the source scan descends into subdirectories, which is how SwiftPM compiles this target")
    func scanIsRecursive() throws {
        // A throwaway tree, so this fires on every run instead of only when Sources/Handoff happens to have
        // a subdirectory today. The reviewer's reproduction lived exactly in that gap: a non-recursive scan
        // and a `files.count >= 2` floor are indistinguishable from a correct scan until a directory exists.
        let fm = FileManager.default
        let tmp = fm.temporaryDirectory.appendingPathComponent("HandoffScan-\(UUID().uuidString)")
        try fm.createDirectory(at: tmp.appendingPathComponent("Fmt"), withIntermediateDirectories: true)
        defer { try? fm.removeItem(at: tmp) }
        try "let top = 1\n".write(to: tmp.appendingPathComponent("Top.swift"),
                                 atomically: true, encoding: .utf8)
        try "// stripped, one directory down\nlet deep = 2\n"
            .write(to: tmp.appendingPathComponent("Fmt/point.swift"), atomically: true, encoding: .utf8)
        try "not swift\n".write(to: tmp.appendingPathComponent("Fmt/notes.md"),
                                atomically: true, encoding: .utf8)

        #expect(Set(try Self.shippingSource(under: tmp).map(\.0)) == ["Top.swift", "Fmt/point.swift"])
        #expect(try Self.swiftFilesByHand(under: tmp) == ["Top.swift", "Fmt/point.swift"])
        // And the comment stripping runs on the file one level down too, not only on the top-level ones.
        let deep = try Self.shippingSource(under: tmp).first { $0.0 == "Fmt/point.swift" }?.1
        #expect(deep == "let deep = 2\n", "got \(deep ?? "nothing")")
    }

    @Test("every capitalised identifier in the shipping source is on the allow-list")
    func everyTypeNamedIsOnTheAllowList() throws {
        let files = try Self.shippingSource(under: Self.sourceRoot)
        #expect(Set(files.map(\.0)) == (try Self.swiftFilesByHand(under: Self.sourceRoot)),
                "the scan missed part of Sources/Handoff; it saw \(files.map(\.0))")
        for (name, code) in files {
            let named = Self.outsideStringLiterals(code)
            let tokens = named.split(whereSeparator: { !($0.isLetter || $0.isNumber || $0 == "_") })
            for token in tokens where token.first?.isUppercase == true {
                #expect(Self.allowedTypes.contains(String(token)),
                        "\(name) names the type \(token), which is not on the Handoff allow-list")
            }
        }
    }

    @Test("the type scan reads code, and the words inside a string literal are not type references")
    func stringLiteralsAreNotTypeReferences() {
        // The half of the string-literal ruling that has to stay true: a type named in CODE is still
        // named, on the same line as a sentence that mentions Apple Maps. Without this, "strip the
        // strings" could quietly become "strip the line" and the allow-list would go blind in silence.
        let code = "let note = \"Plan an afternoon. Apple Maps knows.\"\nlet f = NumberFormatter()\n"
        let named = Self.outsideStringLiterals(code)
        #expect(named.contains("NumberFormatter"), "the scan lost a type in code: \(named)")
        #expect(named.contains("note"), "the scan lost the declaration: \(named)")
        #expect(!named.contains("Apple"), "a word in a sentence is read as a type: \(named)")
        #expect(!named.contains("Plan"), "a word in a sentence is read as a type: \(named)")

        // An escaped quote inside a literal does not end it, and a trailing comment's odd quote stops at
        // its own line instead of swallowing the next one.
        let tricky = "let q = \"say \\\" now\"\nlet Kept = 1 // it's \"odd\n let Also = 2\n"
        let keptNamed = Self.outsideStringLiterals(tricky)
        #expect(keptNamed.contains("Kept"), "an escaped quote ate the code after it: \(keptNamed)")
        #expect(keptNamed.contains("Also"), "a trailing comment's quote ate the next line: \(keptNamed)")
    }

    @Test("the shipping source uses none of the lowercase locale-sensitive spellings")
    func noLocaleSensitiveSpelling() throws {
        // The allow-list is a list of TYPES and so cannot see any of these: `String` is on it and `format:`
        // is an argument label, `formatted()` and `decimalSeparator` are members, `locale:` is a label.
        let forbidden = ["String(format:", "locale:", ".formatted(", "localizedString", "decimalSeparator"]
        let files = try Self.shippingSource(under: Self.sourceRoot)
        #expect(Set(files.map(\.0)) == (try Self.swiftFilesByHand(under: Self.sourceRoot)),
                "the scan missed part of Sources/Handoff; it saw \(files.map(\.0))")
        for (name, code) in files {
            for spelling in forbidden {
                #expect(!code.contains(spelling), "\(name) uses \(spelling) outside a comment")
            }
        }
    }
}
