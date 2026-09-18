"""Prove the hand-authored project.pbxproj object graph is closed and says what it claims.

Nothing here parses Xcode's format properly - it is an OpenStep plist and this is text. That is
deliberate: the point is to catch a dangling 24-hex ID or a renamed product on a box with no Xcode,
which is the only failure mode a hand-authored pbxproj actually has.

Never anchored on a comment (CLAUDE.md): comments are masked out before anything is parsed, so the
/* ScenicDrive */ annotations Xcode regenerates carry no weight here.

Run:  python ops/lib/check-pbxproj-graph.py
Exit: 0 all assertions hold, 1 otherwise.

Lives under ops/ so it survives the merge: it was authored at .artifacts/T-0141/pbxproj-graph.py,
which is gitignored, so an acceptance line naming that path could not be run from the merged tree.
Data file, not a wrapper: 100644 like every other *.py under ops/, invoked as `python <path>`.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PBX = os.path.join(ROOT, "apps", "ios", "ScenicDrive.xcodeproj", "project.pbxproj")
SCHEME = os.path.join(ROOT, "apps", "ios", "ScenicDrive.xcodeproj", "xcshareddata",
                      "xcschemes", "ScenicDrive.xcscheme")
PKG = os.path.join(ROOT, "apps", "ios", "Packages", "ScenicApp", "Package.swift")
PLIST = os.path.join(ROOT, "apps", "ios", "ScenicDrive", "Info.plist")

APP_TARGET = "ScenicDrive"
FALLBACK_PRODUCT = "FeatureScenicHome"
BUNDLE_ID = "com.phineasfritsch.scenicdrive"

ID_RE = re.compile(r"(?<![0-9A-Za-z])([0-9A-F]{24})(?![0-9A-Za-z])")
DEF_RE = re.compile(r"^[ \t]*([0-9A-F]{24})[ \t]*=[ \t]*\{", re.M)

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def mask_comments(text):
    """Blank every /* ... */ span, keeping offsets and newlines so line numbers survive."""
    out = list(text)
    for m in re.finditer(r"/\*.*?\*/", text, re.S):
        for i in range(m.start(), m.end()):
            if out[i] != "\n":
                out[i] = " "
    return "".join(out)


def body_at(text, start):
    """The { ... } body of the object whose definition begins at `start`."""
    i = text.index("{", start)
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j]
    raise ValueError("unbalanced braces from offset %d" % start)


def bracket_region(text, start, open_ch="[", close_ch="]"):
    i = text.index(open_ch, start)
    depth = 0
    for j in range(i, len(text)):
        if text[j] == open_ch:
            depth += 1
        elif text[j] == close_ch:
            depth -= 1
            if depth == 0:
                return text[i + 1:j]
    raise ValueError("unbalanced brackets")


def scalar(body, key):
    m = re.search(r"\b%s\s*=\s*([^;\n]+);" % re.escape(key), body)
    return m.group(1).strip().strip('"') if m else None


def id_list(body, key):
    m = re.search(r"\b%s\s*=\s*\(([^)]*)\)" % re.escape(key), body, re.S)
    return ID_RE.findall(m.group(1)) if m else []


raw = open(PBX, encoding="utf-8").read()
masked = mask_comments(raw)

# --- (a) every referenced 24-hex ID is defined, and every defined ID is referenced -----------
# Only entries at depth 0 inside `objects = { ... }` are object definitions. `TargetAttributes`
# nests `<targetID> = { ... }` one level deeper and reads exactly like one; treating it as a
# definition made the real PBXNativeTarget unreachable and every target assertion came back None.
objects_region = body_at(masked, masked.index("objects"))
base = masked.index("{", masked.index("objects")) + 1
region_depth, d = [], 0
for ch in objects_region:
    region_depth.append(d)
    if ch == "{":
        d += 1
    elif ch == "}":
        d -= 1

defs = {}
dupes = []
for m in DEF_RE.finditer(objects_region):
    if region_depth[m.start(1)] != 0:
        continue
    if m.group(1) in defs:
        dupes.append(m.group(1))
    defs[m.group(1)] = base + m.start(1)
check("object IDs are unique", not dupes, ", ".join(dupes) or "%d objects" % len(defs))
def_starts = set(defs.values())

refs = {}
for m in ID_RE.finditer(masked):
    if m.start(1) in def_starts:
        continue
    refs.setdefault(m.group(1), 0)
    refs[m.group(1)] += 1

dangling = sorted(set(refs) - set(defs))
orphans = sorted(set(defs) - set(refs))
check("every referenced ID is defined", not dangling,
      "dangling: %s" % ", ".join(dangling) if dangling else
      "%d objects defined, %d distinct IDs referenced" % (len(defs), len(refs)))
check("every defined ID is referenced", not orphans,
      "orphans: %s" % ", ".join(orphans) if orphans else "no unreachable objects")
check("all object IDs are 24 hex chars", all(len(k) == 24 for k in defs),
      "%d IDs" % len(defs))

# --- (b) the project's targets list names the app target -------------------------------------
root_m = re.search(r"\brootObject\s*=\s*([0-9A-F]{24})", masked)
check("rootObject resolves to a PBXProject",
      root_m is not None and root_m.group(1) in defs,
      root_m.group(1) if root_m else "no rootObject")

proj_body = body_at(masked, defs[root_m.group(1)]) if root_m else ""
check("rootObject isa PBXProject", scalar(proj_body, "isa") == "PBXProject",
      str(scalar(proj_body, "isa")))
check("objectVersion is 77", scalar(masked, "objectVersion") == "77",
      str(scalar(masked, "objectVersion")))

target_ids = id_list(proj_body, "targets")
named = []
app_target_id = None
for tid in target_ids:
    tbody = body_at(masked, defs[tid])
    name = scalar(tbody, "name")
    named.append("%s (%s)" % (name, scalar(tbody, "productType")))
    if name == APP_TARGET:
        app_target_id = tid
check("exactly one target", len(target_ids) == 1, "; ".join(named) or "none")
check("the targets list names %s" % APP_TARGET, app_target_id is not None,
      "; ".join(named) or "none")

tbody = body_at(masked, defs[app_target_id]) if app_target_id else ""
check("%s is an application" % APP_TARGET,
      scalar(tbody, "productType") == "com.apple.product-type.application",
      str(scalar(tbody, "productType")))
check("%s uses a buildable folder" % APP_TARGET,
      len(id_list(tbody, "fileSystemSynchronizedGroups")) == 1,
      "fileSystemSynchronizedGroups=%s" % id_list(tbody, "fileSystemSynchronizedGroups"))

# --- (c) the target's buildConfigurationList has two configurations ---------------------------
list_id = scalar(tbody, "buildConfigurationList")
check("%s has a buildConfigurationList" % APP_TARGET,
      list_id in defs, str(list_id))
cfg_names, cfg_settings = [], {}
if list_id in defs:
    lbody = body_at(masked, defs[list_id])
    cfg_ids = id_list(lbody, "buildConfigurations")
    for cid in cfg_ids:
        cbody = body_at(masked, defs[cid])
        cname = scalar(cbody, "name")
        cfg_names.append(cname)
        cfg_settings[cname] = cbody
    check("two build configurations", len(cfg_ids) == 2, ", ".join(map(str, cfg_names)))
    check("they are Debug and Release", sorted(cfg_names) == ["Debug", "Release"],
          ", ".join(map(str, cfg_names)))

REQUIRED = {
    "IPHONEOS_DEPLOYMENT_TARGET": "18.4",
    "TARGETED_DEVICE_FAMILY": "1",
    "SWIFT_VERSION": "6.0",
    "GENERATE_INFOPLIST_FILE": "NO",
    "INFOPLIST_FILE": "ScenicDrive/Info.plist",
    "CODE_SIGN_STYLE": "Automatic",
    "PRODUCT_BUNDLE_IDENTIFIER": BUNDLE_ID,
}
for key, want in sorted(REQUIRED.items()):
    got = {c: scalar(cfg_settings[c], key) for c in cfg_settings}
    check("%s = %s in both configs" % (key, want),
          bool(got) and all(v == want for v in got.values()), str(got))

# --- (d) the package product dependency names a product the package declares -------------------
dep_ids = id_list(tbody, "packageProductDependencies")
dep_names = []
for did in dep_ids:
    dbody = body_at(masked, defs[did])
    check("dependency %s isa XCSwiftPackageProductDependency" % did,
          scalar(dbody, "isa") == "XCSwiftPackageProductDependency", str(scalar(dbody, "isa")))
    dep_names.append(scalar(dbody, "productName"))

pkg_ref_ids = id_list(proj_body, "packageReferences")
rel_paths = []
for pid in pkg_ref_ids:
    pbody = body_at(masked, defs[pid])
    if scalar(pbody, "isa") == "XCLocalSwiftPackageReference":
        rel_paths.append(scalar(pbody, "relativePath"))
check("a local package reference to Packages/ScenicApp",
      rel_paths == ["Packages/ScenicApp"], str(rel_paths))

if os.path.exists(PKG):
    src = open(PKG, encoding="utf-8").read()
    region = bracket_region(src, src.index("products:"))
    products = re.findall(r'name\s*:\s*"([^"]+)"', region)
    source = "Package.swift declares %s" % products
else:
    products = [FALLBACK_PRODUCT]
    source = ("Package.swift ABSENT at the time of this run - asserted against the literal %r "
              "agreed with the other agent, NOT against a real product list" % FALLBACK_PRODUCT)
check("every packageProductDependency is a declared product",
      bool(dep_names) and all(d in products for d in dep_names),
      "target imports %s; %s" % (dep_names, source))

# --- extras: the two facts the Brief states about the shell, checked rather than claimed ------
if os.path.exists(PLIST):
    plist = open(PLIST, encoding="utf-8").read()
    check("Info.plist has no UIBackgroundModes", "UIBackgroundModes" not in plist,
          "the plan allows location/audio only with the Drive target")
    check("CFBundleIdentifier defers to PRODUCT_BUNDLE_IDENTIFIER",
          re.search(r"<key>CFBundleIdentifier</key>\s*<string>\$\(PRODUCT_BUNDLE_IDENTIFIER\)</string>",
                    plist) is not None,
          "one literal, in the pbxproj: %s" % BUNDLE_ID)
    # The panel's one-commit change: nothing under apps/ios reads the user's position, so the key is ABSENT.
    # It returns - with P-PRIV-01's >= 30-char rule - alongside the first feature that asks for location.
    location_key = "NSLocationWhenInUseUsageDescription"
    check("%s is absent because nothing asks for location" % location_key,
          location_key not in plist,
          "present" if location_key in plist else "absent")
else:
    check("Info.plist exists", False, PLIST)

if os.path.exists(SCHEME):
    scheme = open(SCHEME, encoding="utf-8").read()
    bps = set(re.findall(r'BlueprintIdentifier = "([^"]+)"', scheme))
    check("shared scheme points at the app target", bps == {app_target_id}, str(sorted(bps)))
else:
    check("shared scheme exists", False, SCHEME)

width = max(len(n) for n, _, _ in results)
failed = 0
for name, ok, detail in results:
    if not ok:
        failed += 1
    print("%-4s %-*s  %s" % ("ok" if ok else "FAIL", width, name, detail))
print("pbxproj-graph: %d assertions, %d failed" % (len(results), failed))
sys.exit(1 if failed else 0)
