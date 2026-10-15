import Foundation
import ScenicAPIClient

/// A test's device: records every item it is asked to erase, in order (T-0356 R3).
actor RecordingEraser: LocalAccountEraser {
    private(set) var erased: [LocalAccountItem] = []

    func erase(_ item: LocalAccountItem) async {
        erased.append(item)
    }
}
