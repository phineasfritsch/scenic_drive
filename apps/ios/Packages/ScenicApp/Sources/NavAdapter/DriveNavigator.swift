import Combine
import CoreLocation
import FerrostarCore
import FerrostarCoreFFI
import Foundation
import ScenicKit

/// The drive, on Ferrostar (T-0321). A thin shell: Ferrostar draws the steps and snaps the puck; every decision -
/// off-route, reroute, rejoin, the motion gate, which answer to take - is ScenicKit's DriveController.
///
/// Every location fix is tapped before Ferrostar sees it and forwarded; every reachability report is forwarded;
/// the returned commands are carried out and nothing else is: `.send` starts the reroute under its ticket,
/// `.cancel` cancels that task, and each answer goes back under the ticket it was sent with, so a late one is
/// dropped by the controller. Ferrostar's own deviation tracking is off and its delegate answers `.doNothing`.
@MainActor
public final class DriveNavigator: ObservableObject {
    /// What the drive screen (T-0324) shows: the controller's mode and surface after the latest input.
    @Published public private(set) var mode: DriveMode
    @Published public private(set) var surface: DriveSurface
    /// What the drive screen renders (T-0324 R2): ScenicKit's DriveDisplay for the session after the latest input.
    @Published public private(set) var display: DriveDisplay
    public let core: FerrostarCore

    private var controller: DriveController
    private var voice: DriveVoice
    private let sender: any RerouteSending
    private let tap: DriveLocationTap
    private let connectivity = DriveConnectivity()
    private let decisions = FerrostarDecisionsOff()
    private var reroutes: [Int: Task<Void, Never>] = [:]

    /// nil when the preview is not a drivable line with its pins on it (DriveSession's own check).
    public init?(preview: PlanPreview, sender: any RerouteSending = RerouteUnavailable()) {
        guard let session = DriveSession(line: preview.route, waypoints: preview.waypoints, lambda: preview.lambda,
                                         online: true) else { return nil }
        controller = DriveController(session: session)
        voice = DriveVoice(session: session)
        mode = session.mode
        surface = session.surface
        display = DriveDisplay(session: session)
        self.sender = sender
        let tap = DriveLocationTap(inner: CoreLocationProvider(activityType: .automotiveNavigation,
                                                               allowBackgroundLocationUpdates: true))
        self.tap = tap
        let route = FerrostarDriveRoute.route(line: session.line.coordinates, legs: session.legs)
        core = FerrostarCore(routeProvider: .customProvider(PlannedRouteProvider(route: route)),
                             locationProvider: tap,
                             navigationControllerConfig: FerrostarDriveRoute.config(),
                             networkSession: URLSession.shared)
        core.delegate = decisions
        tap.onLocations = { [weak self] locations in self?.forward(locations) }
        connectivity.onChange = { [weak self] online in self?.reachability(online) }
    }

    /// Starts guidance on the planned line and the reachability reports.
    public func start() throws {
        let session = controller.session
        try core.startNavigation(route: FerrostarDriveRoute.route(line: session.line.coordinates, legs: session.legs))
        connectivity.start()
    }

    /// Ends the drive: guidance, reachability, and any reroute still out.
    public func stop() {
        core.stopNavigation()
        connectivity.stop()
        for task in reroutes.values { task.cancel() }
        reroutes.removeAll()
    }

    private func forward(_ locations: [UserLocation]) {
        for location in locations {
            act(controller.observe(DriveFix(
                coordinate: Coordinate(latitude: location.coordinates.lat, longitude: location.coordinates.lng),
                speedMetersPerSecond: location.speed?.value ?? -1,
                timestamp: location.timestamp.timeIntervalSinceReferenceDate)))
        }
        publish()
    }

    private func reachability(_ online: Bool) {
        act(controller.connectivity(online: online))
        publish()
    }

    private func act(_ commands: [DriveCommand]) {
        for command in commands {
            switch command {
            case let .send(request, ticket):
                let sender = self.sender
                reroutes[ticket] = Task { [weak self] in
                    do {
                        let reply = try await sender.reroute(request)
                        self?.arrived(ticket: ticket, reply: reply)
                    } catch {
                        self?.failed(ticket: ticket)
                    }
                }
            case let .cancel(ticket):
                reroutes.removeValue(forKey: ticket)?.cancel()
            }
        }
    }

    private func arrived(ticket: Int, reply: RerouteReply) {
        reroutes[ticket] = nil
        if controller.rerouteArrived(ticket: ticket, reply: reply) {
            let session = controller.session
            try? core.startNavigation(route: FerrostarDriveRoute.route(line: session.line.coordinates,
                                                                       legs: session.legs))
        }
        publish()
    }

    private func failed(ticket: Int) {
        reroutes[ticket] = nil
        controller.rerouteFailed(ticket: ticket)
        publish()
    }

    private func publish() {
        mode = controller.session.mode
        surface = controller.session.surface
        display = DriveDisplay(session: controller.session)
        for text in voice.utterances(after: controller.session) { speak(text) }
    }

    /// One line ScenicKit's DriveVoice chose, spoken unchanged through Ferrostar's own observer (T-0329 R1).
    private func speak(_ text: String) {
        let instruction = SpokenInstruction(text: text, ssml: nil, triggerDistanceBeforeManeuver: 0, utteranceId: UUID())
        core.spokenInstructionObserver.spokenInstructionTriggered(instruction)
    }
}
