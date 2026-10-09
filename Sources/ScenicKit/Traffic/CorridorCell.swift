/// The corridor cell a learned ratio is kept for: an H3 resolution-8 index as uber/h3 spells it (T-0320 R1).
///
/// T-0325 R1: the device makes one from a point with `containing(latitudeDegrees:longitudeDegrees:)`, a copy of
/// Telemetry's port of `latLngToCell` from uber/h3 v4.1.0 (https://github.com/uber/h3, Copyright Uber Technologies,
/// Inc., Apache License 2.0) - H3FaceProjection, H3CoordIJK, H3BaseCells and H3IndexBuilder in this folder - run at
/// resolution 8. ScenicKit may not import Telemetry, so the four files are copied, not shared. The copy is pinned by
/// exact equality to h3-py 4.1.2 at resolutions 5 (Telemetry's) and 8 (CorridorCellTests).
public struct CorridorCell: Hashable, Sendable {
    /// The resolution corridors are learned at (mean cell area 0.737 km^2).
    public static let resolution = 8
    /// `M_PI_180`.
    static let radiansPerDegree = 0.0174532925199432957692369076848861271111

    public let index: UInt64

    public init(index: UInt64) {
        self.index = index
    }

    /// The resolution-8 cell containing a point given in DEGREES; nil unless the latitude is in -90...90 and the
    /// longitude in -180...180 (NaN and the infinities are in neither).
    public static func containing(latitudeDegrees: Double, longitudeDegrees: Double) -> CorridorCell? {
        containing(latitudeDegrees: latitudeDegrees, longitudeDegrees: longitudeDegrees, resolution: resolution)
    }

    /// The port at any resolution - 8 for corridors; 5 only to show the copy still answers what Telemetry's does.
    static func containing(latitudeDegrees: Double, longitudeDegrees: Double, resolution: Int) -> CorridorCell? {
        guard (-90...90).contains(latitudeDegrees), (-180...180).contains(longitudeDegrees) else { return nil }
        let projected = H3FaceProjection.faceIJK(latitude: latitudeDegrees * radiansPerDegree,
                                                 longitude: longitudeDegrees * radiansPerDegree,
                                                 resolution: resolution)
        return H3IndexBuilder.index(face: projected.face, coord: projected.coord, resolution: resolution)
            .map(CorridorCell.init(index:))
    }
}
