import Foundation
import ScenicAPIClient
import ScenicKit

/// The T-0314 tests' one way to drive the shipping entry point, `LoopClient.loop`, against a counting fake, and the
/// /loop answers they read: a square loop (four different roads, nothing retraced) and an out-and-back (one road
/// driven both ways - the round_trip failure the retrace check exists for).
enum LoopWire {
    static let base = URL(string: "https://scenic-api.test")!
    static let start = Coordinate(latitude: 34.02, longitude: -118.49)

    static let square = [Coordinate(latitude: 34.02, longitude: -118.49), Coordinate(latitude: 34.04, longitude: -118.49),
                         Coordinate(latitude: 34.04, longitude: -118.46), Coordinate(latitude: 34.02, longitude: -118.46),
                         Coordinate(latitude: 34.02, longitude: -118.49)]
    static let pins = [Coordinate(latitude: 34.04, longitude: -118.49), Coordinate(latitude: 34.04, longitude: -118.46),
                       Coordinate(latitude: 34.02, longitude: -118.46)]
    static let outAndBack = [Coordinate(latitude: 34.02, longitude: -118.49),
                             Coordinate(latitude: 34.05, longitude: -118.49),
                             Coordinate(latitude: 34.02, longitude: -118.49)]

    static let squareRoute = #""route":{"coordinates":[[-118.49,34.02],[-118.49,34.04],[-118.46,34.04],[-118.46,34.02],[-118.49,34.02]],"distance_m":10000}"#
    static let squarePins = #""waypoints":[{"lat":34.04,"lon":-118.49},{"lat":34.04,"lon":-118.46},{"lat":34.02,"lon":-118.46}]"#
    static let tail = #""duration_s":2700,"retrace_fraction":0.02,"attempts":1,"seed":7,"target_distance_m":30000,"minutes":45,"eta_is_estimate":true,"apple_maps_url":"https://maps.apple.com/directions?destination=0,0&mode=driving""#

    static let squareBody = "{\(squareRoute),\(squarePins),\(tail),\"closures_hazard\":{\"state\":\"fresh\"}}"
    static let outAndBackBody = #"{"route":{"coordinates":[[-118.49,34.02],[-118.49,34.05],[-118.49,34.02]],"distance_m":6700},"waypoints":[{"lat":34.05,"lon":-118.49}],"# + tail + "}"
    static let noEstimateBody = squareBody.replacingOccurrences(of: #""eta_is_estimate":true,"#, with: "")
    static let falseEstimateBody = squareBody.replacingOccurrences(of: #""eta_is_estimate":true"#,
                                                                   with: #""eta_is_estimate":false"#)
    static let onePointBody = #"{"route":{"coordinates":[[-118.49,34.02]],"distance_m":0},"waypoints":[],"# + tail + "}"

    static func pinsBody(_ count: Int) -> String {
        let pin = #"{"lat":34.04,"lon":-118.49}"#
        return "{\(squareRoute),\"waypoints\":[\(Array(repeating: pin, count: count).joined(separator: ","))],\(tail)}"
    }

    static func response(route: [Coordinate] = square, distance: Double = 10_000,
                         waypoints: [Coordinate] = pins, estimate: Bool = true) -> LoopResponse {
        LoopResponse(route: route, distanceMeters: distance, durationSeconds: 2_700, retraceFraction: 0.02,
                     minutes: 45, etaIsEstimate: estimate, waypoints: waypoints)
    }

    static func reply(_ status: Int, _ body: String) -> PlanHTTPReply {
        PlanHTTPReply(status: status, body: Data(body.utf8))
    }

    static func loop(through transport: any PlanTransport, from start: Coordinate = start, minutes: Int = 45,
                     vehicle: VehicleProfile = .standard, install: Bool = true,
                     account: (any AccountTokenProvider)? = nil) async -> Result<LoopResponse, LoopError> {
        let client = LoopClient(base: base, transport: transport, installID: install ? PlanWire.install : nil,
                                accountToken: account)
        do {
            return .success(try await client.loop(from: start, minutes: minutes, vehicle: vehicle))
        } catch {
            return .failure(error)
        }
    }
}
