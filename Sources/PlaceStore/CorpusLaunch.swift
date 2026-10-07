import Foundation

/// What `LaunchCorpus.open(updater:fallback:)` did at a cold launch (T-0305 R4): the activation T-0300's
/// `openForLaunch` reported, and the corpus file the app's searches open - the active slot when that file exists,
/// else the bundled fallback (nil when there is neither).
public struct CorpusLaunch: Equatable, Sendable {
    public let activation: CorpusActivation
    public let corpus: URL?

    public init(activation: CorpusActivation, corpus: URL?) {
        self.activation = activation
        self.corpus = corpus
    }
}
