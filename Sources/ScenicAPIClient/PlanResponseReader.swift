import Foundation

/// Reads one Worker reply into a plan or a `PlanError` - the T-0251 R6 table, row for row.
///
/// Matched on the EXACT (status, body `error`) pair the Worker's plan.ts and index.ts emit. A known code at a
/// status the Worker never pairs it with is not trusted: it falls to the two closing rows, any 5xx ->
/// routingOffline (the Worker rethrew, or Cloudflare answered for it) and anything else -> unexpectedResponse.
enum PlanResponseReader {
    static func read(_ reply: PlanHTTPReply) -> Result<PlanResponse, PlanError> {
        .failure(.unexpectedResponse(status: reply.status))
    }
}
