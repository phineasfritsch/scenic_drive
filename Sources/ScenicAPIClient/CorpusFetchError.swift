/// Why `URLSessionCorpusFetcher` wrote no corpus (T-0305 R3). None of them leaves a file at the destination; the
/// comment on each says what happens to the resume file.
public enum CorpusFetchError: Error, Equatable, Sendable {
    /// A reply that was neither 200 nor a 206 resuming at the requested byte. The resume file is deleted.
    case status(Int)
    /// The body ended before the manifest's byte count. The resume file is kept: the next fetch asks for the rest.
    case shortBody(received: Int, expected: Int)
    /// The body ran past the manifest's byte count. The resume file is deleted.
    case longBody(expected: Int)
    /// No reply, or the connection dropped mid-body (the URLError code). The resume file is kept.
    case transport(code: Int)
}
