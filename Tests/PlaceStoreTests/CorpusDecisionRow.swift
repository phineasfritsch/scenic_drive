import Foundation
import PlaceStore

/// One row of the OTA decision table (T-0300 O2/O8): the manifest bytes the app fetched, the app's build, the
/// active corpus's version, and the WHOLE answer `CorpusUpdater.decide` must give - a decision or a typed error.
struct CorpusDecisionRow {
    let name: String
    let json: Data
    let appBuild: Int
    let activeVersion: String?
    let expected: Result<CorpusUpdateDecision, CorpusUpdateError>
}
