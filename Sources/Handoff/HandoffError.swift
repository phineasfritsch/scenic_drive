import Foundation

/// Why a handoff URL could not be built.
///
/// Every case here is a refusal, and refusing is the point. The alternative to each of them is a URL that
/// opens Apple Maps successfully and navigates somewhere other than the route the user was shown - a
/// failure with no error, no log line and no way to notice except by driving it.
public enum HandoffError: Error, Equatable, Sendable {
    /// A latitude, longitude, or both is NaN, infinite, or outside the WGS-84 range.
    case notACoordinate(latitude: Double, longitude: Double)

    /// More intermediate stops than `AppleMapsDirections.maxWaypoints`.
    ///
    /// Deliberately not a truncation. Dropping the tail of the waypoint list yields a route that is shorter,
    /// still plausible, and no longer the scenic one - the pinned waypoints ARE the scenic middle, so losing
    /// them loses the product. Choosing which stops matter is the planner's job, upstream of here.
    case tooManyWaypoints(count: Int, max: Int)

    /// A menu row's printed URL that does not parse as an `https://maps.apple.com` URL (T-0246). Refused rather
    /// than rebuilt: the row's URL is the CLI's, and a rebuilt one would be a second URL nothing compares.
    case notAMapsURL(String)

    /// A menu bundle that does not decode, or decodes to something the sheet cannot show (T-0246).
    case notAMenu(String)
}

extension HandoffError: CustomStringConvertible {
    public var description: String {
        switch self {
        case let .notACoordinate(latitude, longitude):
            return "not a coordinate: \(latitude), \(longitude)"
        case let .tooManyWaypoints(count, max):
            return "\(count) waypoints exceeds the \(max) this builder will pin; "
                + "select decision points upstream rather than truncating here"
        case let .notAMapsURL(text):
            return "not an Apple Maps URL: \(text)"
        case let .notAMenu(reason):
            return "not a drive menu: \(reason)"
        }
    }
}
