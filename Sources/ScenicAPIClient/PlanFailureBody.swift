/// The Worker's failure body: `{"error": code}` plus `resets_at` on 429 and `detail` on 400/502 (plan.ts).
struct PlanFailureBody: Decodable, Equatable {
    let error: String
    let resetsAt: String?
    let detail: String?
    /// T-0332: the offers of a 422 `nothing_pretty`, or nil when the body carries none this client can stand behind.
    /// Read on its own, so a malformed offer never costs the rest of the body its reading.
    var nothingPretty: NothingPrettyOffer? = nil

    enum CodingKeys: String, CodingKey {
        case error
        case resetsAt = "resets_at"
        case detail
    }
}

extension PlanFailureBody {
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        error = try container.decode(String.self, forKey: .error)
        resetsAt = try container.decodeIfPresent(String.self, forKey: .resetsAt)
        detail = try container.decodeIfPresent(String.self, forKey: .detail)
        nothingPretty = try? NothingPrettyOffer(from: decoder)
    }
}
