import Foundation
import PlaceStore
import Testing

/// The OTA decision through the shipped entry point, `CorpusUpdater.decide` (T-0300 O1, O2). Every row is a
/// FUNCTION of a manifest variant and is run over both variants; each answer is compared whole, decision or typed
/// error, never one property of it. `noRowIgnoresItsVariant` holds the rows to that.
struct CorpusUpdateDecisionTests {
    static let variantA = CorpusManifest(
        version: "20261006T000000Z", schemaVersion: PlaceStore.schemaVersion, minAppBuild: 1,
        sha256: "7486da8f1e13943fae21a0b043f1e99640d7d8ebafb25266478b5cddae1272b5", bytes: 4096)
    static let variantB = CorpusManifest(
        version: "20261101T120000Z", schemaVersion: PlaceStore.schemaVersion, minAppBuild: 37,
        sha256: "bbeebd879e1dff6918546dc0c179fdde505f2a21591c9a9c96e36b054ec5af83", bytes: 1)
    static let fields = ["bytes", "min_app_build", "schema_version", "sha256", "version"]

    static func object(_ m: CorpusManifest) -> [String: Any] {
        ["version": m.version, "schema_version": m.schemaVersion, "min_app_build": m.minAppBuild,
         "sha256": m.sha256, "bytes": m.bytes]
    }

    static func json(_ value: Any) -> Data {
        (try? JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])) ?? Data()
    }

    static func edited(_ m: CorpusManifest, _ edit: (inout [String: Any]) -> Void) -> Data {
        var o = object(m)
        edit(&o)
        return json(o)
    }

    static func with(_ m: CorpusManifest, version: String? = nil, schemaVersion: Int? = nil, sha256: String? = nil,
                     bytes: Int? = nil) -> CorpusManifest {
        CorpusManifest(version: version ?? m.version, schemaVersion: schemaVersion ?? m.schemaVersion,
                       minAppBuild: m.minAppBuild, sha256: sha256 ?? m.sha256, bytes: bytes ?? m.bytes)
    }

    /// The first letter digit of the hash upper-cased: still 64 hex characters, but not the lowercase form.
    static func upperOne(_ hex: String) -> String {
        guard let i = hex.firstIndex(where: { "abcdef".contains($0) }) else { return hex }
        return hex.replacingCharacters(in: i...i, with: hex[i].uppercased())
    }

    static func rows(_ m: CorpusManifest) -> [CorpusDecisionRow] {
        let reader = PlaceStore.schemaVersion
        let build = m.minAppBuild
        let other = "19990101T000000Z"
        func row(_ name: String, _ manifest: CorpusManifest, build: Int, active: String?,
                 _ expected: CorpusUpdateDecision) -> CorpusDecisionRow {
            CorpusDecisionRow(name: name, json: json(object(manifest)), appBuild: build, activeVersion: active,
                              expected: .success(expected))
        }
        func refused(_ name: String, _ json: Data, _ error: CorpusUpdateError) -> CorpusDecisionRow {
            CorpusDecisionRow(name: name, json: json, appBuild: build, activeVersion: other, expected: .failure(error))
        }
        let up = with(m, schemaVersion: reader + 1)
        let down = with(m, schemaVersion: reader - 1)
        var rows = [
            row("schema_version == reader, min_app_build == build: download", m, build: build, active: other,
                .download(m)),
            row("schema_version reader + 1: refused", up, build: build, active: other,
                .refusedSchemaVersion(manifest: reader + 1, reader: reader)),
            row("schema_version reader - 1: refused", down, build: build, active: other,
                .refusedSchemaVersion(manifest: reader - 1, reader: reader)),
            row("schema_version reader + 1 at the active version: refused, not up to date", up, build: build,
                active: m.version, .refusedSchemaVersion(manifest: reader + 1, reader: reader)),
            row("min_app_build == build + 1: refused", m, build: build - 1, active: other,
                .refusedAppBuild(minAppBuild: build, build: build - 1)),
            row("min_app_build == build + 1 at the active version: refused, not up to date", m, build: build - 1,
                active: m.version, .refusedAppBuild(minAppBuild: build, build: build - 1)),
            row("build above min_app_build: download", m, build: build + 1, active: other, .download(m)),
            row("version equal to the active one: up to date, no download", m, build: build, active: m.version,
                .upToDate(version: m.version)),
            row("no active corpus: download", m, build: build, active: nil, .download(m)),
            row("active version one character short: download", m, build: build,
                active: String(m.version.dropLast()), .download(m)),
            row("bytes 1, the lower bound: download", with(m, bytes: 1), build: build, active: other,
                .download(with(m, bytes: 1))),
            refused("bytes 0: refused", edited(m) { $0["bytes"] = 0 }, .manifestValue(field: "bytes")),
            refused("bytes -1: refused", edited(m) { $0["bytes"] = -1 }, .manifestValue(field: "bytes")),
            refused("sha256 of 63 characters: refused", edited(m) { $0["sha256"] = String(m.sha256.dropLast()) },
                    .manifestValue(field: "sha256")),
            refused("sha256 of 65 characters: refused", edited(m) { $0["sha256"] = m.sha256 + "0" },
                    .manifestValue(field: "sha256")),
            refused("sha256 with one uppercase digit: refused", edited(m) { $0["sha256"] = upperOne(m.sha256) },
                    .manifestValue(field: "sha256")),
            refused("sha256 with a non-hex character: refused",
                    edited(m) { $0["sha256"] = String(m.sha256.dropLast()) + "g" }, .manifestValue(field: "sha256")),
            refused("version empty: refused", edited(m) { $0["version"] = "" }, .manifestValue(field: "version")),
            refused("an extra field: refused",
                    edited(m) { $0["signature"] = m.sha256 }, .manifestFields(missing: [], extra: ["signature"])),
            refused("bytes renamed size: refused", edited(m) { $0["size"] = m.bytes; $0["bytes"] = nil },
                    .manifestFields(missing: ["bytes"], extra: ["size"])),
            refused("a top-level array: refused", json([object(m)]), .manifestNotAnObject),
            refused("not JSON at all: refused", Data(m.version.utf8), .manifestNotAnObject),
        ]
        for field in fields {
            rows.append(refused("\(field) missing: refused", edited(m) { $0[field] = nil },
                                .manifestFields(missing: [field], extra: [])))
        }
        for field in ["schema_version", "min_app_build", "bytes"] {
            let value = object(m)[field] as? Int ?? 0
            let wrong: [(String, Any)] = [("a string", String(value)), ("a fraction", Double(value) + 0.5),
                                          ("a bool", true), ("null", NSNull())]
            for (label, bad) in wrong {
                rows.append(refused("\(field) as \(label): refused", edited(m) { $0[field] = bad },
                                    .manifestFieldType(field: field)))
            }
        }
        for field in ["version", "sha256"] {
            let wrong: [(String, Any)] = [("a number", build + 7), ("a bool", true), ("null", NSNull())]
            for (label, bad) in wrong {
                rows.append(refused("\(field) as \(label): refused", edited(m) { $0[field] = bad },
                                    .manifestFieldType(field: field)))
            }
        }
        return rows
    }

    static func run(_ rows: [CorpusDecisionRow]) {
        for row in rows {
            let got: Result<CorpusUpdateDecision, CorpusUpdateError>
            do {
                got = .success(try CorpusUpdater.decide(manifestJSON: row.json, appBuild: row.appBuild,
                                                        activeVersion: row.activeVersion))
            } catch let error as CorpusUpdateError {
                got = .failure(error)
            } catch {
                Issue.record("\(row.name): an untyped error \(error)")
                continue
            }
            #expect(got == row.expected, "\(row.name)")
        }
    }

    @Test func decisionTableVariantA() {
        Self.run(Self.rows(Self.variantA))
    }

    @Test func decisionTableVariantB() {
        Self.run(Self.rows(Self.variantB))
    }

    /// Success rows whose decision is the same under both variants by construction: a schema refusal carries only
    /// the manifest's and the reader's schema numbers. Their manifest bytes still differ (asserted below).
    static let variantFree: Set<String> = [
        "schema_version reader + 1: refused",
        "schema_version reader - 1: refused",
        "schema_version reader + 1 at the active version: refused, not up to date",
    ]

    @Test func noRowIgnoresItsVariant() {
        let a = Self.rows(Self.variantA)
        let b = Self.rows(Self.variantB)
        #expect(a.map(\.name) == b.map(\.name))
        #expect(a.count == 45)
        #expect(Self.variantFree.isSubset(of: Set(a.map(\.name))))
        for (x, y) in zip(a, b) {
            #expect(x.json != y.json, "\(x.name): the same manifest bytes under both variants")
            if case .success = x.expected, !Self.variantFree.contains(x.name) {
                #expect(x.expected != y.expected, "\(x.name): the same decision under both variants")
            }
        }
    }
}
