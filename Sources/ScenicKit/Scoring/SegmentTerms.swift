import Foundation

/// The measured properties of one way, in the terms the scenic formula consumes.
///
/// Every term is in `0...1` and every one is **rank-normalised or scaled by the ETL before it arrives**. This
/// type does no measuring; it is the boundary between "what the rasters and OSM said" and "what the formula
/// does with it", and keeping that boundary sharp is what lets the formula be tested on Linux in
/// milliseconds with no GDAL, no PostGIS and no 3DEP tiles anywhere near it.
///
/// **Terms are validated, never clamped.** A value outside `0...1` is a bug in the ETL, and quantising it to
/// the nearest legal number would hide the bug behind a plausible score. `SegmentScore.score(for:)` returns
/// nil for such a way so the caller has to decide, and `ops/route-autopsy` can say which term was wrong.
public struct SegmentTerms: Equatable, Sendable {

    // MARK: - M, how the road drives

    /// Curvature, from the Curvature project's method reimplemented in the ETL.
    public var curvature: Double
    /// Elevation gained over the way, from 3x3-smoothed 3DEP bare earth.
    public var elevationGain: Double
    /// How close the way's character is to a 65 km/h drive - the plan's triangular fit.
    public var speedFit: Double
    /// How much the way wanders relative to its straight-line length.
    public var sinuosity: Double

    // MARK: - E, what the road goes past

    /// Tree canopy cover, from USFS TCC.
    public var canopy: Double
    /// Terrain relief nearby, from 3DEP.
    public var relief: Double
    /// Impervious surface from NLCD. Enters the formula as `1 - impervious`: parking lots are not scenery.
    public var impervious: Double
    /// Density of interesting places, from the curated corpus and the allowlist.
    public var pointsOfInterest: Double
    /// Water nearby.
    public var water: Double
    /// Street furniture - signs, lights, barriers. Enters as `1 - furniture`.
    public var furniture: Double

    /// A designated scenic byway (FHWA or Caltrans). A bonus on E, capped, not a term of its own - the plan
    /// treats it as corroboration of the rasters rather than as a substitute for them.
    public var isByway: Bool

    // MARK: - the road itself

    /// OSM `highway` value. Decides the motorway rule and which surface default applies.
    public var highway: String
    /// OSM `surface`, or nil when the way carries no surface tag - which is the common case on rural lanes
    /// and is **not** evidence of being unpaved.
    public var surface: String?
    /// Length of tunnel on the way, in metres.
    public var tunnelMeters: Double
    /// Distance to the nearest motorway, in metres. `.infinity` when there is none nearby.
    public var metersToNearestMotorway: Double

    public init(curvature: Double = 0,
                elevationGain: Double = 0,
                speedFit: Double = 0,
                sinuosity: Double = 0,
                canopy: Double = 0,
                relief: Double = 0,
                impervious: Double = 0,
                pointsOfInterest: Double = 0,
                water: Double = 0,
                furniture: Double = 0,
                isByway: Bool = false,
                highway: String = "residential",
                surface: String? = nil,
                tunnelMeters: Double = 0,
                metersToNearestMotorway: Double = .infinity) {
        self.curvature = curvature
        self.elevationGain = elevationGain
        self.speedFit = speedFit
        self.sinuosity = sinuosity
        self.canopy = canopy
        self.relief = relief
        self.impervious = impervious
        self.pointsOfInterest = pointsOfInterest
        self.water = water
        self.furniture = furniture
        self.isByway = isByway
        self.highway = highway
        self.surface = surface
        self.tunnelMeters = tunnelMeters
        self.metersToNearestMotorway = metersToNearestMotorway
    }

    /// Every `0...1` term, so validation cannot silently miss one that was added later.
    var unitTerms: [(name: String, value: Double)] {
        [("curvature", curvature), ("elevationGain", elevationGain), ("speedFit", speedFit),
         ("sinuosity", sinuosity), ("canopy", canopy), ("relief", relief), ("impervious", impervious),
         ("pointsOfInterest", pointsOfInterest), ("water", water), ("furniture", furniture)]
    }
}
