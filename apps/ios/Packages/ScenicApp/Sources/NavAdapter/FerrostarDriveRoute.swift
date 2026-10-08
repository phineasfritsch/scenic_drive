import FerrostarCore
import FerrostarCoreFFI
import Foundation
import ScenicKit

/// ScenicKit's planned line and legs as a Ferrostar Route (T-0321 R4/R5): the geometry is the line, one step per
/// DriveLeg, a break waypoint at each end and a via waypoint at each pin. No instruction comes over the wire yet,
/// so each step's banner says where the leg ends.
enum FerrostarDriveRoute {
    /// Step advance as Ferrostar's demo sets it; deviation tracking OFF - off-route is DriveSession's.
    static func config() -> SwiftNavigationControllerConfig {
        SwiftNavigationControllerConfig(
            waypointAdvance: .waypointWithinRange(100.0),
            stepAdvanceCondition: stepAdvanceDistanceEntryAndExit(distanceToEndOfStep: 30, distanceAfterEndOfStep: 5,
                                                                  minimumHorizontalAccuracy: 32),
            arrivalStepAdvanceCondition: stepAdvanceDistanceToEndOfStep(distance: 10, minimumHorizontalAccuracy: 32),
            routeDeviationTracking: .none,
            snappedLocationCourseFiltering: .raw
        )
    }

    static func route(line: [Coordinate], legs: [DriveLeg]) -> Route {
        let geometry = line.map(point)
        let lats = line.map(\.latitude), lngs = line.map(\.longitude)
        let bbox = BoundingBox(sw: GeographicCoordinate(lat: lats.min() ?? 0, lng: lngs.min() ?? 0),
                               ne: GeographicCoordinate(lat: lats.max() ?? 0, lng: lngs.max() ?? 0))
        var waypoints = [Waypoint(coordinate: geometry[0], kind: .break)]
        for leg in legs {
            waypoints.append(Waypoint(coordinate: point(leg.coordinates[leg.coordinates.count - 1]),
                                      kind: leg.maneuver == .arrive ? .break : .via))
        }
        return Route(geometry: geometry, bbox: bbox, distance: legs.reduce(0) { $0 + $1.lengthMeters },
                     waypoints: waypoints, steps: legs.map(step))
    }

    private static func step(_ leg: DriveLeg) -> RouteStep {
        let text = leg.maneuver == .arrive ? "Arrive at your destination" : "Continue to the next scenic stop"
        let banner = VisualInstruction(
            primaryContent: VisualInstructionContent(text: text, maneuverType: nil, maneuverModifier: nil,
                                                     roundaboutExitDegrees: nil, laneInfo: nil, exitNumbers: []),
            secondaryContent: nil, subContent: nil, triggerDistanceBeforeManeuver: leg.lengthMeters)
        return RouteStep(geometry: leg.coordinates.map(point), distance: leg.lengthMeters, duration: 0, roadName: nil,
                         exits: [], instruction: text, visualInstructions: [banner], spokenInstructions: [],
                         annotations: nil, incidents: [], drivingSide: nil, roundaboutExitNumber: nil)
    }

    private static func point(_ c: Coordinate) -> GeographicCoordinate {
        GeographicCoordinate(lat: c.latitude, lng: c.longitude)
    }
}
