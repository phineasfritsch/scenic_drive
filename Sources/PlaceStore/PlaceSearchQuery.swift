#if canImport(GRDB)
/// Turns what a user typed into an FTS5 MATCH expression that can never be FTS5 syntax (T-0254 ruling R6).
///
/// The string is split into maximal runs of token characters - Unicode letters, numbers, private-use and
/// non-spacing marks, which is unicode61's token class plus the marks remove_diacritics folds - and every
/// other scalar is a separator. A run with no letter, number or private-use scalar is dropped. Each run is
/// emitted as a quoted string with a prefix star, `"run"*`, and the runs are ANDed by juxtaposition (R5:
/// every token is a prefix, for type-ahead). A run cannot contain `"`, so quotes, NEAR, AND/OR/NOT, `*`,
/// `^`, `:`, `-`, `+` and parentheses are either separators or quoted barewords.
enum PlaceSearchQuery {
    /// The MATCH expression, or nil when the input has no token at all.
    static func match(for query: String) -> String? {
        var runs: [String] = []
        var current = String.UnicodeScalarView()
        var hasBase = false
        func flush() {
            if hasBase { runs.append("\"" + String(current) + "\"*") }
            current = String.UnicodeScalarView()
            hasBase = false
        }
        for scalar in query.unicodeScalars {
            switch scalar.properties.generalCategory {
            case .uppercaseLetter, .lowercaseLetter, .titlecaseLetter, .modifierLetter, .otherLetter,
                 .decimalNumber, .letterNumber, .otherNumber, .privateUse:
                current.append(scalar)
                hasBase = true
            case .nonspacingMark:
                current.append(scalar)
            default:
                flush()
            }
        }
        flush()
        return runs.isEmpty ? nil : runs.joined(separator: " ")
    }
}
#endif
