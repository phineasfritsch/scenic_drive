"""The mutation population for T-0305's corpus download: the URLSession fetcher
(Sources/ScenicAPIClient/URLSessionCorpusFetcher.swift), its streaming delegate (CorpusDownloadDelegate.swift) and
the launch choice (Sources/PlaceStore/LaunchCorpus.swift). The driver is corpusfetch.py and the runner
corpusfetch_run.py (corpusota's three-file shape).

## What the acceptance names, and where each lives

  * the RESUME - the Range header, the over-long and complete resume files - 1-3 (R3);
  * the ERRORS - which error deletes the resume file, a short body, a long body, a 206 at the wrong byte or with no
    Range, a dropped connection's code, the manifest's status and code, a refusal reported under the cancel it
    caused - 4-6, 12-16, 22 (R3);
  * the NAMES - the corpus URL, the resume file's key, Wi-Fi only - 7-9 (R1, R3, R6);
  * the LAUNCH CHOICE - cold launch, the existence test, the record, the fallback - 17-21 (R4).

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing names in URLSessionCorpusFetcherTests and CorpusLaunchTests, every one of which
must go red. EQUIVALENT entries are `(name, path, old, new, witness)` and must all report MISSED.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

FETCHER = ROOT / "Sources" / "ScenicAPIClient" / "URLSessionCorpusFetcher.swift"
DELEGATE = ROOT / "Sources" / "ScenicAPIClient" / "CorpusDownloadDelegate.swift"
LAUNCH = ROOT / "Sources" / "PlaceStore" / "LaunchCorpus.swift"
SUBJECTS = (FETCHER, DELEGATE, LAUNCH)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "ScenicAPIClientTests" / "URLSessionCorpusFetcherTests.swift",
              ROOT / "Tests" / "PlaceStoreTests" / "CorpusLaunchTests.swift")

FETCH = "fetchTableOverEveryResumeFileAndServer()"
MAN = "manifestFetchReturnsTheBodyOrATypedError()"
NAMES = "wifiOnlyRefusesCellularAndTheNamesAreRuled()"
CHOICE = "launchChoosesTheActivatedCorpusElseTheFallback()"

_URLERR = "(error as? URLError)?.code.rawValue ?? -1))"

MUTATIONS = [
    ("1 the Range header asks one byte late", FETCHER, 'request.setValue("bytes=\\(have)-"',
     'request.setValue("bytes=\\(have + 1)-"', [FETCH]),
    ("2 a resume file one byte too long is kept", FETCHER, "if have > manifest.bytes {",
     "if have > manifest.bytes + 1 {", [FETCH]),
    ("3 a complete resume file is requested again", FETCHER, "if have < manifest.bytes {",
     "if have <= manifest.bytes {", [FETCH]),
    ("4 a refused status keeps the resume file", FETCHER,
     "case .status, .longBody: try? files.removeItem(at: part)\n                case .shortBody, .transport: break",
     "case .longBody: try? files.removeItem(at: part)\n                case .status, .shortBody, .transport: break",
     [FETCH]),
    ("5 a dropped connection deletes the resume file", FETCHER,
     "case .status, .longBody: try? files.removeItem(at: part)\n                case .shortBody, .transport: break",
     "case .status, .longBody, .transport: try? files.removeItem(at: part)\n                case .shortBody: break",
     [FETCH]),
    ("6 a short body is renamed into place", FETCHER, "guard have == manifest.bytes else {",
     "guard have <= manifest.bytes else {", [FETCH]),
    ("7 the corpus URL is not the version's sibling", FETCHER,
     'appendingPathComponent("corpus-\\(manifest.version).sqlite")', 'appendingPathComponent("corpus.sqlite")',
     [FETCH, NAMES]),
    ("8 the resume file is keyed by version, not hash", FETCHER, '"corpus-\\(manifest.sha256).part"',
     '"corpus-\\(manifest.version).part"', [NAMES]),
    ("9 Wi-Fi only allows cellular", FETCHER, "configuration.allowsCellularAccess = !wifiOnly",
     "configuration.allowsCellularAccess = wifiOnly", [NAMES]),
    ("10 the manifest accepts any status", FETCHER, "guard status == 200 else {", "guard status < 600 else {", [MAN]),
    ("11 the manifest drops the URLError code", FETCHER,
     "continuation.resume(throwing: CorpusFetchError.transport(code: " + _URLERR,
     "continuation.resume(throwing: CorpusFetchError.transport(code: -1))", [MAN]),
    ("12 a 200 after a Range keeps counting from the resume offset", DELEGATE,
     "try handle.truncate(atOffset: 0)\n                onDisk = 0\n", "try handle.truncate(atOffset: 0)\n", [FETCH]),
    ("13 a 206 is accepted when no Range was sent", DELEGATE,
     'status == 206, offset > 0, range.hasPrefix("bytes \\(offset)-")', 'status == 206, range.hasPrefix("bytes ")',
     [FETCH]),
    ("14 a 206's Content-Range is not checked", DELEGATE,
     'status == 206, offset > 0, range.hasPrefix("bytes \\(offset)-")', "status == 206, offset > 0", [FETCH]),
    ("15 one byte past the corpus is accepted", DELEGATE, "guard onDisk + data.count <= expected else {",
     "guard onDisk + data.count <= expected + 1 else {", [FETCH]),
    ("16 a dropped connection drops the URLError code", DELEGATE,
     "continuation?.resume(throwing: CorpusFetchError.transport(code: " + _URLERR,
     "continuation?.resume(throwing: CorpusFetchError.transport(code: -1))", [FETCH]),
    ("17 the launch is treated as warm", LAUNCH, "let activation = updater.openForLaunch(isColdLaunch: true)",
     "let activation = updater.openForLaunch(isColdLaunch: false)", [CHOICE]),
    ("18 the active slot is chosen without existing", LAUNCH, "updater.slots.exists(active) ? active : nil",
     "active", [CHOICE]),
    ("19 the choice is not recorded", LAUNCH, "        downloaded = chosen\n", "        downloaded = nil\n",
     [CHOICE]),
    ("20 a feature's ask ignores the record", LAUNCH, "return downloaded ?? fallback", "return fallback", [CHOICE]),
    ("21 no corpus active and the fallback dropped", LAUNCH, "corpus: chosen ?? fallback)", "corpus: chosen)",
     [CHOICE]),
    ("22 the session's cancel error outranks the refusal that caused it", DELEGATE,
     "        if let failure {\n            continuation?.resume(throwing: failure)\n        } else if let error {\n"
     "            continuation?.resume(throwing: CorpusFetchError.transport(code: " + _URLERR + "\n        } else {\n",
     "        if let error {\n"
     "            continuation?.resume(throwing: CorpusFetchError.transport(code: " + _URLERR + "\n"
     "        } else if let failure {\n            continuation?.resume(throwing: failure)\n        } else {\n",
     [FETCH]),
]

EQUIVALENT = [
    ("E1 the destination is not cleared before the fetch", FETCHER,
     "        try? files.removeItem(at: destination)\n", "",
     "the only caller, CorpusUpdater.stage, removes the staging file (the destination) before every fetch and again "
     "on every failure, so no table row - and no production path - reaches fetch with a destination present"),
]

MIN_MUTATIONS = 22
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 2
