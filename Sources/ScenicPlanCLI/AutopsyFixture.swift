import Foundation
import ScenicKit

/// `ops/route-autopsy ... --fixture <dir>`: a bad drive written down as a pinned NEGATIVE fixture before any
/// weight changes - the plan's gate-failure playbook (T-0327 R6).
///
/// What a fixture is: the recordings the plan actually read (fastest.json and exactly the lambdas the trace
/// visited, byte for byte), the terms file it was autopsied with, `fixture.json` (verdict, the arguments,
/// the chosen lambda, the chosen route's way ids - what a fix must move the engine off), and `autopsy.txt`,
/// which is the autopsy RE-RUN against the written directory, so the pinned text is exactly what the fixture
/// reproduces on its own.
///
/// Refused: a directory with no `Tests` path component (a fixture lives in the test tree or nowhere), a
/// directory that exists (a pinned fixture is never overwritten), and a live router (nothing on disk to pin;
/// `AutopsyArguments.parse` refuses that one before a request is made).
enum AutopsyFixture {

    struct Failure: Error, CustomStringConvertible {
        let description: String
    }

    static let autopsyFileName = "autopsy.txt"
    static let fixtureFileName = "fixture.json"
    static let termsFileName = "terms.json"

    static func write(_ arguments: AutopsyArguments, plan: ScenicPlan, steps: [TracingRouteSource.Step],
                      into directory: URL) throws -> [String] {
        guard case let .recorded(recording) = arguments.plan.router else {
            throw Failure(description: "--fixture needs --recorded")
        }
        guard directory.standardizedFileURL.pathComponents.contains("Tests") else {
            throw Failure(description: "a fixture is written under Tests/ (e.g. Tests/Fixtures/negative/<name>), "
                + "not \(directory.path)")
        }
        let files = FileManager.default
        guard !files.fileExists(atPath: directory.path) else {
            throw Failure(description: "\(directory.path) exists: a pinned fixture is never overwritten")
        }
        try files.createDirectory(at: directory, withIntermediateDirectories: true)

        var names = [RecordedRouteSource.fastestFileName]
        for step in steps where !names.contains(RecordedRouteSource.fileName(forLambda: step.lambda)) {
            names.append(RecordedRouteSource.fileName(forLambda: step.lambda))
        }
        for name in names {
            try files.copyItem(at: recording.appendingPathComponent(name),
                               to: directory.appendingPathComponent(name))
        }
        var replayTerms: URL?
        if let terms = arguments.terms {
            replayTerms = directory.appendingPathComponent(termsFileName)
            try files.copyItem(at: terms, to: replayTerms!)
        }
        try Data(fixtureJSON(arguments, plan: plan, terms: replayTerms != nil).utf8)
            .write(to: directory.appendingPathComponent(fixtureFileName))

        let replay = try AutopsyCommand.run(AutopsyArguments(
            plan: PlanArguments(origin: arguments.plan.origin, destination: arguments.plan.destination,
                                budgetMinutes: arguments.plan.budgetMinutes, router: .recorded(directory),
                                maxEvaluations: arguments.plan.maxEvaluations),
            terms: replayTerms, fixture: nil))
        try Data((replay.joined(separator: "\n") + "\n").utf8)
            .write(to: directory.appendingPathComponent(autopsyFileName))
        let count = names.count + (replayTerms == nil ? 0 : 1) + 2
        return replay + ["FIXTURE \(directory.path) files=\(count) verdict=negative"]
    }

    /// Spelled by hand, keys in a fixed order, so the bytes are the same on every box.
    static func fixtureJSON(_ arguments: AutopsyArguments, plan: ScenicPlan, terms: Bool) -> String {
        var ids: [Int] = []
        for row in plan.table.rows {
            if let id = row.wayId, ids.last != id { ids.append(id) }
        }
        let o = arguments.plan.origin
        let d = arguments.plan.destination
        return "{\n  \"verdict\": \"negative\",\n"
            + "  \"origin\": \"\(o.latitude),\(o.longitude)\",\n"
            + "  \"destination\": \"\(d.latitude),\(d.longitude)\",\n"
            + "  \"budgetMinutes\": \(arguments.plan.budgetMinutes),\n"
            + "  \"lambda\": \"\(LambdaCustomModel.multiplier(plan.outcome.lambda))\",\n"
            + "  \"terms\": " + (terms ? "\"\(termsFileName)\"" : "null") + ",\n"
            + "  \"wayIds\": [" + ids.map(String.init).joined(separator: ", ") + "]\n}\n"
    }
}
