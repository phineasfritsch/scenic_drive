/// The Worker's failure body: `{"error": code}` plus `resets_at` on 429 and `detail` on 400/502 (plan.ts).
struct PlanFailureBody: Decodable, Equatable {
    let error: String
    let resetsAt: String?
    let detail: String?

    enum CodingKeys: String, CodingKey {
        case error
        case resetsAt = "resets_at"
        case detail
    }
}
