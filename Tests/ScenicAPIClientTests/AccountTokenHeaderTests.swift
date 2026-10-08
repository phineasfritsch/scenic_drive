import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0315 R1, R2, R5: every plan-family request carries the install id and, exactly when the device holds one, the
/// purchase's appAccountToken as `x-scenic-account-token` - compared as the WHOLE request against literals, so the
/// absence of `authorization` (R1: no session JWT on these requests) is part of every row. Live and expired purchases
/// are both a token on the device; the Worker tells them apart, and the trip the client returns is the Worker's
/// answer whatever token was sent.
@Suite("AccountTokenHeaderTests")
struct AccountTokenHeaderTests {
    enum Purchase: String, CaseIterable, Sendable {
        case noProvider, noPurchase, live, expired
    }

    enum Answer: String, CaseIterable, Sendable {
        case preview, full
    }

    /// Written UPPERCASE, as Foundation's uuidString prints them; the headers below are the lowercased forms.
    static let liveToken = "0E6B9A4C-5F1D-4C2B-9A8E-3D7F1B2C4A5E"
    static let expiredToken = "A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D"

    static func provider(_ purchase: Purchase) -> FixedAccountToken? {
        switch purchase {
        case .noProvider: return nil
        case .noPurchase: return FixedAccountToken(nil)
        case .live: return FixedAccountToken(liveToken)
        case .expired: return FixedAccountToken(expiredToken)
        }
    }

    /// The whole header set each purchase must produce, as literals.
    static func headers(_ purchase: Purchase) -> [String: String] {
        switch purchase {
        case .noProvider, .noPurchase:
            return ["content-type": "application/json", "x-scenic-device": "6f9619ff-8b86-4d01-b42d-00c04fc964ff"]
        case .live:
            return ["content-type": "application/json", "x-scenic-device": "6f9619ff-8b86-4d01-b42d-00c04fc964ff",
                    "x-scenic-account-token": "0e6b9a4c-5f1d-4c2b-9a8e-3d7f1b2c4a5e"]
        case .expired:
            return ["content-type": "application/json", "x-scenic-device": "6f9619ff-8b86-4d01-b42d-00c04fc964ff",
                    "x-scenic-account-token": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"]
        }
    }

    static let planBody =
        #"{"budget_minutes":25,"destination":{"place":"42"},"origin":{"lat":34.02,"lon":-118.49},"vehicle":"standard"}"#
    static let loopBody = #"{"minutes":45,"start":{"lat":34.02,"lon":-118.49},"vehicle":"standard"}"#
    static let tripBody =
        #"{"days":2,"destination":{"place":"42"},"extra_budget_pct":40,"origin":{"lat":34.02,"lon":-118.49},"vehicle":"standard"}"#

    @Test("every plan request carries exactly the device and the purchase's account token",
          arguments: Purchase.allCases)
    func planRequest(_ purchase: Purchase) async {
        let fake = CountingPlanTransport(reply: PlanHTTPReply(status: 200, body: Data()))
        _ = await PlanWire.plan(through: fake, account: Self.provider(purchase))
        let expected = PlanHTTPRequest(url: URL(string: "https://scenic-api.test/plan")!, method: "POST",
                                       headers: Self.headers(purchase), body: Data(Self.planBody.utf8))
        #expect(await fake.requests == [expected])
    }

    @Test("every trip request carries exactly the device and the account token, and the itinerary is the Worker's",
          arguments: Purchase.allCases, Answer.allCases)
    func tripRequest(_ purchase: Purchase, _ answer: Answer) async {
        let body = answer == .preview ? TripWire.previewBody : TripWire.fullBody
        let fake = CountingPlanTransport(reply: TripWire.reply(200, body))
        let outcome = await TripWire.trip(through: fake, account: Self.provider(purchase))
        #expect(outcome == .success(answer == .preview ? TripWire.preview : TripWire.full))
        let expected = PlanHTTPRequest(url: URL(string: "https://scenic-api.test/trip")!, method: "POST",
                                       headers: Self.headers(purchase), body: Data(Self.tripBody.utf8))
        #expect(await fake.requests == [expected])
    }

    @Test("every loop request carries exactly the device and the account token, and the loop is the Worker's",
          arguments: Purchase.allCases)
    func loopRequest(_ purchase: Purchase) async {
        let fake = CountingPlanTransport(reply: LoopWire.reply(200, LoopWire.squareBody))
        let outcome = await LoopWire.loop(through: fake, account: Self.provider(purchase))
        #expect(outcome == .success(LoopWire.response()))
        let expected = PlanHTTPRequest(url: URL(string: "https://scenic-api.test/loop")!, method: "POST",
                                       headers: Self.headers(purchase), body: Data(Self.loopBody.utf8))
        #expect(await fake.requests == [expected])
    }

    @Test("a request refused on the device reads no account token and sends nothing")
    func refusalReadsNothing() async {
        let token = FixedAccountToken(Self.liveToken)
        let fake = CountingPlanTransport(reply: TripWire.reply(200, TripWire.fullBody))
        let trip = await TripWire.trip(through: fake, days: 0, account: token)
        let plan = await PlanWire.plan(through: fake, from: Coordinate(latitude: 34.021, longitude: -118.49),
                                       account: token)
        let loop = await LoopWire.loop(through: fake, minutes: 0, account: token)
        #expect(trip == .failure(.refusedOnDevice(.daysOutOfRange)))
        #expect(loop == .failure(.refusedOnDevice(.minutesOutOfRange)))
        #expect(PlanWire.error(plan) == .refusedOnDevice(.originMoreThanTwoDecimals))
        #expect(await fake.count == 0)
        #expect(await token.reads == 0)
    }

    @Test("the table's rows are functions of the purchase: each token is its own header, no token none")
    func rowsFollowThePurchase() {
        let sets = Purchase.allCases.map(Self.headers)
        #expect(Set(sets).count == 3)
        #expect(Self.headers(.noProvider) == Self.headers(.noPurchase))
        #expect(Purchase.allCases.allSatisfy { Self.headers($0)["authorization"] == nil })
        #expect(Self.headers(.live)["x-scenic-account-token"] == Self.liveToken.lowercased())
        #expect(Self.headers(.expired)["x-scenic-account-token"] == Self.expiredToken.lowercased())
    }
}
