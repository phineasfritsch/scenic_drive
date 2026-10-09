import SwiftUI

/// A plan card's last control, pinned in the card's bottom safe-area inset (T-0346): SwiftUI lays a bottom inset out
/// above the sheet's bottom bar, so the control is on screen and tappable at rest at every Dynamic Type size, and the
/// card's scrolling content gains the same bottom inset, so nothing it scrolls can end under the bar either.
struct PlanCardExit: View {
    let title: String
    let action: () -> Void

    init(_ title: String, action: @escaping () -> Void) {
        self.title = title
        self.action = action
    }

    var body: some View {
        Button(title, action: action)
            .font(.body)
            .multilineTextAlignment(.center)
            .frame(maxWidth: .infinity, minHeight: 44)
            .padding(.vertical, 4)
            .background(.bar)
    }
}
