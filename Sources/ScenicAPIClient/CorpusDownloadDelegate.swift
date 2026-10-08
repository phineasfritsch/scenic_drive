import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// One corpus download's URLSession delegate (T-0305 R3): it appends the body to the resume file as it arrives and
/// finishes with the byte count on disk, or a `CorpusFetchError`.
///
/// `offset` is what the resume file held when the request was sent. A 200 rewrites the file from byte 0 (a server
/// that ignored the Range header sends the whole body); a 206 is accepted only when a Range was sent and its
/// Content-Range starts at `offset`; any other status, and a body past `expected`, cancel the task. A delegate, not
/// a completion handler, so the body streams to disk instead of being held in memory. Every member is touched only
/// from the session's serial delegate queue, after `run` has stored the continuation under `lock`.
final class CorpusDownloadDelegate: NSObject, URLSessionDataDelegate, @unchecked Sendable {
    private let file: URL
    private let offset: Int
    private let expected: Int
    private let onProgress: @Sendable (Int, Int) -> Void
    private let lock = NSLock()
    private var handle: FileHandle?
    private var onDisk: Int
    private var failure: CorpusFetchError?
    private var continuation: CheckedContinuation<Int, any Error>?

    init(file: URL, offset: Int, expected: Int, onProgress: @escaping @Sendable (Int, Int) -> Void) {
        self.file = file
        self.offset = offset
        self.expected = expected
        self.onProgress = onProgress
        self.onDisk = offset
    }

    /// Sends `request` through `session` and returns the bytes on disk when the body ended cleanly.
    func run(_ request: URLRequest, in session: URLSession) async throws -> Int {
        try await withCheckedThrowingContinuation { continuation in
            lock.lock()
            self.continuation = continuation
            lock.unlock()
            session.dataTask(with: request).resume()
        }
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive response: URLResponse,
                    completionHandler: @escaping @Sendable (URLSession.ResponseDisposition) -> Void) {
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        let range = (response as? HTTPURLResponse)?.value(forHTTPHeaderField: "Content-Range") ?? ""
        do {
            let handle = try FileHandle(forWritingTo: file)
            self.handle = handle
            if status == 200 {
                try handle.truncate(atOffset: 0)
                onDisk = 0
            } else if status == 206, offset > 0, range.hasPrefix("bytes \(offset)-") {
                try handle.seekToEnd()
            } else {
                failure = .status(status)
                completionHandler(.cancel)
                return
            }
        } catch {
            failure = .transport(code: URLError.Code.cannotWriteToFile.rawValue)
            completionHandler(.cancel)
            return
        }
        completionHandler(.allow)
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        guard failure == nil, let handle else { return }
        guard onDisk + data.count <= expected else {
            failure = .longBody(expected: expected)
            dataTask.cancel()
            return
        }
        do {
            try handle.write(contentsOf: data)
            onDisk += data.count
            onProgress(onDisk, expected)
        } catch {
            failure = .transport(code: URLError.Code.cannotWriteToFile.rawValue)
            dataTask.cancel()
        }
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: (any Error)?) {
        try? handle?.close()
        handle = nil
        lock.lock()
        let continuation = self.continuation
        self.continuation = nil
        lock.unlock()
        if let failure {
            continuation?.resume(throwing: failure)
        } else if let error {
            continuation?.resume(throwing: CorpusFetchError.transport(code: (error as? URLError)?.code.rawValue ?? -1))
        } else {
            continuation?.resume(returning: onDisk)
        }
    }
}
