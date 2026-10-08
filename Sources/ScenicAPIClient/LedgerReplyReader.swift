import Foundation
import ScenicKit

/// T-0307 R4: every /ledger reply -> exactly one `LedgerOutcome`, by status, then by body where the status alone
/// does not decide. Pure: no reply is ever re-requested from here.
enum LedgerReplyReader {
    private struct Recorded: Decodable {
        let recorded: Bool
    }

    private struct Places: Decodable {
        struct Row: Decodable {
            let place_id: String
            let cell: String
            let day: String
        }

        let places: [Row]
    }

    private struct Failure: Decodable {
        let error: String
    }

    static func read(_ reply: PlanHTTPReply, isRead: Bool) -> LedgerOutcome {
        switch reply.status {
        case 200: return isRead ? places(reply.body) : recorded(reply.body)
        case 400: return .invalidRequest
        case 401: return .unauthorized
        case 405: return .methodRefused
        case 429:
            let error = try? JSONDecoder().decode(Failure.self, from: reply.body).error
            return error == "ledger_daily_cap" ? .dailyCap : .unexpected(429)
        case 503: return .unavailable
        default: return .unexpected(reply.status)
        }
    }

    private static func recorded(_ body: Data) -> LedgerOutcome {
        (try? JSONDecoder().decode(Recorded.self, from: body))?.recorded == true ? .recorded : .unreadable
    }

    private static func places(_ body: Data) -> LedgerOutcome {
        guard let decoded = try? JSONDecoder().decode(Places.self, from: body) else { return .unreadable }
        var rows: [LedgerRow] = []
        for row in decoded.places {
            guard let day = civilDate(row.day) else { return .unreadable }
            rows.append(LedgerRow(placeId: row.place_id, cell: row.cell, day: day))
        }
        return .places(rows)
    }

    /// `YYYY-MM-DD` (the Worker's `toISOString().slice(0, 10)`) naming a real Gregorian day, or nil.
    static func civilDate(_ text: String) -> CivilDate? {
        let b = Array(text.utf8)
        guard b.count == 10, b[4] == 45, b[7] == 45 else { return nil }
        let fields = [b[0..<4], b[5..<7], b[8..<10]]
        guard fields.allSatisfy({ $0.allSatisfy { (48...57).contains($0) } }) else { return nil }
        let n = fields.map { $0.reduce(0) { $0 * 10 + Int($1 - 48) } }
        let (year, month, day) = (n[0], n[1], n[2])
        guard (1...12).contains(month) else { return nil }
        let leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)
        let lengths = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        guard (1...lengths[month - 1]).contains(day) else { return nil }
        return CivilDate(year: year, month: month, day: day)
    }
}
