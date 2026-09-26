import Foundation
import Handoff
import ScenicKit

/// What `ops/plan --menu` DOES once its arguments are understood: the lines the terminal shows, or a thrown
/// refusal. Kept out of main.swift for PlanCommand's reason - a test can call this with the arguments a
/// person types, and cannot enter top-level code.
///
/// Every row carries its own Apple Maps URL: the pins are `PlanWaypoints.decisionPoints` over that row's own
/// table (the committed rule - at most 9, in route order) and the URL is Handoff's `AppleMapsDirections`,
/// which refuses more than 9. Built whole and returned: a run that refuses at row 2's URL prints nothing.
public enum MenuCommand {

    /// The menu `run` prints, from the recording `--recorded` names, under the cap `--max` set.
    public static func menu(_ arguments: MenuArguments) throws -> RouteMenu {
        let recorded = try RecordedAlternatives.load(directory: arguments.recorded, ladder: RouteMenu.ladder,
                                                     origin: arguments.origin,
                                                     destination: arguments.destination)
        return RouteMenu(fastest: recorded.fastest, candidates: recorded.candidates,
                         maxMinutes: arguments.maxMinutes)
    }

    public static func run(_ arguments: MenuArguments) throws -> [String] {
        let menu = try menu(arguments)
        var lines = ["ROUTER recorded \(arguments.recorded.lastPathComponent)", menu.header()]
        for (index, row) in menu.rows.enumerated() {
            let waypoints = PlanWaypoints.decisionPoints(table: row.table, path: row.path)
            let url = try AppleMapsDirections(source: arguments.origin, destination: arguments.destination,
                                              waypoints: waypoints).url()
            lines.append(row.line(index))
            lines.append("URL \(index) waypoints=\(waypoints.count) \(url.absoluteString)")
        }
        return lines
    }
}
