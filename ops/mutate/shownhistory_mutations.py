"""The mutation population for T-0312: the Surprise card's basis/history split (Sources/ScenicKit/Surprise/
SurpriseCardHistory.swift) and the stored day with its retention bound (SurpriseShownDay.swift), plus the pick's
own 90-day block in Surprise.swift, which the retention bound must agree with. Driver shownhistory.py, runner
shownhistory_run.py (session.py's three-file shape).

  * THE SPLIT (1-10): showing moves the basis, declining or starting over keeps the old basis, starting over keeps
    the feedback, a restore puts the in-memory recordings into the basis or drops the stored entries from it or
    loses the feedback, the union's order and its (place, day) key;
  * THE DAY (11-17): the epoch, the era offset, the month shift, the year carry, the day's +1, the century rule,
    the retention bound;
  * THE PICK'S BLOCK (18-20): the window's bound, the block switched off - with 16, the three PRE-REVIEW
    HOLD-BACKS: MISSED before their rows landed (T-0312 Log), CAUGHT after.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

KIT = ROOT / "Sources" / "ScenicKit" / "Surprise"
CARD = KIT / "SurpriseCardHistory.swift"
DAY = KIT / "SurpriseShownDay.swift"
PICK = KIT / "Surprise.swift"
SUBJECTS = (CARD, DAY)
MUTATED_FILES = (CARD, DAY, PICK)

TESTS = ROOT / "Tests" / "ScenicKitTests" / "Surprise"
TEST_FILES = (TESTS / "SurpriseCardHistoryTests.swift", TESTS / "SurpriseShownDayTests.swift")

TABLE = "Every operation over every starting state is its recomputed history and basis, whole"
REPICK = "Recording the place on the card never moves the pick; recording into the basis would"
KNOWN = "A known calendar date is its hand-counted day number, and that number is the date"
OLDEST = "The oldest kept day on 2026-10-07 is 89 days back: 2026-07-10"
SWEEP = "Every day from 1600 to 2400 is a valid calendar date that numbers back to itself"
RETAIN = "The pick blocks a place shown on the oldest kept day and not one shown the day before"

DECLINE = "history.feedback + [feedback])\n        return SurpriseCardHistory(history: next, basis: next)"
START = "let next = SurpriseHistory(shown: history.shown)\n        return SurpriseCardHistory(history: next, basis: next)"
BLOCK = "$0.candidateId == c.id && days(date, since: $0.date) < shownDays"

MUTATIONS = [
    ("1 showing moves the basis", CARD, "return SurpriseCardHistory(history: next, basis: basis)",
     "return SurpriseCardHistory(history: next, basis: next)", [TABLE, REPICK]),
    ("2 declining keeps the old basis", CARD, DECLINE, DECLINE.replace("basis: next", "basis: basis"), [TABLE]),
    ("3 starting over keeps the old basis", CARD, START, START.replace("basis: next", "basis: basis"), [TABLE]),
    ("4 starting over keeps the feedback", CARD, START,
     START.replace("shown: history.shown)", "shown: history.shown, feedback: history.feedback)"), [TABLE]),
    ("5 a restore puts the in-memory recordings into the basis", CARD, "Self.union(stored, basis.shown)",
     "Self.union(stored, history.shown)", [TABLE]),
    ("6 a restore leaves the stored entries out of the basis", CARD,
     "basis: SurpriseHistory(shown: Self.union(stored, basis.shown)", "basis: SurpriseHistory(shown: basis.shown",
     [TABLE]),
    ("7 a restore loses the feedback", CARD, "Self.union(stored, history.shown), feedback: history.feedback)",
     "Self.union(stored, history.shown))", [TABLE]),
    ("8 the union puts memory first", CARD, "for entry in first + then", "for entry in then + first", [TABLE]),
    ("9 the union's key ignores the day", CARD, "$0.candidateId == entry.candidateId && $0.date == entry.date",
     "$0.candidateId == entry.candidateId", [TABLE]),
    ("10 the union keeps duplicates", CARD, "$0.candidateId == entry.candidateId && $0.date == entry.date",
     "$0.candidateId == entry.candidateId && $0.date == entry.date && false", [TABLE]),
    ("11 the epoch a day early", DAY, "epochJulianDay = 2_440_588", "epochJulianDay = 2_440_587", [KNOWN, OLDEST]),
    ("12 the era offset a day late", DAY, "number + 719_468", "number + 719_469", [KNOWN]),
    ("13 January is month 13", DAY, "shiftedMonth < 10 ? shiftedMonth + 3", "shiftedMonth < 11 ? shiftedMonth + 3",
     [KNOWN]),
    ("14 February keeps the counted year", DAY, "month <= 2 ? year + 1", "month < 2 ? year + 1", [KNOWN]),
    ("15 the day's +1 dropped", DAY, "(153 * shiftedMonth + 2) / 5 + 1", "(153 * shiftedMonth + 2) / 5", [KNOWN]),
    ("16 the century rule off by a day", DAY, "dayOfEra / 36_524", "dayOfEra / 36_525", [SWEEP]),
    ("17 the retention bound a day short", DAY, "(Surprise.shownDays - 1)", "Surprise.shownDays", [OLDEST, RETAIN]),
    ("18 the pick's window inclusive", PICK, BLOCK, BLOCK.replace("< shownDays", "<= shownDays"), [RETAIN]),
    ("19 the pick's window a day short", PICK, BLOCK, BLOCK.replace("< shownDays", "< shownDays - 1"), [RETAIN]),
    ("20 the pick's shown block off", PICK, BLOCK, "false && " + BLOCK, [REPICK, RETAIN]),
]

# (name, path, old, new, witness): cannot change behaviour, so anything but MISSED is a failure.
EQUIVALENT = [
    ("E1 the era's zero on the other branch", DAY, "(z >= 0 ? z : z - 146_096)", "(z > 0 ? z : z - 146_096)",
     "the branches differ only at z == 0, where the else branch is -146_096 / 146_097, which Swift's integer "
     "division truncates toward zero to 0 - the then branch's 0 / 146_097"),
]

MIN_MUTATIONS = 20
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 2
