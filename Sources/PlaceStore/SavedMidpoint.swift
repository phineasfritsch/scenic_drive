/// A saved segment's midpoint at exactly five decimal places, stored as fixed-point 1e-5 integers (T-0290 R3).
///
/// The public initialiser refuses - never rounds - a coordinate that is not finite, is outside its range, or has
/// more than five decimals; latitude is checked before longitude (R4).
public struct SavedMidpoint: Equatable, Sendable {
    public let latE5: Int
    public let lonE5: Int

    /// The inclusive bounds extractway.py accepts.
    static let maxLatitude: Double = 90
    static let maxLongitude: Double = 180

    public init(latitude: Double, longitude: Double) throws {
        latE5 = try FiveDecimals.fixedPoint(latitude, in: -Self.maxLatitude...Self.maxLatitude, field: .latitude)
        lonE5 = try FiveDecimals.fixedPoint(longitude, in: -Self.maxLongitude...Self.maxLongitude, field: .longitude)
    }

    /// A row the store wrote; its CHECK constraints hold the same bounds (R3a).
    init(latE5: Int, lonE5: Int) {
        self.latE5 = latE5
        self.lonE5 = lonE5
    }

    public var latitude: Double { FiveDecimals.degrees(latE5) }
    public var longitude: Double { FiveDecimals.degrees(lonE5) }
}
