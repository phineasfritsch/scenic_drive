"""The mutation population for T-0300's corpus OTA core: the manifest parser (Sources/PlaceStore/CorpusManifest.swift),
the decision, verify and activation (CorpusUpdater.swift), the slots and their rename (CorpusSlots.swift), the
SHA-256 (SHA256.swift) and the drive hold (DriveSessionLock.swift, DriveSessionToken.swift). The driver is
corpusota.py and the runner corpusota_run.py (saveddrive's three-file shape).

## What the acceptance names, and where each lives

  * the DECISION - the schema gate, the build gate, up-to-date - entries 1-6 (O2);
  * the MANIFEST - the key set, every value bound, the field a type error names - 7-13 (O1);
  * the VERIFY - byte count, hash, staging cleanup, the slot a pass lands in - 14-17 (O6);
  * the ACTIVATION - warm, drive, validator, undo, cleanup, interrupted-swap recovery - 18-23 (O7);
  * the SHA-256 - a round constant, padding, the length field, a rotation, the state carry, the chunked file read,
    the hex padding - 24-30 (O6);
  * the SLOTS - the pending path, the dev-box replace, remove, exists - 31-34 (O4); only the Windows branch of
    `replace` is compiled on this box, so the rename(2) branch is CI's, not this population's;
  * the DRIVE HOLD - the held test, hold, release, a second end, deinit - 35-39 (O7).

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing names in CorpusUpdateDecisionTests, CorpusStageTests, CorpusActivationTests
and SHA256Tests, every one of which must go red. EQUIVALENT entries are `(name, path, old, new, witness)` and must
all report MISSED.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

_DIR = ROOT / "Sources" / "PlaceStore"
MANIFEST = _DIR / "CorpusManifest.swift"
UPDATER = _DIR / "CorpusUpdater.swift"
SLOTS = _DIR / "CorpusSlots.swift"
SHA = _DIR / "SHA256.swift"
LOCK = _DIR / "DriveSessionLock.swift"
TOKEN = _DIR / "DriveSessionToken.swift"
SUBJECTS = (MANIFEST, UPDATER, SLOTS, SHA, LOCK, TOKEN)
MUTATED_FILES = SUBJECTS

_TESTS = ROOT / "Tests" / "PlaceStoreTests"
TEST_FILES = (_TESTS / "CorpusUpdateDecisionTests.swift", _TESTS / "CorpusStageTests.swift",
              _TESTS / "CorpusActivationTests.swift", _TESTS / "SHA256Tests.swift")

DA = "decisionTableVariantA()"
DB = "decisionTableVariantB()"
VA = "verifyTablePayloadA()"
VB = "verifyTablePayloadB()"
AO = "activationTableOverAnOldCorpus()"
AF = "activationTableOnFirstInstall()"
HOLD = "aDriveTokenIsHeldUntilItsLastEndOrDeinit()"
DIGEST = "digestsEqualHashlib()"
FILE = "aFileHashedInChunksEqualsHashlib()"

MUTATIONS = [
    ("1 schema gate == becomes >=", UPDATER, "guard manifest.schemaVersion == PlaceStore.schemaVersion else {",
     "guard manifest.schemaVersion >= PlaceStore.schemaVersion else {", [DA, DB]),
    ("2 schema gate compares the manifest to itself", UPDATER,
     "guard manifest.schemaVersion == PlaceStore.schemaVersion else {",
     "guard manifest.schemaVersion == manifest.schemaVersion else {", [DA, DB]),
    ("3 build gate <= becomes <", UPDATER, "guard manifest.minAppBuild <= appBuild else {",
     "guard manifest.minAppBuild < appBuild else {", [DA, DB]),
    ("4 build gate compares the manifest to itself", UPDATER, "guard manifest.minAppBuild <= appBuild else {",
     "guard manifest.minAppBuild <= manifest.minAppBuild else {", [DA, DB]),
    ("5 up-to-date when the version differs", UPDATER, "if manifest.version == activeVersion {",
     "if manifest.version != activeVersion {", [DA, DB]),
    ("6 never up to date", UPDATER, "if manifest.version == activeVersion {", "if false {", [DA, DB]),
    ("7 an extra key accepted", MANIFEST, "guard keys == fields else {", "guard keys.isSuperset(of: fields) else {",
     [DA, DB]),
    ("8 bytes 0 accepted", MANIFEST, "guard manifest.bytes >= 1 else", "guard manifest.bytes >= 0 else", [DA, DB]),
    ("9 a sha256 longer than 64 accepted", MANIFEST, "manifest.sha256.utf8.count == 64",
     "manifest.sha256.utf8.count >= 64", [DA, DB]),
    ("10 uppercase hex accepted", MANIFEST, "(0x61...0x66)", "(0x41...0x66)", [DA, DB]),
    ("11 an empty version accepted", MANIFEST, "guard !manifest.version.isEmpty else",
     "guard !manifest.version.isEmpty || true else", [DA, DB]),
    ("12 a field's type error names no field", MANIFEST,
     "throw CorpusUpdateError.manifestFieldType(field: key.rawValue)",
     "throw CorpusUpdateError.manifestFieldType(field: \"\")", [DA, DB]),
    ("13 an up-front type error names no field", MANIFEST,
     "throw CorpusUpdateError.manifestFieldType(field: named ?? \"\")",
     "throw CorpusUpdateError.manifestFieldType(field: \"\")", [DA, DB]),
    ("14 the byte count is not compared", UPDATER, "guard found.count == manifest.bytes, hashMatches else",
     "guard hashMatches else", [VA, VB]),
    ("15 the hash is not compared", UPDATER, "guard found.count == manifest.bytes, hashMatches else",
     "guard found.count == manifest.bytes else", [VA, VB]),
    ("16 a refused staging file is left behind", UPDATER, "            slots.remove(staging)\n            throw error",
     "            throw error", [VA, VB]),
    ("17 a verified download renamed over active", UPDATER, "try slots.replace(slots.pending, with: staging)",
     "try slots.replace(slots.active, with: staging)", [VA, VB]),
    ("18 a warm resume swaps", UPDATER, "guard isColdLaunch else {", "guard isColdLaunch || true else {", [AO, AF]),
    ("19 a held drive does not defer", UPDATER, "guard !drives.isHeld else {",
     "guard !drives.isHeld || true else {", [AO, AF]),
    ("20 the swapped-in corpus is not validated", UPDATER, "            try validate(slots.active)\n", "", [AO, AF]),
    ("21 a refused swap is not undone", UPDATER,
     "                try? slots.replace(slots.active, with: slots.previous)\n            } else if",
     "            } else if", [AO]),
    ("22 the undo slot is kept after a good swap", UPDATER, "        slots.remove(slots.previous)\n        return .activated",
     "        return .activated", [AO]),
    ("23 an interrupted swap is not restored", UPDATER,
     "        if slots.exists(slots.previous) {\n            try? slots.replace(slots.active, with: slots.previous)\n"
     "        }\n", "", [AO]),
    ("24 a round constant off by one", SHA, "0x428a_2f98", "0x428a_2f99", [DIGEST]),
    ("25 padding to 55 mod 64", SHA, "while tail.count % 64 != 56 {", "while tail.count % 64 != 55 {", [DIGEST]),
    ("26 the length field in bytes, not bits", SHA, "UInt64(count) &* 8", "UInt64(count)", [DIGEST]),
    ("27 sigma0 rotates by 8", SHA, "Self.rotr(w[i - 15], 7)", "Self.rotr(w[i - 15], 8)", [DIGEST]),
    ("28 the last state word not carried", SHA, "state[7] &+= h", "state[7] = h", [DIGEST]),
    ("29 a file read in one chunk only", SHA, "while let data = try handle.read(upToCount: chunk), !data.isEmpty {",
     "if let data = try handle.read(upToCount: chunk), !data.isEmpty {", [FILE]),
    ("30 hex words not zero-padded", SHA, "String(repeating: \"0\", count: 8 - digits.count) + digits", "digits",
     [DIGEST]),
    ("31 pending is the active path", SLOTS, "\"corpus-pending.sqlite\"", "\"corpus.sqlite\"", [VA, VB]),
    ("32 replace does not clear its target", SLOTS,
     "        if files.fileExists(atPath: destination.path) {\n            try files.removeItem(at: destination)\n"
     "        }\n", "", [VA, VB]),
    ("33 remove removes nothing", SLOTS, "try? FileManager().removeItem(at: url)", "_ = url", [VA, VB]),
    ("34 every slot exists", SLOTS, "FileManager().fileExists(atPath: url.path)", "true", [AO, AF]),
    ("35 one token is not a hold", LOCK, "return held > 0", "return held > 1", [AO, AF, HOLD]),
    ("36 hold takes nothing", LOCK, "held += 1", "held += 0", [AO, AF, HOLD]),
    ("37 release releases nothing", LOCK, "held -= 1", "held -= 0", [AO, AF, HOLD]),
    ("38 a second end releases again", TOKEN, "let first = !ended", "let first = true", [HOLD]),
    ("39 deinit keeps the hold", TOKEN, "    deinit {\n        end()\n    }", "    deinit {}", [AO, AF]),
]

EQUIVALENT = [
    ("E1 a rejected swap does not delete the pending slot", UPDATER,
     "            slots.remove(slots.pending)\n            if movedOld", "            if movedOld",
     "every path into openForLaunch's catch that a table can reach has already run `replace(active, with: pending)`, "
     "which MOVED the pending file, so the slot is empty when this line runs; the line is there for a rename that "
     "throws, which no fake can induce without a fault-injecting file system"),
]

MIN_MUTATIONS = 39
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 4
