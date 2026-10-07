import Foundation

/// The corpus OTA manifest the publisher serves beside each corpus (plan, Runtime lifecycles / OTA: "R2 manifest
/// {version, schema_version, min_app_build, sha256, bytes}"). Every field is required and typed (T-0300 O1).
///
/// `parse(_:)` is the only way the device reads one: it refuses - with a typed `CorpusUpdateError`, never a crash -
/// a body that is not a JSON object, a key set that is not exactly the five, a field of the wrong JSON type, and a
/// value out of range (an empty `version`, `bytes` < 1, a `sha256` that is not 64 lowercase hex digits).
public struct CorpusManifest: Codable, Equatable, Sendable {
    /// The `meta.corpus_version` of the corpus this manifest names, e.g. "20261006T000000Z".
    public let version: String
    /// The corpus schema; downloaded only when it equals `PlaceStore.schemaVersion`.
    public let schemaVersion: Int
    /// The oldest app build that may download it.
    public let minAppBuild: Int
    /// The corpus file's SHA-256, 64 lowercase hex digits.
    public let sha256: String
    /// The corpus file's size in bytes.
    public let bytes: Int

    enum CodingKeys: String, CodingKey, CaseIterable {
        case version
        case schemaVersion = "schema_version"
        case minAppBuild = "min_app_build"
        case sha256
        case bytes
    }

    /// The manifest's key set, exactly.
    public static let fields: Set<String> = ["version", "schema_version", "min_app_build", "sha256", "bytes"]

    public init(version: String, schemaVersion: Int, minAppBuild: Int, sha256: String, bytes: Int) {
        self.version = version
        self.schemaVersion = schemaVersion
        self.minAppBuild = minAppBuild
        self.sha256 = sha256
        self.bytes = bytes
    }

    /// Each field decoded on its own, so a wrong JSON type names its field: JSONDecoder's own error leaves the
    /// coding path empty for some of them (see `parse`).
    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        func field<T: Decodable>(_ type: T.Type, _ key: CodingKeys) throws -> T {
            do {
                return try container.decode(type, forKey: key)
            } catch is DecodingError {
                throw CorpusUpdateError.manifestFieldType(field: key.rawValue)
            }
        }
        version = try field(String.self, .version)
        schemaVersion = try field(Int.self, .schemaVersion)
        minAppBuild = try field(Int.self, .minAppBuild)
        sha256 = try field(String.self, .sha256)
        bytes = try field(Int.self, .bytes)
    }

    public static func parse(_ json: Data) throws -> CorpusManifest {
        guard let object = try? JSONSerialization.jsonObject(with: json, options: []),
              let dictionary = object as? [String: Any] else {
            throw CorpusUpdateError.manifestNotAnObject
        }
        // JSONDecoder ignores a key it was not asked for, so the set is compared before it runs.
        let keys = Set(dictionary.keys)
        guard keys == fields else {
            throw CorpusUpdateError.manifestFields(missing: fields.subtracting(keys).sorted(),
                                                   extra: keys.subtracting(fields).sorted())
        }
        let manifest: CorpusManifest
        do {
            manifest = try JSONDecoder().decode(CorpusManifest.self, from: json)
        } catch is DecodingError {
            // Refused before any field was read (measured on Swift 6.3 for a fraction where an Int belongs): the
            // field is the first, in key order, whose value does not bridge to its declared type.
            let ints: Set<String> = ["schema_version", "min_app_build", "bytes"]
            let named = CodingKeys.allCases.map(\.rawValue).first { key in
                ints.contains(key) ? !(dictionary[key] is Int) : !(dictionary[key] is String)
            }
            throw CorpusUpdateError.manifestFieldType(field: named ?? "")
        }
        guard !manifest.version.isEmpty else { throw CorpusUpdateError.manifestValue(field: "version") }
        guard manifest.bytes >= 1 else { throw CorpusUpdateError.manifestValue(field: "bytes") }
        guard manifest.sha256.utf8.count == 64,
              manifest.sha256.utf8.allSatisfy({ (0x30...0x39).contains($0) || (0x61...0x66).contains($0) }) else {
            throw CorpusUpdateError.manifestValue(field: "sha256")
        }
        return manifest
    }
}
