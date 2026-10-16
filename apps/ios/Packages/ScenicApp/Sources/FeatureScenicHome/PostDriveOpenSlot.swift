import ScenicKit
import SwiftUI

/// The home sheet's place for the next-open question (T-0366 R5): PostDriveCard while the shell's PostDriveOpenModel
/// is asking, and no view at all otherwise - so the sheet's stack spends no spacing on it and the home is unchanged.
/// Not a modal. With no model in the environment it is never anything.
struct PostDriveOpenSlot: View {
    @Environment(PostDriveOpenModel.self) private var model: PostDriveOpenModel?

    var body: some View {
        if let model, model.isAsking {
            PostDriveCard(onAnswer: { model.answered($0) })
        }
    }
}
