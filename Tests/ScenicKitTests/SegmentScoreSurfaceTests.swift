import Foundation
import Testing

/// T-0218 R2: the plan formula reaches no surface but its approved sites. A WHITELIST on the identifier:
/// every non-`//` line under Sources/ and apps/ that names `score(for` or `SegmentScore.score` - once the
/// approved entry token `SegmentScoreCeiling.score(for` is removed from it - must be one of the approved
/// (file, whole trimmed line) sites below. A new surface that shows the formula's number is red here by name;
/// it calls `SegmentScoreCeiling.score(for:)` instead.
@Suite("SegmentScore surfaces (T-0218)")
struct SegmentScoreSurfaceTests {

    static let entryToken = "SegmentScoreCeiling.score(for"
    static let approved: [String: [String]] = [
        "Sources/ScenicKit/Scoring/SegmentScore.swift":
            ["public static func score(for t: SegmentTerms) -> Double? {"],
        "Sources/ScenicKit/Scoring/SegmentScoreCeiling.swift":
            ["public static func score(for t: SegmentTerms) -> Double? {",
             "guard let formula = SegmentScore.score(for: t) else { return nil }"],
        // R4: ops/route-autopsy prints M and E and the formula score they make; a developer tool, not a device.
        "Sources/ScenicPlanCLI/AutopsyReport.swift":
            ["guard let score = SegmentScore.score(for: way.terms) else { return [gate, \"invalid\", \"invalid\", \"invalid\"] }"],
    ]
    static let pattern = try! NSRegularExpression(pattern: #"\bscore\s*\(\s*for\b|\bSegmentScore\s*\.\s*score\b"#)

    static var root: URL {
        URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .deletingLastPathComponent()
    }

    static func swiftFiles(under dir: String) -> [String] {
        guard let walker = FileManager.default.enumerator(atPath: root.appendingPathComponent(dir).path) else {
            return []
        }
        var out: [String] = []
        while let next = walker.nextObject() as? String {
            let relative = next.replacingOccurrences(of: "\\", with: "/")
            // Build products are skipped by path component, not by skipDescendants(), which on this
            // Windows Foundation ended the whole walk at the first dot-file (apps/ read 1 file of 113).
            let parts = relative.split(separator: "/")
            if parts.contains(where: { $0.hasPrefix(".") || $0 == "DerivedData" || $0 == "build" }) { continue }
            if relative.hasSuffix(".swift") { out.append(dir + "/" + relative) }
        }
        return out.sorted()
    }

    /// The (file, trimmed line) of every site naming the formula, entry token removed first.
    static func sites(_ relative: String, _ text: String) -> [(String, String)] {
        var out: [(String, String)] = []
        for raw in text.replacingOccurrences(of: "\r\n", with: "\n").split(separator: "\n") {
            let trimmed = raw.trimmingCharacters(in: .whitespaces)
            if trimmed.hasPrefix("//") { continue }
            let rest = trimmed.replacingOccurrences(of: entryToken, with: "")
            let range = NSRange(rest.startIndex..., in: rest)
            if pattern.firstMatch(in: rest, range: range) != nil { out.append((relative, trimmed)) }
        }
        return out
    }

    @Test("every call of the formula in Sources/ and apps/ is at an approved site")
    func formulaOnlyAtApprovedSites() throws {
        let sources = Self.swiftFiles(under: "Sources"), apps = Self.swiftFiles(under: "apps")
        // Fail closed per root: a walk that silently reads nothing under one root guards nothing there.
        #expect(sources.count > 300, "read only \(sources.count) Swift files under Sources/")
        #expect(apps.count > 50, "read only \(apps.count) Swift files under apps/")
        let files = sources + apps
        var found: [String: [String]] = [:]
        for f in files {
            let text = try String(contentsOf: Self.root.appendingPathComponent(f), encoding: .utf8)
            for (file, line) in Self.sites(f, text) {
                if Self.approved[file]?.contains(line) == true {
                    found[file, default: []].append(line)
                } else {
                    Issue.record("unapproved formula site \(file): \(line)")
                }
            }
        }
        for (file, lines) in Self.approved {
            #expect(found[file]?.sorted() == lines.sorted(), "\(file): approved \(lines), found \(found[file] ?? [])")
        }
    }

    @Test("the surface guard sees every spelling of a call to the formula")
    func guardSeesSpellings() {
        let red = ["let x = SegmentScore.score(for: t)", "let x = SegmentScore . score ( for: t)",
                   "let f = SegmentScore.score", "x = Self.score(for: t) ?? 0", "x = score(for: t)",
                   "x = ScenicKit.SegmentScore.score(for: t) // shown", "x = SegmentScoreCeiling.score(for: t) + SegmentScore.score(for: t)"]
        for line in red { #expect(Self.sites("Sources/X.swift", line).count == 1, "missed: \(line)") }
        let quiet = ["// SegmentScore.score(for: t)", "/// see score(for:)", "let x = SegmentScoreCeiling.score(for: t)",
                     "let m = SegmentScore.axes(for: t)", "let s = RouteScore(edges: e).score"]
        for line in quiet { #expect(Self.sites("Sources/X.swift", line).isEmpty, "flagged: \(line)") }
    }
}
