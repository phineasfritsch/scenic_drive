import Foundation
import Testing
@testable import Telemetry

/// P-PRIV-05's location half: the only place telemetry carries is an H3 resolution-5 cell, and the encoder
/// that makes it is H3 - pinned by EXACT equality of the shipping entry point, `H3Cell.containing`, against
/// uber/h3's own published reference rows (T-0265 R5). Fixtures/rand05centers.txt is
/// https://github.com/uber/h3/blob/v4.1.0/tests/inputfiles/rand05centers.txt copied unedited (sha256
/// 8bf6e8d5597ea7d72a931e239bb91bc1184510abc82c92e789cfee1119791066): 5000 rows `h3index lat lng`, each a res-5
/// cell and its center in degrees.
@Suite("H3 resolution-5 reference cells") struct H3ReferenceCellTests {
    static let fixture = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        .appendingPathComponent("Fixtures").appendingPathComponent("rand05centers.txt")

    /// The first ten rows of that file, retyped here so that a fixture that stopped loading could not make
    /// the population test below the only witness.
    static let published: [(cell: String, latitude: Double, longitude: Double)] = [
        ("850dab63fffffff", 67.194014, 191.598258),
        ("850336b7fffffff", 87.372197, 166.176925),
        ("85440d83fffffff", 27.350796, 272.064443),
        ("85f2316bfffffff", -79.704099, 209.043753),
        ("8503053bfffffff", 87.178177, 270.372677),
        ("85d70b6bfffffff", -52.743559, 34.199852),
        ("850ee59bfffffff", 55.810429, 282.843962),
        ("85eb885bfffffff", -60.693672, 187.742078),
        ("85026c63fffffff", 74.269230, 290.224650),
        ("857a9983fffffff", 8.317316, 47.328903),
    ]

    @Test("ten published H3 reference cells encode by exact equality")
    func tenPublishedCells() {
        let got = Self.published.map {
            H3Cell.containing(latitudeDegrees: $0.latitude, longitudeDegrees: $0.longitude)?.hexString ?? "nil"
        }
        #expect(got == Self.published.map(\.cell))
    }

    @Test("every row of uber/h3 rand05centers.txt encodes to its published cell")
    func everyPublishedRow() throws {
        let text = try String(contentsOf: Self.fixture, encoding: .utf8)
        let rows = text.split(separator: "\n")
        #expect(rows.count == 5000)
        var mismatches: [String] = []
        for line in rows {
            let parts = line.split(separator: " ")
            guard parts.count == 3, let latitude = Double(parts[1]), let longitude = Double(parts[2]) else {
                mismatches.append("unreadable row: \(line)")
                continue
            }
            let got = H3Cell.containing(latitudeDegrees: latitude, longitudeDegrees: longitude)?.hexString ?? "nil"
            if got != String(parts[0]) {
                mismatches.append("\(parts[0]) at \(latitude),\(longitude) encoded as \(got)")
            }
        }
        #expect(mismatches.isEmpty, "\(mismatches.count) of \(rows.count) differ; first: \(mismatches.prefix(5))")
    }

    @Test("every point around the twelve res-5 pentagons encodes to uber/h3's own cell")
    func everyPentagonPoint() throws {
        let mismatches = try Self.mismatches(in: "pentagon05points.txt", expectedRows: 5184)
        #expect(mismatches.isEmpty, "\(mismatches.count) differ; first: \(mismatches.prefix(5))")
    }

    /// Fixtures/pentagon05points.txt: rand05centers.txt never reaches the pentagon k-axis correction (T-0265,
    /// measured by the mutation population), so 5184 points ring the twelve res-5 pentagons at 1-40 km, each
    /// with the cell h3-py 4.1.2 (uber/h3 C v4.1.0) assigns it - Fixtures/make_pentagon05points.py.
    static func mismatches(in file: String, expectedRows: Int) throws -> [String] {
        let url = fixture.deletingLastPathComponent().appendingPathComponent(file)
        let rows = try String(contentsOf: url, encoding: .utf8).split(separator: "\n")
        var out = rows.count == expectedRows ? [] : ["\(rows.count) rows, expected \(expectedRows)"]
        for line in rows {
            let parts = line.split(separator: " ")
            guard parts.count == 3, let latitude = Double(parts[1]), let longitude = Double(parts[2]) else {
                out.append("unreadable row: \(line)")
                continue
            }
            let got = H3Cell.containing(latitudeDegrees: latitude, longitudeDegrees: longitude)?.hexString ?? "nil"
            if got != String(parts[0]) {
                out.append("\(parts[0]) at \(latitude),\(longitude) encoded as \(got)")
            }
        }
        return out
    }

    @Test("a non-finite coordinate has no cell")
    func nonFiniteHasNoCell() {
        #expect(H3Cell.containing(latitudeDegrees: .nan, longitudeDegrees: 0) == nil)
        #expect(H3Cell.containing(latitudeDegrees: 0, longitudeDegrees: .infinity) == nil)
    }
}
