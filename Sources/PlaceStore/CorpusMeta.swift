#if canImport(GRDB)
/// The rows of corpus.sqlite's `meta` table a device reads before it trusts the file.
///
/// `meta` is key/value on purpose (services/etl/etl/schema.py rule 1): a new key is not a DDL change. This type
/// names only the keys the device acts on - the OTA comparison (`schema_version`, `min_app_build`), what the
/// file is (`region`, `corpus_version`, `built_at`) and the credit every map surface shows (`attribution`).
public struct CorpusMeta: Equatable, Sendable {
    public let schemaVersion: Int
    public let minAppBuild: Int
    public let region: String
    public let corpusVersion: String
    public let builtAt: String
    public let attribution: String

    public init(schemaVersion: Int, minAppBuild: Int, region: String, corpusVersion: String, builtAt: String,
                attribution: String) {
        self.schemaVersion = schemaVersion
        self.minAppBuild = minAppBuild
        self.region = region
        self.corpusVersion = corpusVersion
        self.builtAt = builtAt
        self.attribution = attribution
    }
}
#endif
