import Foundation
import Testing
import ScenicKit
@testable import ScenicPlanCLI

/// T-0385: ops/plan's body gate covers every encoded value the SHIPPED base profile hard-gates on.
///
/// The Swift twin of services/api/test/customModelGateValues.test.ts (T-0382). The list is never restated here:
/// the gate identifiers are read from services/routing/profiles/car_scenic_base.json - the lower-case identifiers
/// in the `if` of every `multiply_by: "0"` priority clause, in profile order - and the builder's are read from
/// LambdaCustomModel.json(for:) at every lambda tenth the bisection can reach. forbiddenEncodedValues must equal
/// the first minus the second, and the overlap must be exactly road_class.
///
/// Each derived name then gets a GENERATED near-miss corpus, placed in every clause shape, embedded by
/// body(_:_:profile:model:) and sent through send(_:) - the one function fastest() and scenic() reach the socket
/// through. Oracle: refused with that name iff the lowered model text contains a derived name, else the transport
/// receives the body unchanged.
@Suite("ops/plan body gate is bound to the shipped base profile")
struct PlanCLIGateValuesTests {

    /// A row of the corpus: which generator made it, and the text it places in a model.
    struct Row: Equatable {
        let family: String
        let text: String
    }

    /// One body through the gate: where its text sat, and what the gate did with it.
    struct Sent: Equatable {
        let shape: String
        let family: String
        let text: String
        let outcome: String
    }

    static let profile = URL(fileURLWithPath: #filePath)   // Tests/ScenicPlanCLITests/<this file>
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        .appendingPathComponent("services/routing/profiles/car_scenic_base.json")

    static let separators = [" ", "\t", ";", "_", "-", ",", "|", "x"]
    static let families = ["affix", "case", "compound", "deletion", "empty", "exact", "operator", "separator"]
    static let shapes = ["priority if", "priority else_if", "speed if", "speed else_if", "areas property", "object key"]
    static let origin = Coordinate(latitude: 34.0944, longitude: -118.6013)
    static let destination = Coordinate(latitude: 34.0365, longitude: -118.6870)

    /// Port 9 is discard: a body that got past both the gate and the seam would fail loudly and differently.
    static var source: GraphHopperRouteSource {
        var source = GraphHopperRouteSource(baseURL: URL(string: "http://127.0.0.1:9")!, timeout: 2)
        source.post = { body in throw PlanFailure.routerRefused(body) }
        return source
    }

    /// A GraphHopper condition names an encoded value in lower case; enum constants (PRIVATE, GRADE3) are upper.
    static func identifiers(of condition: String) -> [String] {
        let pattern = try! NSRegularExpression(pattern: "[A-Za-z_][A-Za-z0-9_]*")
        let tokens = pattern.matches(in: condition, range: NSRange(condition.startIndex..., in: condition))
            .compactMap { Range($0.range, in: condition).map { String(condition[$0]) } }
        return tokens.filter { token in
            guard let first = token.unicodeScalars.first, ("a"..."z").contains(first) else { return false }
            return token != "true" && token != "false"
        }
    }

    static func unique(_ names: [String]) -> [String] {
        var seen: [String] = []
        for name in names where !seen.contains(name) { seen.append(name) }
        return seen
    }

    static func condition(of clause: [String: Any]) -> String {
        (clause["if"] as? String) ?? (clause["else_if"] as? String) ?? (clause["else"] as? String) ?? ""
    }

    /// The `multiply_by: "0"` priority clauses of the shipped profile, in order.
    static func zeroClauses() throws -> [[String: Any]] {
        let object = try JSONSerialization.jsonObject(with: try Data(contentsOf: profile)) as? [String: Any]
        let priority = try #require(object?["priority"] as? [[String: Any]], "no priority list in \(profile.path)")
        return priority.filter { $0["multiply_by"] as? String == "0" }
    }

    static func gateIdentifiers() throws -> [String] {
        unique(try zeroClauses().flatMap { identifiers(of: condition(of: $0)) })
    }

    /// Every identifier the CLI's one model builder reads, over every lambda tenth in [0, LambdaSearch.maxLambda].
    static func builderIdentifiers() throws -> [String] {
        var names: [String] = []
        for tenths in 0...Int(LambdaSearch.maxLambda * 10) {
            let model = try LambdaCustomModel.json(for: Double(tenths) / 10)
            let object = try #require(try JSONSerialization.jsonObject(with: Data(model.utf8)) as? [String: Any])
            for key in ["priority", "speed"] {
                for clause in object[key] as? [[String: Any]] ?? [] { names += identifiers(of: condition(of: clause)) }
            }
        }
        return unique(names)
    }

    static func derived() throws -> [String] {
        let builder = try builderIdentifiers()
        return try gateIdentifiers().filter { !builder.contains($0) }
    }

    /// Every row is a function of the name: nothing here is a hand-picked spelling of one name.
    static func corpus(_ name: String) -> [Row] {
        let letters = Array(name)
        var rows = [Row(family: "exact", text: name), Row(family: "empty", text: "")]
        rows.append(Row(family: "case", text: name.uppercased()))
        rows.append(Row(family: "case", text: String(letters[0]).uppercased() + String(letters.dropFirst())))
        rows.append(Row(family: "case", text: String(letters.enumerated().map { at, ch in
            at % 2 == 1 ? Character(String(ch).uppercased()) : ch })))
        for at in letters.indices {
            rows.append(Row(family: "deletion", text: String(letters[..<at]) + String(letters[(at + 1)...])))
        }
        for separator in separators {
            for at in 0...letters.count {
                rows.append(Row(family: "separator",
                                text: String(letters[..<at]) + separator + String(letters[at...])))
            }
        }
        for text in ["x\(name)", "\(name)x", "\(name)_x", "in_\(name)"] { rows.append(Row(family: "affix", text: text)) }
        for text in ["\(name);paved", "paved;\(name)", "\(name);\(name)"] {
            rows.append(Row(family: "compound", text: text))
        }
        for text in ["\(name) == GRADE3", "\(name) != NO", "!\(name)", "\(name) >= 3", "\(name) < 1",
                     "true && \(name)", "\(name) || false", "(\(name) == BAD)", "scenic_score >= 7 && \(name) == X",
                     "road_class == PRIMARY || \(name)"] {
            rows.append(Row(family: "operator", text: text))
        }
        return rows
    }

    /// The text placed in one clause shape, as the JSON model the body embeds.
    static func model(_ shape: String, _ text: String) throws -> String {
        let square: [String: Any] = ["type": "Polygon",
                                     "coordinates": [[[-118.5, 34.0], [-118.4, 34.0], [-118.4, 34.1], [-118.5, 34.0]]]]
        var keyed: [String: Any] = ["multiply_by": "1"]
        keyed[text] = "1"
        let object: [String: Any]
        switch shape {
        case "priority if": object = ["priority": [["if": text, "multiply_by": "1"]]]
        case "priority else_if":
            object = ["priority": [["if": "scenic_score >= 7", "multiply_by": "1"], ["else_if": text, "multiply_by": "0.5"]]]
        case "speed if": object = ["speed": [["if": text, "limit_to": "100"]]]
        case "speed else_if":
            object = ["speed": [["if": "true", "multiply_by": "0.9"], ["else_if": text, "multiply_by": "0.5"]]]
        case "areas property":
            let feature: [String: Any] = ["type": "Feature", "id": "a", "properties": ["note": text], "geometry": square]
            object = ["priority": [["if": "in_a", "multiply_by": "0"]],
                      "areas": ["type": "FeatureCollection", "features": [feature]]]
        case "object key": object = ["priority": [keyed]]
        default: throw PlanFailure.routerRefused("unknown shape \(shape)")
        }
        let data = try JSONSerialization.data(withJSONObject: object, options: [.sortedKeys, .withoutEscapingSlashes])
        return String(decoding: data, as: UTF8.self)
    }

    static func body(_ model: String?) -> String {
        source.body(origin, destination, profile: "car_scenic", model: model)
    }

    /// The oracle reads the PROFILE-derived list, never the constant under test.
    static func firstMention(_ derived: [String], _ text: String) -> String? {
        derived.first { text.lowercased().contains($0) }
    }

    /// One body through the shipping gate: refused with a name, or what the transport received.
    static func outcome(_ body: String) -> String {
        do {
            _ = try source.send(body)
            return "returned without reaching the transport"
        } catch PlanFailure.modelTouchesSafetyGate(let value) {
            return "refused \(value)"
        } catch PlanFailure.routerRefused(let sent) {
            return "forwarded \(sent)"
        } catch {
            return "threw \(error)"
        }
    }

    @Test("forbiddenEncodedValues equals the shipped profile's zero-clause identifiers minus LambdaCustomModel's own")
    func theGateListIsTheShippedProfilesGateValues() throws {
        let clauses = try Self.zeroClauses()
        #expect(clauses.map { $0["if"] is String } == clauses.map { _ in true })
        let gates = try Self.gateIdentifiers()
        let builder = try Self.builderIdentifiers()
        #expect(gates.filter { builder.contains($0) } == ["road_class"])
        #expect(GraphHopperRouteSource.forbiddenEncodedValues == gates.filter { !builder.contains($0) })
    }

    @Test("the corpus is generated for every derived name, and nothing outside the model mentions one")
    func theCorpusCoversEveryFamilyForEveryName() throws {
        let derived = try Self.derived()
        let seen = derived.map { name -> [String] in
            let rows = Self.corpus(name)
            let anchored = rows.filter { $0.family == "exact" || $0.family == "operator" }
            return Self.unique(rows.map(\.family)).sorted() + [
                "refused \(rows.contains { Self.firstMention(derived, $0.text) != nil })",
                "forwarded \(rows.contains { Self.firstMention(derived, $0.text) == nil })",
                "anchored \(anchored.allSatisfy { Self.firstMention(derived, $0.text) == name })",
            ]
        }
        #expect(seen == derived.map { _ in Self.families + ["refused true", "forwarded true", "anchored true"] })
        #expect(!derived.isEmpty)
        // The oracle reads only the model text, so the body around it must mention no name at any lambda.
        var around = [Self.body(nil), Self.body("{}")]
        for tenths in 0...Int(LambdaSearch.maxLambda * 10) {
            around.append(Self.body(try LambdaCustomModel.json(for: Double(tenths) / 10)))
        }
        #expect(around.compactMap { Self.firstMention(derived, $0) } == [])
    }

    @Test("send refuses every near miss in every clause shape iff it names a gate value, else forwards it unchanged")
    func sendRefusesExactlyTheGateValues() throws {
        let derived = try Self.derived()
        for name in derived {
            var actual: [Sent] = []
            var expected: [Sent] = []
            for row in Self.corpus(name) {
                for shape in Self.shapes {
                    let model = try Self.model(shape, row.text)
                    let body = Self.body(model)
                    actual.append(Sent(shape: shape, family: row.family, text: row.text, outcome: Self.outcome(body)))
                    let word = Self.firstMention(derived, model)
                    expected.append(Sent(shape: shape, family: row.family, text: row.text,
                                         outcome: word.map { "refused \($0)" } ?? "forwarded \(body)"))
                }
            }
            let differing = zip(actual, expected).filter { $0 != $1 }.count
            #expect(actual == expected, "\(name): \(differing) of \(expected.count) rows differ")
        }
    }
}
