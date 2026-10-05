#if canImport(GRDB)
/// One `places` row of corpus.sqlite (services/etl/etl/schema.py), as stored: the integer e7 pair is
/// returned untouched, nothing here converts it to degrees.
public struct Place: Equatable, Sendable {
    public let placeID: Int64
    public let osmType: String
    public let osmID: Int64
    public let cls: String
    public let name: String?
    public let lonE7: Int64
    public let latE7: Int64

    public init(placeID: Int64, osmType: String, osmID: Int64, cls: String, name: String?, lonE7: Int64,
                latE7: Int64) {
        self.placeID = placeID
        self.osmType = osmType
        self.osmID = osmID
        self.cls = cls
        self.name = name
        self.lonE7 = lonE7
        self.latE7 = latE7
    }
}
#endif
