import Foundation
import ScenicKit

// `ops/plan <O> <D> <B>` - the plan's M3 exit, and the only way to drive this engine without a phone.
//
// The whole of it: parse, route, plan, print. The bisection is ScenicKit's, the scoring is ScenicKit's,
// the URL is Handoff's, and nothing is reimplemented here - a second copy of any of them is a copy that
// drifts and then disagrees with the app the owner is actually driving.
//
// Exit codes, because this is run from scripts and read by people:
//   0  a plan
//   2  the arguments are wrong (the usage line is printed)
//   3  the engine refused to call it a plan (the ceiling, or the route is the fastest route)
//   4  the router could not be reached or answered something unreadable

func fail(_ message: String, _ code: Int32) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(code)
}

let rawArguments = Array(CommandLine.arguments.dropFirst())

// `ops/plan --emit-model <lambda>` prints the exact per-request custom model this tool would send at that
// lambda, and nothing else. It exists because the model is the request: it is how a recording off a real
// graph is made with the bytes the engine would have sent, and how somebody reading a bad route finds out
// what was actually asked for. It is the Worker's model, byte for byte (Tests/Fixtures/custom-model).
if rawArguments.first == "--emit-model" {
    guard rawArguments.count == 2, let lambda = Double(rawArguments[1]) else {
        fail("ops/plan: --emit-model takes one lambda in [0, 8]", 2)
    }
    do {
        print(try LambdaCustomModel.json(for: lambda))
        exit(0)
    } catch {
        fail("ops/plan: \(error)", 3)
    }
}

// `ops/plan --menu <O> <D> [--max N] --recorded <dir>` prints the time-versus-fun menu for one trip
// (T-0239): MenuCommand.run, with main.swift's exit codes.
if rawArguments.first == "--menu" {
    do {
        let menuArguments = try MenuArguments.parse(Array(rawArguments.dropFirst()))
        for line in try MenuCommand.run(menuArguments) { print(line) }
        exit(0)
    } catch let failure as PlanArguments.Failure {
        fail("ops/plan: \(failure)\n\(MenuArguments.usage)", 2)
    } catch let failure as PlanFailure {
        fail("ops/plan REFUSED: \(failure)", 3)
    } catch {
        fail("ops/plan: \(error)", 4)
    }
}

let arguments: PlanArguments
do {
    arguments = try PlanArguments.parse(rawArguments)
} catch let failure as PlanArguments.Failure {
    fail("ops/plan: \(failure)\n\(PlanArguments.usage)", 2)
} catch {
    fail("ops/plan: \(error)\n\(PlanArguments.usage)", 2)
}

do {
    // The run itself is PlanCommand.run - a function a test can call with the arguments a person types.
    // This file is only what a process can do and a test cannot enter: printing and exit codes.
    for line in try PlanCommand.run(arguments) { print(line) }
} catch let failure as PlanFailure {
    // Not a crash and not a plan. The engine looked at what the router returned and refused to print a
    // drive it cannot stand behind, which is the product state the plan calls honest failure.
    fail("ops/plan REFUSED: \(failure)", 3)
} catch {
    fail("ops/plan: \(error)", 4)
}
