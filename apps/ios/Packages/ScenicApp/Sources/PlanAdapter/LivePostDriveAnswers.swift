import ScenicKit

/// The app's post-drive answer sink (T-0358 R7): each answer the drive screen hands it becomes LiveTelemetry's
/// post_drive_answer, the only thing sent. The shell sets it in the drive's environment.
public struct LivePostDriveAnswers: PostDriveAnswering {
    public init() {}

    public func answered(prettier: Bool) {
        LiveTelemetry.postDriveAnswer(prettier: prettier)
    }
}
