import SwiftUI

/// The largest text size the home's chrome and sheet draw at (T-0378 R2), and the shell's Plan pill with them
/// (T-0384 R1/R2): the one binding of the cap, read by `ScenicHomeScreen` and by the app shell.
public enum HomeTypeSize {
    public static let cap = DynamicTypeSize.xxxLarge
}
