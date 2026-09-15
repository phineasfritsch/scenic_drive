import Foundation
import Testing
@testable import ScenicKit

/// What the search does when it cannot answer honestly, and the sentence it produces when it refuses.
///
/// Split out of `LambdaSearchBudgetUseTests` at the 300-line cap, along the section boundary that suite
/// already had - it asks whether the budget is spent, this asks what happens when there is nothing to spend
/// it on. Cutting at a line number would have left half of one argument in each file.
///
/// A type-only assertion is satisfied by ANY refusal: dropping `isFinite` from the router guard turns an
/// infinite duration into a `noFeasibleLambda` reading "the shortest seen was inf s" - a different refusal,
/// a different sentence in the log, and the same type. So wherever a refusal carries a value, the test here
/// pattern-matches the case and its payload.
///
/// THREE tests are deliberately type-only, and this is the exact extent of it. That count read "two" while
/// the same paragraph went on to name the third (N-SG3) - in a header rewritten to fix a false sentence
/// about exactly this, which is how a count gets copied instead of recounted. `noFeasibleLambdaThrows` and
/// `refusesBadInputs` pin "refused rather than returned" across many inputs, cheaply, and neither is the
/// only assertion on its case: the payloads of `noFeasibleLambda` are pinned by
/// `refusalCarriesWhatTheSearchMeasured`, and those of `notADuration` and `notABudget` by
/// `errorsCarryTheirNumbers`. `propagatesRouterErrors` is the third, and it is type-only on purpose: what
/// it pins is that a non-BudgetError comes back out unchanged, which is a statement about the type.
///
/// What a type-only family is still worth exactly as much as is its list of INPUTS, which is how F-R1 hid
/// here for three rounds. `refusesBadInputs` carried (.nan, 60), (1800, .nan) and (1800, .infinity) and not
/// (.infinity, 60), so the `fastest.isFinite` half of the constructor guard had no witness in the family and
/// no payload assertion either: `errorsCarryTheirNumbers` pins `notADuration(-1)`, and -1 is a value
/// `fastest > 0` refuses on its own. A guard with two halves needs a value the halves DISAGREE about;
/// `infiniteFastestIsRefusedAsNotADuration` is that value, and `routerGuardBoundaryIsExactlyZero` is the
/// same repair on the router-side guard, whose threshold was bracketed in (-1, 0] and not pinned.
@Suite("Lambda search - refusals and the sentences they produce")
struct LambdaSearchRefusalTests {

    static let fastest: TimeInterval = 1800
    static let budget: TimeInterval = 1500

    @Test("a router that overshoots even at lambda zero is refused, not rounded down to a breach")
    func noFeasibleLambdaThrows() throws {
        let search = try LambdaSearch(fastest: Self.fastest, budget: 60)
        #expect(throws: BudgetError.self) {
            _ = try search.search { _ in Self.fastest + 99_999 }
        }
    }

    @Test("the refusal carries the ceiling, the shortest route seen, and what it cost to find out")
    func refusalCarriesWhatTheSearchMeasured() throws {
        // F-B. `noFeasibleLambda` is the only BudgetError whose payload the search COMPUTES instead of
        // echoing back a caller's input, and it was the only one with no payload assertion anywhere:
        // `errorsDescribeThemselves` hand-builds the case from literals, so it pins the format string and
        // nothing about what the search puts into it, and `noFeasibleLambdaThrows` is type-only. Three
        // different wrong sentences reached the log with the suite green - the longest route seen reported
        // as the shortest, a zero ceiling, and zero evaluations.
        //
        // Derived by hand: fastest 1800 + budget 60 = an 1860 s ceiling, nothing here fits under it, so
        // `best` stays nil and the bracket halves downward every pass - 0 -> 5000, 4 -> 9000, 2 -> 4000,
        // 1 -> 6000, 0.5 -> 7000, 0.25 -> 8000, stopping on the cap of 6. The shortest of the six is the
        // THIRD measured: not the first, not the last, not the largest, so `min()` written as `first`,
        // `last` or `max` each reads back a different number. A fixture whose seed happened to be the
        // minimum - which is what this one was first - lets two of those through.
        let search = try LambdaSearch(fastest: Self.fastest, budget: 60)
        let nothingFits: (Double) -> TimeInterval = { lambda in
            switch lambda {
            case 0:       return 5000
            case ..<0.4:  return 8000
            case ..<0.75: return 7000
            case ..<1.5:  return 6000
            case ..<3:    return 4000
            default:      return 9000
            }
        }
        do {
            _ = try search.search(nothingFits)
            Issue.record("nothing was feasible, so the search must refuse rather than return")
        } catch let e as BudgetError {
            guard case let .noFeasibleLambda(ceiling, best, evaluations) = e else {
                Issue.record("wrong case: \(e)"); return
            }
            #expect(ceiling == 1860, "the ceiling it was actually measured against")
            #expect(best == 4000, "the SHORTEST duration seen - not the longest, and not infinity")
            #expect(evaluations == 6, "six router requests were spent finding this out")
            #expect(String(describing: e)
                    == "no lambda produced a route within the 1860.0 s ceiling in 6 evaluations; "
                    + "the shortest seen was 4000.0 s")
        }
    }

    @Test("nonsense from the router is refused AS nonsense, naming the value and the lambda",
          arguments: [TimeInterval.nan, .infinity, -1, -0.2])
    func refusesNonsense(bad: TimeInterval) throws {
        // This was `#expect(throws: BudgetError.self)`, which any BudgetError satisfies - and dropping
        // `isFinite` from the guard produces one: an infinite duration sails past, is never feasible, and
        // the search ends in `noFeasibleLambda` reporting "the shortest seen was inf s". Same type, wrong
        // refusal. My own mutation, not a reviewer's; the standalone control put 154 changed cases on it.
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
        do {
            _ = try search.search { _ in bad }
            Issue.record("\(bad) is not a duration and must be refused")
        } catch let e as BudgetError {
            guard case let .routerReturnedNonsense(lambda, duration) = e else {
                Issue.record("wrong case for \(bad): \(e)"); return
            }
            #expect(lambda == 0, "the seed is where the router first answered")
            #expect(duration.isNaN == bad.isNaN)
            if !bad.isNaN { #expect(duration == bad) }
        }
    }

    @Test("a duration of exactly zero is a number the router is allowed to return")
    func zeroIsADurationNotNonsense() throws {
        // F-I. `refusesNonsense` covers .nan, .infinity and -1, so the guard's boundary - `d >= 0` - had
        // witnesses only on the far side. Tightening it to `d > 0` turns a legal answer into a refusal,
        // and nothing objected. Zero is feasible under every ceiling, so the flat-curve tie-break applies
        // and the winner is the last lambda the bisection reaches: 0, 4, 6, 7, 7.5, 7.75.
        //
        // This is ONE SIDE of that boundary and was written as though it were both: with -1 illegal and 0
        // legal the threshold is only constrained to (-1, 0], and `d >= -0.5` survived. The other side is
        // `routerGuardBoundaryIsExactlyZero`; what this test still owns is the winning lambda.
        let out = try LambdaSearch(fastest: Self.fastest, budget: Self.budget).search { _ in 0 }
        #expect(out.duration == 0)
        #expect(out.lambda == 7.75)
    }

    @Test("the router guard's boundary is exactly zero, to the last bit a Double has")
    func routerGuardBoundaryIsExactlyZero() throws {
        // F-R2. `refusesNonsense` pins -1 as illegal and the test above pins 0 as legal, which BRACKETS the
        // threshold in (-1, 0] and pins nothing inside it: `d >= -0.5` survived all 46 tests, and a router
        // answering -0.2 s then reached the caller as a route, with `usedBudget == true` and an `extraTime`
        // of -1800.2 s. Exactly the defect F3 was filed for - "pinned the interval (0.4, 0.55], which holds
        // for any threshold in that range" - in the sibling guard, while the comment above claimed the
        // boundary was pinned.
        //
        // The far side is therefore the LARGEST negative Double there is, not a round number: every
        // threshold `t <= -Double.leastNonzeroMagnitude` accepts it, and every `t > 0` rejects the zero
        // below, so the two assertions together admit only `t` in (-5e-324, 0] - and the only Doubles there
        // are 0 and -0, which compare identically. The boundary is pinned, not bracketed.
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
        #expect(try search.search { _ in 0 }.duration == 0, "zero seconds is a legal answer")

        let justBelowZero = -Double.leastNonzeroMagnitude
        do {
            let out = try search.search { _ in justBelowZero }
            Issue.record("a negative duration is not a route; got \(out.duration) s at lambda \(out.lambda)")
        } catch let e as BudgetError {
            guard case let .routerReturnedNonsense(lambda, duration) = e else {
                Issue.record("wrong case: \(e)"); return
            }
            #expect(lambda == 0, "the seed is where the router first answered")
            #expect(duration == justBelowZero)
        }
    }

    @Test("invalid inputs are refused at construction",
          arguments: [(TimeInterval(0), TimeInterval(60)), (-1, 60), (.nan, 60), (.infinity, 60),
                      (1800, -1), (1800, -0.5), (1800, -1e-9), (1800, .nan), (1800, .infinity)])
    func refusesBadInputs(fastest: TimeInterval, budget: TimeInterval) {
        #expect(throws: BudgetError.self) { _ = try LambdaSearch(fastest: fastest, budget: budget) }
    }

    @Test("an infinite fastest duration is refused, because it makes the ceiling vacuous rather than tight")
    func infiniteFastestIsRefusedAsNotADuration() {
        // F-R1. The `fastest.isFinite` half of the constructor guard had NO witness: this family covered
        // (.nan, 60), (1800, .nan) and (1800, .infinity), and an infinite `fastest` was the one combination
        // it omitted. NaN does not witness `isFinite` - `Double.nan > 0` is already false, so `fastest > 0`
        // refuses NaN on its own - and infinity is the only value the two halves disagree about. Dropping
        // `isFinite` was MISSED by all 46 tests, twice, and again spelled `!fastest.isNaN`.
        //
        // What it costs: `ceiling` is `fastest + budget`, so an infinite `fastest` gives an infinite ceiling
        // and EVERY duration the router returns compares `<=` against it. The product invariant - returned
        // ETA <= fastest + budget - is then not breached but VACUOUS, which is the worse failure of the two
        // and the one this repository is named after. The refusal is the behaviour; the case and the value
        // it carries are asserted, not the bare type, because `noFeasibleLambda` is a BudgetError too.
        //
        // What this guard does NOT close, recorded rather than left to be rediscovered: `fastest` and
        // `budget` can both be finite and legal and still SUM to an infinite ceiling -
        // `LambdaSearch(fastest: 1e308, budget: 1e308)` constructs, and a standalone sweep prints
        // `CTOR OK f=1e+308 b=1e+308 ceiling=inf`. Same vacuity, reached without an infinite input.
        // Refused this round rather than closed (N-SG4): 1e308 seconds is unreachable from the product, and
        // an honest refusal needs an error case of its own, since neither input is the bad one.
        do {
            _ = try LambdaSearch(fastest: .infinity, budget: 60)
            Issue.record("an infinite fastest duration must be refused at construction")
        } catch let e as BudgetError {
            guard case let .notADuration(t) = e else {
                Issue.record("wrong case: \(e)"); return
            }
            #expect(t == .infinity)
            #expect(String(describing: e)
                    == "fastest duration is not a positive finite number of seconds: inf")
        } catch {
            Issue.record("wrong error type: \(error)")
        }
    }

    @Test("the search propagates a router error rather than swallowing it")
    func propagatesRouterErrors() throws {
        struct Offline: Error {}
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
        #expect(throws: Offline.self) { _ = try search.search { _ in throw Offline() } }
    }

    @Test("every BudgetError says what happened, in a sentence with the numbers in it")
    func errorsDescribeThemselves() {
        // F4: every error assertion in this suite was type-only, so 41 lines of public API - including the
        // whole CustomStringConvertible conformance - had no behavioural coverage at all. These strings
        // reach a log and a bug report, so they are pinned as text.
        #expect(String(describing: BudgetError.notADuration(-1))
                == "fastest duration is not a positive finite number of seconds: -1.0")
        #expect(String(describing: BudgetError.notABudget(-5))
                == "budget is not a non-negative finite number of seconds: -5.0")
        #expect(String(describing: BudgetError.routerReturnedNonsense(lambda: 2.5, duration: -3))
                == "router returned -3.0 s at lambda 2.5")
        #expect(String(describing: BudgetError.noFeasibleLambda(ceiling: 3300, best: 4000, evaluations: 6))
                == "no lambda produced a route within the 3300.0 s ceiling in 6 evaluations; "
                + "the shortest seen was 4000.0 s")
    }

    @Test("the error carries the values, not just the case")
    func errorsCarryTheirNumbers() throws {
        // A typed throw whose payload is wrong is worse than an untyped one: it puts a plausible wrong number
        // in front of whoever reads it. Pinned by pattern-matching the payload, not by the case alone.
        do {
            _ = try LambdaSearch(fastest: -1, budget: Self.budget)
            Issue.record("a negative fastest duration must be refused")
        } catch let e as BudgetError {
            guard case let .notADuration(t) = e else {
                Issue.record("wrong case: \(e)"); return
            }
            #expect(t == -1)
        }

        do {
            _ = try LambdaSearch(fastest: Self.fastest, budget: -5)
            Issue.record("a negative budget must be refused")
        } catch let e as BudgetError {
            guard case let .notABudget(b) = e else {
                Issue.record("wrong case: \(e)"); return
            }
            #expect(b == -5)
        }

        do {
            _ = try LambdaSearch(fastest: Self.fastest, budget: Self.budget).search { l in
                l == 0 ? -7 : Self.fastest
            }
            Issue.record("a negative duration from the router must be refused")
        } catch let e as BudgetError {
            guard case let .routerReturnedNonsense(lambda, duration) = e else {
                Issue.record("wrong case: \(e)"); return
            }
            #expect(lambda == 0)
            #expect(duration == -7)
        }
    }
}
