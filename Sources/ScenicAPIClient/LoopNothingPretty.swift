import Foundation

/// What /loop's 422 `nothing_pretty` carries (T-0335 R3, T-0337 R1): the request's own minutes, echoed by
/// services/api/src/loop.ts when every clean loop of the day's three seeds scored below RouteScore's 0.45.
///
/// Read fail-closed, as `NothingPrettyOffer` is: the key present, a JSON number that is finite, whole and inside the
/// Worker's whitelist (loopRequest.ts). The Worker accepts a fractional minute, but this client only ever sends whole
/// ones (LoopRequestBody), so a fraction answers no request it made. Anything else is `unexpectedResponse`.
public struct LoopNothingPretty: Equatable, Sendable, Decodable {
    /// loopRequest.ts MIN_LOOP_MINUTES...MAX_LOOP_MINUTES.
    public static let minuteRange = 10...180

    public let minutes: Int

    public init(minutes: Int) {
        self.minutes = minutes
    }

    enum CodingKeys: String, CodingKey {
        case minutes
    }

    struct Refused: Error {}

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let minutes = try container.decode(Double.self, forKey: .minutes)
        guard minutes.isFinite, minutes == minutes.rounded(), minutes >= Double(Self.minuteRange.lowerBound),
              minutes <= Double(Self.minuteRange.upperBound) else { throw Refused() }
        self.init(minutes: Int(minutes))
    }
}
