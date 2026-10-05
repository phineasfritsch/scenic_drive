import Foundation

/// An H3 resolution-5 cell (mean area 252.9 km^2) - the only location telemetry carries (P-PRIV-05).
///
/// The encoder is a Foundation-only port of `latLngToCell` from uber/h3 v4.1.0 (https://github.com/uber/h3,
/// Copyright Uber Technologies, Inc., Apache License 2.0) at ONE fixed resolution: H3FaceProjection,
/// H3CoordIJK, H3BaseCells and H3IndexBuilder. It is pinned by exact equality against every row of uber/h3
/// own test input tests/inputfiles/rand05centers.txt (T-0265 R5). There is no public initializer from an
/// index: the only way to make a cell is to name the point it contains, at resolution 5.
public struct H3Cell: Hashable, Sendable {
    /// The one resolution this type encodes.
    public static let resolution = 5
    /// `M_PI_180`.
    static let radiansPerDegree = 0.0174532925199432957692369076848861271111

    /// The 64-bit H3 index.
    public let index: UInt64

    init(index: UInt64) {
        self.index = index
    }

    /// The resolution-5 cell containing a point given in DEGREES, or nil for a non-finite input.
    public static func containing(latitudeDegrees: Double, longitudeDegrees: Double) -> H3Cell? {
        guard latitudeDegrees.isFinite, longitudeDegrees.isFinite else { return nil }
        let projected = H3FaceProjection.faceIJK(latitude: latitudeDegrees * radiansPerDegree,
                                                 longitude: longitudeDegrees * radiansPerDegree,
                                                 resolution: resolution)
        return H3IndexBuilder.index(face: projected.face, coord: projected.coord, resolution: resolution)
            .map(H3Cell.init(index:))
    }

    /// The canonical lowercase hex form, as `h3ToString` prints it (e.g. `85283473fffffff`).
    public var hexString: String {
        String(index, radix: 16)
    }
}
