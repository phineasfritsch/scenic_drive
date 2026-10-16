import Foundation

/// "Prettier than your usual way?" at the next open after a handoff (T-0366 R2/R4): the whole decision, so the home
/// only calls `opened` on each foreground open and shows the card when it answers true.
///
/// A handoff leaves `opensAfterHandoff` opens. An open with none left reads no fix and writes nothing. Otherwise one
/// fix is read; the full surface asks (PostDriveQuestion's handedOff/appOpened row) and spends the marker at the ask;
/// any other open spends one. The marker is re-read after the fix, so two overlapping opens ask at most once.
public enum PostDriveNextOpen {
    public static let opensAfterHandoff = 3

    /// A stored value clamped to 0...opensAfterHandoff.
    static func pending(_ stored: Int) -> Int {
        min(max(stored, 0), opensAfterHandoff)
    }

    @MainActor
    public static func opened(marker: any HandoffMarkerStoring, fix: any OpenFixReading) async -> Bool {
        guard pending(marker.opensLeft()) > 0 else { return false }
        let surface = await fix.read()?.surface ?? .minimal
        let left = pending(marker.opensLeft())
        guard left > 0 else { return false }
        let asks = PostDriveQuestion.asks(outcome: .handedOff, moment: .appOpened, surface: surface, alreadyAsked: false)
        marker.setOpensLeft(asks ? 0 : left - 1)
        return asks
    }
}
