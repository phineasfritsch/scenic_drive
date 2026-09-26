import Foundation
@testable import ScenicKit

/// A per-request custom model READ BACK the way GraphHopper applies it, so a test can ask what an edge of a
/// given class and score costs at a lambda without trusting how the model was built.
///
/// GraphHopper's semantics for `priority`: a chain starts at an `if` and continues through `else_if` / `else`;
/// the FIRST matching clause of a chain applies; separate chains multiply. Conditions are read in the only
/// shapes a scenic model uses - `road_class == X` atoms joined by `||` inside parentheses, `scenic_score >= N`
/// or `< N`, joined by `&&` - and anything else is refused by name rather than guessed.
struct CustomModelChain {

    enum Unreadable: Error, Equatable { case condition(String), shape(String) }

    let priority: [[String: String]]
    let distanceInfluence: Double?

    init(json text: String) throws {
        guard let object = try JSONSerialization.jsonObject(with: Data(text.utf8)) as? [String: Any],
              let clauses = object["priority"] as? [[String: Any]] else {
            throw Unreadable.shape(text)
        }
        priority = try clauses.map { clause in
            var strings: [String: String] = [:]
            for (key, value) in clause {
                guard let text = value as? String else { throw Unreadable.shape("\(key) is not a string") }
                strings[key] = text
            }
            return strings
        }
        distanceInfluence = (object["distance_influence"] as? NSNumber)?.doubleValue
    }

    /// The product of every chain's first matching multiplier for an edge of `roadClass` scored `score`.
    func multiplier(roadClass: String, score: Int) throws -> Double {
        var product = 1.0
        var chainMatched = true
        for clause in priority {
            let condition: String
            if let text = clause["if"] {
                chainMatched = false
                condition = text
            } else if let text = clause["else_if"] {
                condition = text
            } else if clause["else"] != nil {
                condition = ""
            } else {
                throw Unreadable.shape("a clause with no if/else_if/else: \(clause)")
            }
            guard !chainMatched else { continue }
            guard try condition.isEmpty || Self.holds(condition, roadClass: roadClass, score: score) else { continue }
            guard let text = clause["multiply_by"], let value = Double(text) else {
                throw Unreadable.shape("multiply_by missing or not a number: \(clause)")
            }
            product *= value
            chainMatched = true
        }
        return product
    }

    /// Seconds of weight per second driven: 1 / priority.
    func cost(roadClass: String, score: Int) throws -> Double {
        1 / (try multiplier(roadClass: roadClass, score: score))
    }

    /// The distinct `scenic_score >= N` thresholds the model branches on, highest first.
    var scoreThresholds: [Int] {
        let prefix = "scenic_score >= "
        let found = priority.compactMap { clause -> Int? in
            guard let text = clause["if"] ?? clause["else_if"], text.hasPrefix(prefix) else { return nil }
            return Int(text.dropFirst(prefix.count))
        }
        return Array(Set(found)).sorted(by: >)
    }

    static func holds(_ condition: String, roadClass: String, score: Int) throws -> Bool {
        for conjunct in condition.components(separatedBy: "&&") {
            var term = conjunct.trimmingCharacters(in: .whitespaces)
            if term.hasPrefix("(") && term.hasSuffix(")") { term = String(term.dropFirst().dropLast()) }
            let anyHolds = try term.components(separatedBy: "||").contains { atom in
                try atomHolds(atom.trimmingCharacters(in: .whitespaces), roadClass: roadClass, score: score)
            }
            if !anyHolds { return false }
        }
        return true
    }

    static func atomHolds(_ atom: String, roadClass: String, score: Int) throws -> Bool {
        let parts = atom.split(separator: " ").map(String.init)
        guard parts.count == 3 else { throw Unreadable.condition(atom) }
        switch (parts[0], parts[1]) {
        case ("road_class", "=="): return parts[2] == roadClass.uppercased()
        case ("scenic_score", ">="): return score >= (try number(parts[2], atom))
        case ("scenic_score", "<"): return score < (try number(parts[2], atom))
        default: throw Unreadable.condition(atom)
        }
    }

    static func number(_ text: String, _ atom: String) throws -> Int {
        guard let value = Int(text) else { throw Unreadable.condition(atom) }
        return value
    }
}
