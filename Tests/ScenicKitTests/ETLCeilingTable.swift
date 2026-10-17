import Foundation

/// `services/etl/etl/assemble.py`'s `CLASS_SCORE_CEILING`, read from the file by identifier (T-0218 R1).
///
/// Fails closed. Every non-comment line of assemble.py that names the identifier must be one of the two
/// approved sites - the one column-0 definition `CLASS_SCORE_CEILING = {...}` and `scored_row`'s lookup - so a
/// second assignment, an `update(...)` or a definition split over lines is a refusal, never a stale read. The
/// definition's right-hand side must decode, whole, as a JSON object of class string to number.
enum ETLCeilingTable {
    static let identifier = "CLASS_SCORE_CEILING"
    static let definitionPrefix = "CLASS_SCORE_CEILING = "
    static let lookupLine = "ceiling = CLASS_SCORE_CEILING.get(record.highway)"

    enum Refusal: Error, CustomStringConvertible {
        case unreadable(String)
        case definitions(Int)
        case unapproved(String)
        case notOneDict(String)
        var description: String {
            switch self {
            case let .unreadable(why): return "assemble.py unreadable: \(why)"
            case let .definitions(n): return "assemble.py defines \(identifier) on \(n) lines, need exactly 1"
            case let .unapproved(line): return "assemble.py names \(identifier) at an unapproved site: \(line)"
            case let .notOneDict(rhs): return "\(identifier)'s value is not one JSON-shaped dict: \(rhs)"
            }
        }
    }

    static var assembleURL: URL {
        URL(fileURLWithPath: #filePath)     // Tests/ScenicKitTests/ETLCeilingTable.swift
            .deletingLastPathComponent()    // Tests/ScenicKitTests
            .deletingLastPathComponent()    // Tests
            .deletingLastPathComponent()    // repo root
            .appendingPathComponent("services/etl/etl/assemble.py")
    }

    static func load() throws -> [String: Double] {
        let text: String
        do { text = try String(contentsOf: assembleURL, encoding: .utf8) } catch {
            throw Refusal.unreadable("\(error)")
        }
        return try parse(text)
    }

    static func parse(_ text: String) throws -> [String: Double] {
        let lines = text.replacingOccurrences(of: "\r\n", with: "\n").split(separator: "\n", omittingEmptySubsequences: false)
        var definitions: [String] = []
        for raw in lines {
            let line = String(raw)
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            guard line.contains(identifier), !trimmed.hasPrefix("#") else { continue }
            if line.hasPrefix(definitionPrefix) { definitions.append(line); continue }
            if trimmed == lookupLine { continue }
            throw Refusal.unapproved(line)
        }
        guard definitions.count == 1 else { throw Refusal.definitions(definitions.count) }
        let rhs = String(definitions[0].dropFirst(definitionPrefix.count)).trimmingCharacters(in: .whitespaces)
        guard rhs.hasPrefix("{"), rhs.hasSuffix("}"), let data = rhs.data(using: .utf8),
              let table = try? JSONDecoder().decode([String: Double].self, from: data) else {
            throw Refusal.notOneDict(rhs)
        }
        return table
    }
}
