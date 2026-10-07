/// What `CorpusUpdater.openForLaunch(isColdLaunch:)` did with a pending corpus (T-0300 O7).
public enum CorpusActivation: Equatable, Sendable {
    /// No pending corpus: the active one is opened as it is.
    case noPending
    /// A warm resume: the pending corpus waits for the next cold launch.
    case deferredWarmLaunch
    /// A drive holds the store: the pending corpus waits.
    case deferredDriveHeld
    /// The pending corpus passed the validator and is now the active one.
    case activated
    /// The pending corpus failed the validator: the swap was undone, the old corpus kept, the pending one deleted.
    case rejected
}
