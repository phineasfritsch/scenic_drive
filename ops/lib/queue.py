#!/usr/bin/env python3
"""Repo work queue. State IS the directory; every transition is a git commit (and a push, for claims).

  queue.py new "<title>" [--touches a,b] [--exclusive x,y] [--depends T-0001,...] [--state backlog|ready]
  queue.py check              exit 1 on any protocol violation (reviewer == owner, review/ without reviewer, ...)
  queue.py sweep              move expired claimed/ tasks back to ready/, release their LOCKS, append to ## Log
  queue.py review ID --reviewer NAME   claimed/ -> review/, assign the reviewer, release its LOCKS
  queue.py next               print the next unblocked ready/ task id
  queue.py claim T-0007 --owner agent/x --session <id> [--worktree .worktrees/T-0007] [--hours 2]
  queue.py lock T-0007 [--owner agent/x]   acquire locks a claimed task declares but does not hold

--touches, --exclusive, --pins and --depends are LISTS: repeat the flag or use commas, in any mix. Every
other flag holds one value and repeating it is refused, as is an unknown flag, a flag with no value, and a
stray word - all four used to be accepted silently and cost the task file its declared scope (T-0084).

No PyYAML: front matter is parsed by a deliberately small reader (scalars, [flow, lists], and `- ` block lists).
"""
import datetime as dt
import os
import hashlib
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
Q = ROOT / "queue"
STATES = ["backlog", "ready", "claimed", "review", "blocked", "done"]
LOCKS = Q / "LOCKS"


# ----------------------------------------------------------------------------- front matter
def parse(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError("no front matter")
    fm, body = {}, m.group(2)
    key = None
    for line in m.group(1).splitlines():
        if re.match(r"^\s+-\s", line) and key:
            fm.setdefault(key, [])
            if not isinstance(fm[key], list):
                fm[key] = []
            fm[key].append(_scalar(line.split("-", 1)[1]))
            continue
        km = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if not km:
            continue
        key, val = km.group(1), km.group(2).strip()
        # LAST-WINS is the amplifier, not the newline. `dump()` writes each key once, so a second one means
        # the file was hand-edited, arrived from a merge, or was injected through a value - and in every
        # case silently preferring the later line is how `owner:` gets displaced by something written below
        # it. Refuse instead. Measured before enforcing: 0 of the task files in this tree carry a duplicate.
        if key in fm:
            raise ValueError(
                f"front matter defines {key!r} twice; the parser is last-wins, so the later line silently "
                f"replaces the earlier one. That is the shape a value containing a newline produces.")
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            fm[key] = [_scalar(v) for v in inner.split(",")] if inner else []
        elif val == "":
            fm[key] = None  # may be filled by a block list
        else:
            fm[key] = _scalar(val)
    return fm, body


def _scalar(v):
    v = v.strip()
    if v in ("null", "~", ""):
        return None
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


AGENT_NAME = re.compile(r"^agent/[a-z0-9][a-z0-9._+-]*$")
NOT_A_NAME = frozenset({"", "-", "~", "nil", "none", "null", "true", "false"})


def agent(v):
    """Normalise an owner/reviewer field to a comparable agent name, or None if it is not one.

    P-PROC-01 is an INEQUALITY. T-0068 hardened the PRESENCE of its operands and left the COMPARISON
    vacuous, and eleven evasions walked through the gap by supplying something truthy that was not a name
    (T-0073): `- agent/self` parses to ['agent/self'], truthy AND != 'agent/self'; `owner: "null"` survives
    _scalar's quote-stripping as the STRING 'null'; `agent/Self` is one capital away. A non-name is a
    FAILURE, never a value to compare - callers must read None as "undecidable", not as "they differ".
    """
    if not isinstance(v, str):
        return None                       # a list (block or flow), None, a number: not a name
    v = v.strip().casefold()
    return v if v not in NOT_A_NAME and AGENT_NAME.match(v) else None


def _no_newline(k, v):
    """A front-matter scalar may not contain a line break. Refuse; do not try to encode it.

    `dump()` decided quoting with a round-trip test - `_scalar(s) == s` - and that is TRUE for a string with
    an embedded newline, because `.strip()` does not touch interior ones. So the value was written raw and
    every line after the first became another key, which `parse()` then applied LAST-WINS:

        fm["reviewer"] = "agent/x\nowner: agent/x"   ->   reviewer: agent/x
                                                          owner: agent/x     <- overwrites line 5's null

    One field setting another, in the format P-PROC-01 reads. The reviewer-is-not-owner rule that T-0068 and
    T-0073 were both filed to make un-evadable is satisfied while the real owner is displaced.

    Quoting does not fix it: `reviewer: "agent/x\nowner: agent/x"` still occupies two physical lines and the
    second still parses as a key. The value has no representation here, so writing it is the bug.
    """
    if isinstance(v, str) and ("\n" in v or "\r" in v):
        raise ValueError(
            f"front-matter field {k!r} contains a line break, which cannot be written: every line after the "
            f"first would parse as another key and overwrite it (last-wins). Value: {v!r}")
    return v


def dump(fm, body):
    lines = ["---"]
    for k, v in fm.items():
        _no_newline(k, v)
        if isinstance(v, list):
            for x in v:
                _no_newline(k, x)
        if isinstance(v, list):
            if k == "acceptance" and v:
                lines.append(f"{k}:")
                lines += [f"  - \"{x}\"" for x in v]
            else:
                lines.append(f"{k}: [{', '.join(str(x) for x in v)}]")
        elif v is None:
            lines.append(f"{k}: null")
        else:
            # Round-trip, never reinterpret. The string 'null' was written back as a bare `null`, so
            # ops/review on a task carrying owner: "null" MANUFACTURED the real null the guard exists to
            # refuse (T-0073 route 2). Any scalar parse() would not read back unchanged is quoted.
            s = str(v)
            lines.append(f"{k}: {s}" if _scalar(s) == s else f"{k}: \"{s}\"")
    lines.append("---")
    return "\n".join(lines) + "\n" + body.lstrip("\n")


# ----------------------------------------------------------------------------- helpers
def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def iso(t):
    return t.isoformat().replace("+00:00", "Z")


TASK_FILE = re.compile(r"^T-\d{4}-[A-Za-z0-9._-]+\.md$")
TASK_ID = re.compile(r"^T-\d{4}$")
NOT_TASKS = frozenset({".gitkeep"})
KNOWN_DIRS = frozenset(STATES) | {"LOCKS", "_schema"}
MIN_TASKS = 40


def tasks():
    """yield (state, path, fm, body) for EVERY file in a state directory except .gitkeep.

    The glob was rglob("T-*.md"), and a file it could not see was a file no check could fail on:
    queue/done/selfgraded-fixture.md was owner == reviewer == agent/self and queue-check printed QUEUE OK
    without counting it, as did the same fixture saved as .markdown (T-0073). Name discipline is now
    ASSERTED in cmd_check instead of enforced by invisibility; an unreadable file yields fm={} so callers
    report it rather than raising a traceback at whoever ran an unrelated command.
    """
    for state in STATES:
        d = Q / state
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*")):
            if not p.is_file() or p.name in NOT_TASKS:
                continue
            try:
                fm, body = parse(p.read_text(encoding="utf-8"))
            except (ValueError, OSError, UnicodeDecodeError):
                fm, body = {}, ""
            yield state, p, fm, body


# Set by _ids_in_refs() when its scan could not be completed. A module global rather than a return value
# because every existing caller reads the set and none of them asked; making it a tuple would have let a
# caller keep ignoring it, which is exactly what happened.
SCAN_DEGRADED = []


def _ids_in_refs():
    """Task ids visible on every remote-tracking branch, not just this worktree.

    Without this, two branches allocate the same id: T-0015 was created on task/T-0007 and again on
    task/T-0011 because the first was pushed but unmerged, and `queue-check` only notices once both land.
    Scanning remote refs catches every id that has been PUSHED, and that is all it can do.

    This docstring used to end "the push is the compare-and-swap that settles that, exactly as for claims."
    That was false, and it is the sentence T-0101 was filed against. For a CLAIM the push really is the CAS:
    the moved file goes to main and a rejected push means somebody else moved it first. For an ALLOCATION
    nothing is pushed at allocation time, and the task file's eventual push goes to a task BRANCH, where it
    can never conflict with another branch's push. There was no second step, only a longer read.

    Measured on 2026-09-08: T-0099 and T-0088 were each allocated twice, hours apart, by agents that both
    read the refs before either had pushed anything. `_reserve_id()` below supplies the missing step.
    """
    ids = set()

    def warn(what, detail):
        SCAN_DEGRADED.append(what)
        # Never silent: a degraded scan means collision protection is off, and the caller must know.
        # This is the difference between "offline, as expected" and "the network hiccupped and you now
        # have a duplicate id you will not notice until two branches merge".
        print(f"WARNING: next_id could not {what} ({detail}); id allocation is falling back to this "
              f"worktree only, so a duplicate id is possible. Verify with ops/queue-check after pushing.",
              file=sys.stderr)

    try:
        r = subprocess.run(["git", "fetch", "--quiet", "--all"], cwd=ROOT, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            warn("fetch remotes", (r.stderr or "").strip().splitlines()[-1] if r.stderr.strip() else f"exit {r.returncode}")
    except Exception as e:
        warn("fetch remotes", type(e).__name__)

    try:
        refs = subprocess.run(["git", "for-each-ref", "--format=%(refname)", "refs/remotes"],
                              cwd=ROOT, capture_output=True, text=True, timeout=30)
        if refs.returncode != 0:
            warn("list remote refs", f"exit {refs.returncode}")
            return ids
        for ref in refs.stdout.split():
            if ref.endswith("/HEAD"):
                continue
            out = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref, "queue/"],
                                 cwd=ROOT, capture_output=True, text=True, timeout=30)
            if out.returncode != 0:
                warn(f"read queue/ on {ref}", f"exit {out.returncode}")
                continue
            for name in out.stdout.splitlines():
                m = re.search(r"/(T-(\d+))-", name)
                if m:
                    ids.add(int(m.group(2)))
    except Exception as e:
        warn("scan remote refs", type(e).__name__)
    return ids


ID_TAG = "refs/tags/id/"


def _git_env():
    """MSYS rewrites any argument that looks like a path, and `HEAD:refs/tags/...` looks like one.

    Without this, `HEAD:refs/tags/id/T-0103` reaches git as `HEAD;C:/Program Files/Git/refs/tags/...` and
    the push fails for a reason that has nothing to do with the id. Measured in this repo on the merge
    tooling before it was measured here.
    """
    env = dict(os.environ)
    env["MSYS_NO_PATHCONV"] = "1"
    env["MSYS2_ARG_CONV_EXCL"] = "*"
    return env


def _reserved_ids():
    """Ids reserved on the remote, whether or not any branch carries a file for them yet.

    Asked of the remote directly rather than of local refs: a reservation made by another agent one second
    ago must be visible, and `git fetch` does not bring `refs/tags/id/*` into this repo by default.

    Returns a set, or None for "could not ask" - which the caller must not read as "none reserved".
    """
    try:
        r = subprocess.run(["git", "ls-remote", "--refs", "origin", ID_TAG + "T-*"],
                           cwd=ROOT, capture_output=True, text=True, timeout=60, env=_git_env())
    except Exception:
        return None
    if r.returncode != 0:
        return None
    out = set()
    for line in r.stdout.splitlines():
        m = re.search(r"refs/tags/id/T-(\d+)$", line.strip())
        if m:
            out.add(int(m.group(1)))
    return out


def _remote_ref_object(ref):
    """The object `ref` points at ON THE REMOTE, asked directly rather than inferred.

    Returns the sha, "" for "asked, and the ref is not there", or None for "could not ask". The three are
    different answers and `_reserve_id()` acts differently on each; collapsing "not there" into "could not
    ask" is how a failed push gets read as a lost race.
    """
    try:
        r = subprocess.run(["git", "ls-remote", "--refs", "origin", ref],
                           cwd=ROOT, capture_output=True, text=True, timeout=60, env=_git_env())
    except Exception:
        return None
    if r.returncode != 0:
        return None
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == ref:
            return parts[0]
    return ""


def _reservation_object(n):
    """A commit object that exists nowhere else, created for THIS reservation attempt only.

    This is the whole of the fix for the defect the T-0101 reviewer found, so it is worth being explicit
    about. `git push origin HEAD:refs/tags/id/T-0103` is rejected only when the ref exists at a DIFFERENT
    object. When it already exists at the SAME object git prints "Everything up-to-date" and exits 0. The
    first version of this file read that 0 as "we created the tag", so two allocators that pushed the same
    commit were both told they had won the id.

    That is not an edge case: `ops/new-task` runs at the START of a piece of work, when a fresh worktree has
    no commits of its own and HEAD is still the shared base. Two agents who branch off main and allocate
    therefore have IDENTICAL HEADs - the same-object condition and the collision condition coincide almost
    exactly. This PR's own reservations (T-0103..T-0106) all sit on the single commit 4305be5, which is the
    evidence for it.

    A per-attempt object removes the coincidence: the remote cannot already be at an object that was
    invented here a millisecond ago, so "already there" and "we put it there" stop being confusable. The
    commit is parentless over an empty tree, references nothing, and is never read - only its uniqueness is
    load-bearing. Returns None if the object could not be made, which the caller treats as "cannot ask".
    """
    env = _git_env()
    # A box with no user.name configured can still reserve an id; commit-tree would otherwise refuse.
    env.setdefault("GIT_AUTHOR_NAME", "scenic-drive")
    env.setdefault("GIT_AUTHOR_EMAIL", "id-reservation@scenic.invalid")
    env.setdefault("GIT_COMMITTER_NAME", "scenic-drive")
    env.setdefault("GIT_COMMITTER_EMAIL", "id-reservation@scenic.invalid")
    nonce = f"{os.getpid()} {time.time_ns()} {secrets.token_hex(16)}"
    try:
        tree = subprocess.run(["git", "hash-object", "-w", "-t", "tree", "--stdin"], cwd=ROOT, input="",
                              capture_output=True, text=True, timeout=60, env=env)
        if tree.returncode != 0 or not tree.stdout.strip():
            return None
        obj = subprocess.run(["git", "commit-tree", tree.stdout.strip(), "-m",
                              f"scenic-drive id reservation T-{n:04d}\n\nnonce: {nonce}\n"],
                             cwd=ROOT, capture_output=True, text=True, timeout=60, env=env)
    except Exception:
        return None
    if obj.returncode != 0:
        return None
    sha = obj.stdout.strip()
    return sha or None


def _reserve_id(n):
    """Try to claim id n by creating its tag on the remote.

    True  - the tag on origin carries OUR object, so we created it and the id is ours.
    False - the tag on origin carries somebody else's object, so they hold the id. THIS is the
            compare-and-swap, and it is decided by looking at the remote, not by reading the push.
    None  - the question could not be asked (offline, no remote, no permission).

    Two things it deliberately does NOT do, both of which it used to:

    * It does not push HEAD. See `_reservation_object()`: pushing an object the remote may already have
      turns a lost race into "Everything up-to-date", exit 0, "we won".
    * It does not classify a failed push by grepping stderr for "already exists" / "rejected" /
      "non-fast-forward". Wording is not an interface; git's phrasing, locale and hint text all move. After
      the push, the remote ref is asked what it holds, and that answer decides. The exit code is used only
      as the fallback when the remote cannot be asked a second time, and only in the direction that a
      unique object makes sound.

    Nothing is committed and no branch is touched, so this is safe to run from any worktree.
    """
    tag = f"{ID_TAG}T-{n:04d}"
    obj = _reservation_object(n)
    if obj is None:
        return None
    try:
        r = subprocess.run(["git", "push", "origin", f"{obj}:{tag}"],
                           cwd=ROOT, capture_output=True, text=True, timeout=120, env=_git_env())
    except Exception:
        r = None
    holder = _remote_ref_object(tag)
    if holder is None:
        # Could not look. Fall back to the exit code, which is sound in this one direction ONLY because
        # `obj` was invented for this call: the remote cannot have been at it already, so exit 0 cannot
        # mean "up-to-date" and can only mean "created".
        return True if (r is not None and r.returncode == 0) else None
    if holder == obj:
        return True
    if holder:
        return False
    # Asked, and the tag is not on the remote at all - so the push did not take effect and nobody holds
    # the id either. Not ours, and not somebody else's: unanswerable.
    return None


def next_id(reserve=True):
    """Allocate an id, and RESERVE it before returning, so two allocators cannot be handed the same one.

    `--reserve no` (reserve=False) is the escape hatch for an offline box. It restores the old behaviour exactly, which
    is why it prints what it is giving up rather than doing it quietly.
    """
    ids = {int(str(fm.get("id")).split("-")[1]) for _, _, fm, _ in tasks()
           if TASK_ID.match(str(fm.get("id")))} | _ids_in_refs()
    # Read the reservations ALWAYS, even with --reserve no. The escape hatch exists because a box
    # may not be able to PUSH; it does not make reading free-er to skip, and skipping it handed out
    # T-0103 while T-0103 was already reserved - measured in this task's own demo, which is the only
    # reason it is not still doing that.
    reserved = _reserved_ids()
    if reserved is None or SCAN_DEGRADED:
        why = ("the id reservations on origin could not be read" if reserved is None
               else "the remote-ref scan degraded (" + ", ".join(sorted(set(SCAN_DEGRADED))) + ")")
        if reserve:
            # REFUSE, do not warn. Warning here is what produced the third collision of 2026-09-08: the
            # message goes to stderr where an agent running a tool does not read it, the id comes back
            # looking ordinary, and queue-check cannot see the duplicate from either tree - only from the
            # merge, on a branch neither author is watching. An allocator that cannot see the other
            # allocators is not degraded, it is wrong.
            raise SystemExit(
                f"cannot allocate an id: {why}. Allocating without seeing the other allocators is what "
                f"issued T-0076, T-0088 and T-0099 twice each, so this refuses instead of warning. Fix the "
                f"remote, or pass `--reserve no` to take an id you know may collide.")
        print(f"WARNING: {why}; the id below is a guess at the maximum from this worktree alone. "
              f"task/T-0071's tree topped out at T-0075 while main was at T-0104, and that is how T-0076 "
              f"was issued twice.", file=sys.stderr)
        reserved = set()
    ids |= reserved
    n = (max(ids) + 1) if ids else 1
    if not reserve:
        print(f"WARNING: --reserve no: T-{n:04d} is NOT reserved on origin. Another agent reading right "
              f"now gets the same number, and nothing notices until the two branches merge - which is how "
              f"T-0088 and T-0099 were each issued twice.", file=sys.stderr)
        return f"T-{n:04d}"
    for _ in range(20):
        got = _reserve_id(n)
        if got is True:
            return f"T-{n:04d}"
        if got is False:
            # Somebody won the race between our read and our push. That is the mechanism working.
            print(f"T-{n:04d} was reserved by someone else between the read and the push; taking the next.",
                  file=sys.stderr)
            n += 1
            continue
        raise SystemExit(
            f"cannot reserve T-{n:04d} on origin: the push could not be made at all. Allocating without a "
            f"reservation is what issued T-0088 and T-0099 twice, so this refuses instead. Use "
            f"`--reserve no` if you accept that risk deliberately.")
    raise SystemExit(f"could not reserve an id after 20 attempts starting at T-{n - 20:04d}")


BRIEF_SECTION = re.compile(r"^##[ \t]+Brief[ \t]*$(.*?)(?=^##[ \t]|\Z)", re.M | re.S)


def brief_is_unwritten(body: str) -> bool:
    """True when the `## Brief` section carries no prose of its own.

    Matched on SHAPE, never on `cmd_new`'s placeholder wording. A check anchored on that literal sentence
    would stop firing the moment somebody rephrases it, and would report every task as fine - which is the
    failure class this repo keeps finding (the CRLF check in T-0051 could not fire at all; four decorative
    tests before it asserted things that could not fail). The property that matters is "somebody wrote
    something here", and a lone parenthetical instruction is not that.

    A missing section counts as unwritten: a task with no Brief heading has even less to be claimed against
    than one with an empty heading.
    """
    m = BRIEF_SECTION.search(body)
    if m is None:
        return True
    for raw in m.group(1).splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("(") and line.endswith(")"):
            continue          # an instruction to the author, not a brief
        return False
    return True


def log(path, msg):
    fm, body = parse(path.read_text(encoding="utf-8"))
    if "## Log" not in body:
        body = body.rstrip("\n") + "\n\n## Log\n"
    body = body.rstrip("\n") + f"\n- {iso(now())} {msg}\n"
    path.write_text(dump(fm, body), encoding="utf-8", newline="\n")


# ----------------------------------------------------------------------------- commands
def cmd_new(title, opts):
    # `state` is interpolated straight into the path this function writes, so an unchecked one is not a
    # typo, it is a traceback and a write outside queue/: `--state` with no value became queue/true/ and
    # `--state ../../../escape` resolved out of the repo. Both raised FileNotFoundError only because the
    # directory happened not to exist, which is not a guard.
    state = opts.get("state", "backlog")
    if state not in STATES:
        print(f"usage: queue.py new \"<title>\" [--state {'|'.join(STATES)}] [options]")
        print(f"refused --state {state!r}: a task file lives in one of those directories and nowhere else.")
        return 2
    # Refused here as well as in cmd_check, on T-0056's argument: after the fact is a report, at the
    # transition is a prevention. A duplicate never committed costs nothing; one that is claimed costs two
    # worktrees and a merge conflict.
    want, _ = _same_work(title, "")
    for _s, _p, _fm, _b in tasks():
        have, _ = _same_work(_fm.get("title"), "")
        if want and have == want:
            print(f"refusing: {_fm.get('id')} already has this title ({_p.relative_to(ROOT).as_posix()}).")
            print("Add to that task, or give this one a title that says how it differs.")
            return 1
    # `--reserve no` is the offline escape. A bare flag is not expressible here: every option in
    # this parser takes a value (T-0087), and inventing a flag class for one caller is worse than
    # the small ugliness of writing the word.
    reserve = str(opts.get("reserve", "yes")).strip().lower() not in ("no", "false", "0", "off")
    tid = next_id(reserve=reserve)
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48]
    fm = {
        "id": tid, "title": title, "state": state, "owner": None, "owner_session": None,
        "claimed_at": None, "lease_expires_at": None, "worktree": None, "branch": None,
        "exclusive": _list(opts.get("exclusive")), "touches": _list(opts.get("touches")),
        "pins_affected": _list(opts.get("pins")), "reviewer": None, "depends_on": _list(opts.get("depends")),
        "verify": ["ops/test", "ops/check-pins"], "acceptance": [],
    }
    body = "## Brief\n\n(what, why, and the exact demonstration that proves it — including the red run)\n\n## Log\n"
    p = Q / state / f"{tid}-{slug}.md"
    p.write_text(dump(fm, body), encoding="utf-8", newline="\n")
    print(p.relative_to(ROOT).as_posix())


def _same_work(title, body):
    """A pair of keys for "these two files are the same task".

    `title` is normalised (case, punctuation, runs of whitespace) because two agents writing the same finding
    minutes apart differ by exactly that much. `body` is hashed with the `id:` line removed, which is the only
    line new-task guarantees will differ - T-0066 and T-0067 were otherwise byte-identical.
    """
    norm = re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()
    stripped = "\n".join(l for l in (body or "").splitlines() if not l.startswith("id:"))
    return norm, hashlib.sha256(stripped.encode("utf-8")).hexdigest()


def cmd_check(_operand, _opts_):
    problems = []
    seen = {}
    by_title, by_body, _raw = {}, {}, {}
    # STRUCTURE FIRST, because P-PROC-01's whole assertion is `bash ops/queue-check >/dev/null` and an
    # unpopulated pass IS the pin passing. All three were executed green before (T-0073 route 4): an empty
    # queue/ printed QUEUE OK (0 tasks), so did deleting queue/review and queue/done, and a self-graded task
    # parked in queue/completed/ was invisible because that directory is not in STATES.
    for state in STATES:
        if not (Q / state).is_dir():
            problems.append(f"queue/{state}/ is missing - a deleted state directory silently hides every task in it")
    for d in sorted(Q.iterdir()) if Q.is_dir() else []:
        if d.is_dir() and d.name not in KNOWN_DIRS:
            problems.append(f"{d.relative_to(ROOT).as_posix()}/ is not a queue state - a task parked there is invisible")
    # LOCKS/ and _schema/ are allow-listed above, so a task file dropped in one of them would be invisible
    # for exactly the reason queue/completed/ was. A task-NAMED file only belongs in a state directory.
    for p in sorted(Q.rglob("T-*.md")) if Q.is_dir() else []:
        if p.relative_to(Q).parts[0] not in STATES and TASK_FILE.match(p.name):
            problems.append(f"{p.relative_to(ROOT).as_posix()}: a task file outside {'/'.join(STATES)}")
    for state, p, fm, _body in tasks():
        rel = p.relative_to(ROOT).as_posix()
        _raw[rel] = _body or ""
        # Asserted, not assumed: tasks() yields every file under a state dir so a mis-named one is reported
        # here instead of being hidden by the glob that used to define what counted as a task.
        if not TASK_FILE.match(p.name):
            problems.append(f"{rel}: not a task file (expected T-NNNN-slug.md) - an unnameable file is uncheckable")
        if not fm:
            problems.append(f"{rel}: no readable front matter")
            continue
        tid = fm.get("id")
        if not TASK_ID.match(str(tid)):
            problems.append(f"{rel}: id {tid!r} is not a T-NNNN task id")
            continue
        if tid in seen:
            problems.append(f"duplicate id {tid}: {rel} and {seen[tid]}")
        seen[tid] = rel
        # The id is the one field new-task GUARANTEES is unique, so the check above can never fire on
        # anything it produced. Two ids for one piece of work can, and did: T-0066 and T-0067 were
        # byte-identical apart from the id line and this printed QUEUE OK.
        nt, nb = _same_work(fm.get('title'), _raw.get(rel, ''))
        if nt:
            by_title.setdefault(nt, []).append(rel)
        by_body.setdefault(nb, []).append(rel)
        if fm.get("state") != state:
            problems.append(f"{rel}: state field '{fm.get('state')}' != directory '{state}'")
        if state in ("review", "done"):
            # P-PROC-01 is an INEQUALITY, and an inequality between two absent values is vacuously true.
            # `owner: null` with `reviewer: agent/self` passed this gate while the worker graded its own
            # work, and so did deleting the `owner:` line outright (both executed in T-0068). cmd_sweep
            # writes owner=None itself when a lease expires, so a null owner is a state this tooling
            # PRODUCES, not an exotic hand edit. Presence of both names is part of the rule.
            #
            # PRESENCE IS NOT ENOUGH (T-0073): eleven evasions supplied a truthy NON-name and sailed
            # through - `- agent/self` as a block list, `owner: "null"` in quotes, `agent/Self`. Both
            # operands go through agent() first, and a non-name fails rather than being compared.
            names = {}
            for k in ("owner", "reviewer"):
                raw = fm.get(k)
                names[k] = agent(raw)
                if names[k]:
                    continue
                if raw in (None, [], ""):
                    problems.append(f"{rel}: in {state}/ without {'an' if k == 'owner' else 'a'} {k}")
                else:
                    problems.append(f"{rel}: in {state}/ with {k}: {raw!r}, which is not an agent/<name> - "
                                    f"a non-name cannot be compared, so reviewer-is-not-owner is undecidable")
            if names["owner"] and names["owner"] == names["reviewer"]:
                problems.append(f"{rel}: reviewer == owner ({names['owner']}) - a worker may not grade its own work")
        if state == "claimed":
            for k in ("owner", "claimed_at", "lease_expires_at"):
                if not fm.get(k):
                    problems.append(f"{rel}: claimed without {k}")
            for res in fm.get("exclusive") or []:
                lock = LOCKS / f"{res}.lock"
                if not lock.exists():
                    problems.append(f"{rel}: declares exclusive [{res}] but {lock.relative_to(ROOT).as_posix()} is not held")
                elif tid not in lock.read_text(encoding="utf-8"):
                    problems.append(f"{rel}: {res}.lock is held by someone else")
    # locks held by non-claimed tasks
    if LOCKS.is_dir():
        claimed_ids = {fm.get("id") for s, _, fm, _ in tasks() if s == "claimed"}
        for lock in LOCKS.glob("*.lock"):
            holder = lock.read_text(encoding="utf-8").strip().split()[0] if lock.read_text(encoding="utf-8").strip() else "?"
            if holder not in claimed_ids:
                problems.append(f"{lock.relative_to(ROOT).as_posix()} held by {holder}, which is not in claimed/")
    # dependencies of ready tasks must exist
    ids = set(seen)
    for state, p, fm, _ in tasks():
        for dep in fm.get("depends_on") or []:
            if dep not in ids:
                problems.append(f"{p.relative_to(ROOT).as_posix()}: depends_on {dep} which does not exist")
    # THE FLOOR. Everything above is decoration if the population can be emptied. 69 tasks live here today,
    # so a run seeing fewer than MIN_TASKS is looking at a truncated tree, not a queue that shrank; the
    # floor sits far below the real count because it exists to catch "inspected nothing", not to track the
    # queue. It is a constant here and not pins/floor_queue.txt: that path is serial-only (CLAUDE.md) and
    # this task declares no exclusive lock.
    for key, paths in sorted(by_body.items()):
        if len(paths) > 1:
            problems.append(f"{len(paths)} tasks share one brief (identical but for the id line): "
                            + ", ".join(paths))
    for key, paths in sorted(by_title.items()):
        # Reported separately from the body match: two briefs that diverged after being filed twice
        # still describe one piece of work, and that is the state worth catching before either is claimed.
        if len(paths) > 1 and not any(set(paths) <= set(q) for q in by_body.values() if len(q) > 1):
            problems.append(f"{len(paths)} tasks share one title: " + ", ".join(paths))
    if len(seen) < MIN_TASKS:
        problems.append(f"only {len(seen)} task(s) visible, floor is {MIN_TASKS} - a queue-check that "
                        f"inspected nothing still reports success, and that IS P-PROC-01 passing")
    if problems:
        print("QUEUE CHECK FAIL")
        for pr in problems:
            print(" -", pr)
        return 1
    print(f"QUEUE OK ({len(seen)} tasks)")
    return 0


def _git_usable():
    """Can git answer questions about this repo at all?

    Asked once, before anything is swept, because every guard below is a git query and a git that cannot read
    the worktree would answer "no such branch" to all of them - which is indistinguishable from "abandoned"
    and is exactly the wrong default. From WSL against a Windows worktree this is a real state, not a
    hypothetical: the .git file says `gitdir: C:/...` and WSL's git cannot follow it (T-0055).
    """
    try:
        r = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=ROOT,
                           capture_output=True, text=True, timeout=30)
        return r.returncode == 0
    except Exception:
        return False


def _branch_exists(name):
    """True when this task's branch is real - here or on the remote.

    Deliberately checks the remote-tracking ref FIRST: the case this exists for is work that was pushed and is
    waiting on a merge, which is visible as origin/<branch> even in a worktree that never had the local
    branch. No fetch is done - a sweeper that reaches the network is a sweeper nobody runs - so a branch
    pushed by someone else since the last fetch reads as absent. That direction is safe: it can only make the
    sweeper more conservative if the ref is stale in the other direction, and `git fetch` before sweeping is
    one line in the caller.
    """
    if not name or str(name).strip() in ("", "null", "none", "~"):
        return False
    for ref in (f"refs/remotes/origin/{name}", f"refs/heads/{name}"):
        try:
            r = subprocess.run(["git", "rev-parse", "--verify", "-q", ref], cwd=ROOT,
                               capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                return True
        except Exception:
            return True   # cannot tell -> assume the work is real. Never sweep on a failed query.
    return False


def cmd_sweep(_operand, _opts_):
    moved = 0
    # A lease says an agent stopped working. It does not say the work is gone, and this queue keeps finished
    # work in claimed/ until it MERGES - so on 2026-09-08, 29 of 29 expired leases belonged to pushed branches
    # with open PRs. Sweeping them would have set owner: None on all 29 (the state T-0068 exists to reject,
    # and which this very function produces), and left main saying ready/<id> while each branch says review/ or
    # done/ - the add/add divergence eleven branches had already been repaired by hand for.
    if not _git_usable():
        print("SWEEP REFUSED: git cannot read this repo, so 'has this task got a branch?' cannot be answered.")
        print("  Every expired lease would look abandoned and be swept. Run this where git works.")
        return 2
    held = []
    for state, p, fm, _ in list(tasks()):
        if state != "claimed" or not fm.get("lease_expires_at"):
            continue
        exp = dt.datetime.fromisoformat(fm["lease_expires_at"].replace("Z", "+00:00"))
        if exp < now():
            if _branch_exists(fm.get("branch")):
                held.append(f"{fm['id']} (branch {fm.get('branch')} exists)")
                continue
            for res in fm.get("exclusive") or []:
                lock = LOCKS / f"{res}.lock"
                if lock.exists() and fm["id"] in lock.read_text(encoding="utf-8"):
                    lock.unlink()
            owner = fm.get("owner")
            fm.update(state="ready", owner=None, owner_session=None, claimed_at=None, lease_expires_at=None, worktree=None)
            dest = Q / "ready" / p.name
            dest.write_text(dump(fm, parse(p.read_text(encoding="utf-8"))[1]), encoding="utf-8", newline="\n")
            p.unlink()
            log(dest, f"sweep: lease held by {owner} expired at {iso(exp)}; returned to ready/, locks released")
            print(f"swept {fm['id']} -> ready/")
            moved += 1
    if held:
        print(f"SWEEP kept {len(held)} expired lease(s) whose branch still exists - finished work waiting to")
        print("  merge is not an abandoned task, and clearing its owner would break the reviewer-is-not-owner")
        print("  rule it will be checked against later:")
        for h in held:
            print(f"    {h}")
    print(f"SWEEP done ({moved} moved, {len(held)} kept)")
    return 0


def cmd_next(_operand, _opts_):
    done = {fm.get("id") for s, _, fm, _ in tasks() if s == "done"}
    for state, p, fm, _ in tasks():
        if state != "ready":
            continue
        if all(d in done for d in (fm.get("depends_on") or [])):
            print(fm.get("id"), "-", fm.get("title"))
            return 0
    print("(no unblocked ready task)")
    return 0


def cmd_claim(tid, opts):
    owner = opts.get("owner") or "agent/unknown"
    hours = _hours(opts.get("hours", "2"))
    if hours is None:
        print("usage: queue.py claim <id> [--owner NAME] [--session ID] [--worktree PATH] [--hours N]")
        print(f"refused --hours {opts.get('hours')!r}: a lease is a positive number of hours under a year.")
        return 2
    for state, p, fm, body in tasks():
        if fm.get("id") != tid:
            continue
        if state != "ready":
            print(f"{tid} is in {state}/, not ready/")
            return 1
        # Refuse a task nobody has written a brief for. Ten task files in this tree still carried cmd_new's
        # placeholder verbatim when this was added, and one of them - T-0011 - was in queue/done/: signed off
        # by a reviewer against acceptance criteria that were never written down. An unwritten brief cannot
        # be argued with, so the work cannot be wrong, which is the same thing as it not being checked.
        #
        # Enforced HERE rather than in cmd_check on purpose: eight of those ten are stale copies on main
        # whose real briefs live on unmerged branches, so a queue-check rule would fail the gate for everyone
        # until an unrelated billing block clears (T-0053). Claim time is the last moment the failure can
        # still be prevented, and it cannot be tripped by somebody else's in-flight work.
        if brief_is_unwritten(body):
            print(f"{tid} has no brief - the ## Brief section is empty or still the placeholder.")
            print("Write it, commit it, then claim. What the change is, why, and the exact demonstration")
            print("that proves it, including the red run. A task nobody wrote a brief for is a task whose")
            print("acceptance nobody can argue with.")
            return 1
        held = []
        for res in fm.get("exclusive") or []:
            lock = LOCKS / f"{res}.lock"
            if lock.exists():
                held.append(f"{res} (held: {lock.read_text(encoding='utf-8').strip()})")
        if held:
            print("cannot claim, locks held:", "; ".join(held))
            return 1
        t = now()
        fm.update(state="claimed", owner=owner, owner_session=opts.get("session"), claimed_at=iso(t),
                  lease_expires_at=iso(t + dt.timedelta(hours=hours)),
                  worktree=opts.get("worktree"), branch=f"task/{tid}")
        LOCKS.mkdir(exist_ok=True)
        for res in fm.get("exclusive") or []:
            (LOCKS / f"{res}.lock").write_text(f"{tid} {owner} {iso(t)}\n", encoding="utf-8", newline="\n")
        dest = Q / "claimed" / p.name
        dest.write_text(dump(fm, body), encoding="utf-8", newline="\n")
        p.unlink()
        log(dest, f"claimed by {owner}; lease until {fm['lease_expires_at']}")
        print(f"claimed {tid} -> {dest.relative_to(ROOT).as_posix()}  (now: git add queue/ && git commit && git push - a rejected push means someone else claimed it)")
        return 0
    print(f"{tid} not found")
    return 1


def _git(*args):
    """(ok, stdout). ok is False for a failed command AND for a git that cannot run at all - the caller must
    treat those the same, because "I could not ask" and "the answer is no" lead to opposite actions here."""
    try:
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=30)
        return r.returncode == 0, r.stdout.strip()
    except Exception:
        return False, ""


def _main_ref():
    for ref in ("refs/remotes/origin/main", "refs/heads/main"):
        ok, _ = _git("rev-parse", "--verify", "-q", ref)
        if ok:
            return ref
    return None


def _would_duplicate_on_merge(tid):
    """Paths where main holds `tid` that THIS BRANCH CANNOT DELETE. None when git cannot answer.

    A branch deletes a file by recording a deletion against a base that has it. `ops/claim` moves
    ready/ -> claimed/ on MAIN; a stacked worktree is cut from another task branch whose base predates that
    claim, so the branch does not contain the commit that created claimed/<id>. Whatever it writes, main's
    copy is an independent add and survives the merge - both exist, `queue-check` fails on the merged tree
    only, and eleven branches were repaired by hand for exactly this.

    Note the test is on HISTORY, not on the working tree. A branch that WROTE a file at main's path still has
    a file there; it just shares no history with main's copy, so git keeps both. Asking "does the path exist"
    answers yes and misses the defect - measured, in this task's first attempt.
    """
    ref = _main_ref()
    if ref is None:
        return None
    ok, out = _git("ls-tree", "-r", "--name-only", ref, "queue/")
    if not ok:
        return None
    bad = []
    for path in (l.strip() for l in out.splitlines()):
        if f"/{tid}-" not in path:
            continue
        ok, commit = _git("rev-list", "-1", ref, "--", path)
        if not ok or not commit:
            return None
        reachable, _ = _git("merge-base", "--is-ancestor", commit, "HEAD")
        if not reachable:
            bad.append(path)
    return bad


def cmd_review(tid, opts):
    """Move a CLAIMED task to review/, assign its reviewer, and release the locks it holds.

    The transition existed only as a habit: every agent did `git mv` plus a hand edit of `state:` and
    `reviewer:`. Because there was no code path at the moment the work stops, nothing ever released the
    `exclusive:` locks `claim` had taken - and `cmd_check` treats an orphaned lock as an error, so the first
    task to carry a lock into review/ would have started failing `ops/queue-check` for every agent in every
    worktree, not just its own owner. One lock exists today: scenic-index, held by T-0024, still claimed.

    Releasing at review rather than at done is the judgement here. A task sitting in review is not editing
    the resource it locked, and review takes hours or days, so holding `scenic-index` or `prod` that long
    starves everyone. The objection is that a FAIL sends it back to the owner - and the answer is `ops/lock`,
    which already exists to acquire the locks a claimed task declares. The round trip is supported, so this
    is not a one-way door.
    """
    for state, p, fm, body in tasks():
        if fm.get("id") != tid:
            continue
        if state != "claimed":
            print(f"{tid} is in {state}/, not claimed/")
            return 1
        reviewer_raw = opts.get("reviewer") or fm.get("reviewer")
        if not reviewer_raw:
            print(f"{tid} needs a reviewer: ops/review {tid} --reviewer agent/<name>")
            return 1
        # Refused here as well as in cmd_check, on the same argument as T-0056's brief guard: after the fact
        # is a report, at the transition is a prevention.
        #
        # The owner must EXIST before that comparison means anything: `reviewer != None` is true for every
        # reviewer alive, so an ownerless task hands itself to itself and this gate says nothing. T-0068
        # executed it - `owner: null` and a deleted `owner:` line both walked a self-review into review/.
        owner_raw = fm.get("owner")
        if not owner_raw:
            print(f"{tid} has no owner, so 'the reviewer is not the owner' cannot be decided - a null owner")
            print("satisfies that inequality for every reviewer. Restore owner: before handing it over")
            print("(ops/queue-sweep clears owner: when a lease expires; re-claim with ops/claim).")
            return 1
        # Present is not the same as comparable (T-0073): a `- agent/self` block list is truthy and
        # != 'agent/self'; `owner: "null"` is the truthy STRING 'null', which dump() then wrote back as a
        # real null, so this guard MANUFACTURED the state it exists to refuse; `--reviewer` with no value
        # made the reviewer 'true'. Refuse a non-name outright rather than compare it.
        owner, reviewer = agent(owner_raw), agent(reviewer_raw)
        for label, norm, raw in (("owner", owner, owner_raw), ("reviewer", reviewer, reviewer_raw)):
            if not norm:
                print(f"{tid}: {label} is {raw!r}, which is not an agent/<name>. A non-name cannot be")
                print("compared, so 'the reviewer is not the owner' cannot be decided - a list, a quoted")
                print("\"null\" and a bare flag all read as present while meaning nothing.")
                return 1
        if reviewer == owner:
            print(f"reviewer {reviewer_raw} is also the owner of {tid} - a worker may not grade its own work")
            return 1

        # THE MERGE STATE, checked before anything moves, because it is the only defect here that no check
        # running on the branch or on main can see - it exists solely in the merged tree.
        #
        # Refused, not silently repaired: `git merge origin/main` inside a state transition is a
        # history-changing act hidden in a rename, and it would swallow a genuine duplicate created some other
        # way. The refusal prints the two commands and costs one run.
        dup = _would_duplicate_on_merge(tid)
        if dup is None:
            print(f"{tid}: cannot read main, so whether merging this branch would duplicate the task file")
            print("cannot be decided. Refusing rather than guessing - a wrong guess is invisible until the")
            print("merge. Fetch, or run this where git can read the repo.")
            return 1
        if dup:
            print(f"{tid}: main holds this task where this branch cannot delete it:")
            for m in dup:
                print(f"    {m}")
            print("This branch does not contain the commit that put the file there, so it has no deletion to")
            print("record. Merging leaves BOTH that copy and queue/review/ - ops/queue-check then fails on the")
            print("merged tree while passing here and on main, which is why no per-branch CI ever caught it.")
            print()
            print("    git merge origin/main")
            for m in dup:
                print(f"    git rm {m}")
            print()
            print("then run this again. (T-0063; this repair was applied by hand to eleven branches.)")
            return 1

        # Inspect every lock BEFORE unlinking any of them, so a foreign lock cannot leave the task half
        # released - the same reason ops/claim checks all resources before taking the first.
        mine, foreign = [], []
        for res in fm.get("exclusive") or []:
            lock = LOCKS / f"{res}.lock"
            if not lock.exists():
                continue
            holder = lock.read_text(encoding="utf-8").strip()
            # Only ever release OUR OWN lock. One naming a different task is somebody else's, and taking it
            # over silently is the exact collision these locks exist to prevent.
            if holder.split()[:1] == [tid]:
                mine.append((res, lock))
            else:
                foreign.append(f"{res} (held by {holder})")
        if foreign:
            print(f"{tid} declares exclusive resources locked by someone else: {'; '.join(foreign)}")
            print("Nothing was released and the task did not move. ops/queue-check reports this state.")
            return 1
        for _, lock in mine:
            lock.unlink()
        released = [res for res, _ in mine]

        # The NORMALISED name is persisted on purpose, so `agent/Self` cannot be stored and later re-read
        # as something different from its owner.
        fm.update(state="review", reviewer=reviewer)
        dest = Q / "review" / p.name
        dest.write_text(dump(fm, body), encoding="utf-8", newline="\n")
        p.unlink()
        note = f"handed to {reviewer}; state -> review"
        if released:
            note += f"; released lock(s) {', '.join(released)}"
        log(dest, note)
        print(f"{tid} -> {dest.relative_to(ROOT).as_posix()}  reviewer={reviewer}  "
              f"released=[{', '.join(released) or 'none'}]")
        print("(now: git add queue/ && git commit && git push)")
        return 0
    print(f"{tid} not found")
    return 1


def cmd_lock(tid, opts):
    """Acquire the locks a CLAIMED task declares but does not hold.

    `claim` creates every declared lock, but a task whose `exclusive:` list is edited AFTER it was claimed
    has no lock and no way to get one. That happened on T-0011 (exclusive: [floors] added post-claim);
    queue-check caught it, but only after the window in which a concurrent write could have been lost.
    """
    for state, p, fm, _ in tasks():
        if fm.get("id") != tid:
            continue
        if state != "claimed":
            print(f"{tid} is in {state}/, not claimed/ - only a claimed task holds locks")
            return 1
        owner = opts.get("owner") or fm.get("owner") or "agent/unknown"
        if fm.get("owner") and owner != fm.get("owner"):
            print(f"{tid} is owned by {fm['owner']}, not {owner}")
            return 1
        wanted = fm.get("exclusive") or []
        if not wanted:
            print(f"{tid} declares no exclusive resources")
            return 0
        LOCKS.mkdir(exist_ok=True)
        taken, already = [], []
        for res in wanted:
            lock = LOCKS / f"{res}.lock"
            if lock.exists():
                holder = lock.read_text(encoding="utf-8").strip()
                if not holder.startswith(tid):
                    print(f"cannot lock {res}: held by {holder}")
                    return 1
                already.append(res)
            else:
                taken.append(res)
        for res in taken:
            (LOCKS / f"{res}.lock").write_text(f"{tid} {owner} {iso(now())}\n", encoding="utf-8", newline="\n")
        if taken:
            log(p, f"acquired lock(s) {', '.join(taken)} for {owner}")
        print(f"{tid}: acquired [{', '.join(taken) or 'none'}]" + (f", already held [{', '.join(already)}]" if already else ""))
        return 0
    print(f"{tid} not found")
    return 1


def _opts(argv, cmd):
    """(options, None), or (None, why-this-command-line-cannot-be-obeyed).

    Every failure this refuses used to be SILENT, which is worse than the traceback T-0087 started from: a
    stack trace at least stops. The old parser wrote `out[name] = value` into a dict nobody validated:

      --touchez a                 set a key no caller reads; the task recorded touches: []
      --touches a --touches b     kept only `b` - T-0084, measured on four live branches
      --touches --state done      recorded touches: ['--state'] and dropped --state entirely
      --owner x --owner y         claimed for `y`, last-wins, with nothing printed
      claim T-1 T-2               ignored the second word

    List options ACCUMULATE, because `--touches a --touches b` has exactly one meaning. A repeated SCALAR
    is refused instead of resolved: which of two `--owner`s was meant is not knowable from here, and the
    old answer (the last) is the one an agent re-reading its own command line is least likely to expect.
    """
    out, seen = {}, set()
    i = 0
    while i < len(argv):
        tok = argv[i]
        if not tok.startswith("--"):
            takes = f"one operand ({NEEDS_ARG[cmd]}) then options" if cmd in NEEDS_ARG else "no operand"
            return None, f"{tok!r} is not an option. `{cmd}` takes {takes}, and a stray word was ignored."
        name, eq, inline = tok[2:].partition("=")
        if name not in OPTS[cmd]:
            known = ", ".join("--" + o for o in sorted(OPTS[cmd])) or "it takes none"
            return None, f"--{name} is not an option of `{cmd}` ({known})."
        if eq:
            val = inline
        else:
            i += 1
            if i >= len(argv):
                return None, f"--{name} needs a value; it was the last word on the line."
            val = argv[i]
            # (the DASHES and empty checks live below, outside this branch - see there for why)
            # A value starting with a dash is the NEXT OPTION, eaten. Guarded on the whole DASHES class for
            # the same reason the operand is: an ASCII-only version of this test is one keystroke from
            # useless. No option here takes a dash-leading value.
        # BOTH checks below sit outside the `if eq:` split on purpose. The DASHES guard used to live only in
        # this branch, so `--touches=--state` walked straight past it and recorded `touches: [--state]` while
        # the identical `--touches --state` was refused - one step past the self-attack that found `=` bypasses
        # this parser at all. Two spellings of one option must take one path.
        if val[:1] and val[0] in DASHES:
            return None, f"--{name} was given {val!r}, which is another option, not a value."
        # An EMPTY value is a supplied flag whose value was thrown away, which is the same silence one
        # scale down and it survived the first version of this guard: `claim T-1 --owner=` and
        # `--owner ""` both claimed the task for agent/unknown, exit 0, nothing printed. No option here
        # has a meaningful empty value - `_list("")` is [], and every scalar is a name, a path or a number.
        # Test the PARSED value, not the raw string. The comment above states the right criterion -
        # "`_list("")` is []" - and `if not val.strip()` shipped a weaker one: `_list(",")` is ALSO [], and a
        # comma survives .strip(). `--touches ,`, `--exclusive ,,,` and `--depends " , "` were each accepted
        # with exit 0, recorded an empty list, and printed nothing - verbatim the silence this guard removes.
        empty = (not _list(val)) if name in LIST_OPTS else (not val.strip())
        if empty:
            return None, (f"--{name} was given {val!r}, which parses to nothing; drop the flag or give it a "
                          f"value.")
        if name in LIST_OPTS:
            out.setdefault(name, []).append(val)
        elif name in seen:
            return None, (f"--{name} was given twice ({out[name]!r} then {val!r}); it holds one value and "
                          "which one was meant is not knowable here.")
        else:
            out[name] = val
        seen.add(name)
        i += 1
    return out, None


def _hours(v):
    """A lease length in hours, or None when the string cannot be one.

    Three tracebacks lived in this one argument: `--hours` with no value parses as "true" (ValueError out
    of float), and `inf`/`nan` got past float() to blow up inside dt.timedelta. `-5` raised nothing at all
    - it claimed the task with a lease that had already expired, which queue-sweep hands to the next agent.
    The range rejects all four; every comparison against nan is False.
    """
    try:
        h = float(v)
    except (TypeError, ValueError):
        return None
    return h if 0 < h < 24 * 365 else None


def _list(v):
    """A list option's value: comma-separated (`--touches a,b`), repeated (`--touches a --touches b`),
    or both. The comma spelling was the only one that ever worked and it is documented nowhere an agent
    reads, which is how T-0084's four tasks came to declare one path out of several."""
    return [x.strip() for part in (v if isinstance(v, list) else [v]) if part
            for x in str(part).split(",") if x.strip()]


# subcommand -> options it accepts. The dispatch reads this, so a command added without a line here is a
# KeyError at parse time rather than a command that quietly accepts anything - COMMANDS is derived from it
# so the two cannot drift. Names in LIST_OPTS accumulate across repeats; every other name is scalar and a
# repeat is refused.
LIST_OPTS = frozenset({"touches", "exclusive", "pins", "depends"})
OPTS = {
    "new": frozenset({"state", "touches", "exclusive", "pins", "depends", "reserve"}),
    "check": frozenset(),
    "sweep": frozenset(),
    "next": frozenset(),
    "claim": frozenset({"owner", "session", "worktree", "hours"}),
    "lock": frozenset({"owner"}),
    "review": frozenset({"reviewer"}),
}
COMMANDS = tuple(OPTS)
# subcommand -> the operand it reads, for the usage line. `new` takes a title, not an id.
NEEDS_ARG = {"new": '"<title>"', "claim": "<id>", "lock": "<id>", "review": "<id>"}
# Every dash that a keyboard, an autocorrect or a pasted document can leave where '-' was meant. The first
# version of the guard below said "may not start with '-'" and was defeated by the neighbouring character
# in one line: `new '--touches' ops/lib/queue.py` typed with EN DASHES still wrote a task titled "--touches".
DASHES = "-\u00ad\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uff0d"


def _bad_operand(cmd, got):
    """Why `got` cannot be cmd's first operand, or None when it can. Anchored on TASK_ID, not on shape
    guesswork: for claim/lock/review the operand is an id, and an id is exactly T- and four digits."""
    if not got.strip():
        return "the operand comes first and may not be blank."
    if got.strip()[0] in DASHES:
        return "that is an option, not an operand - the operand comes first."
    if cmd != "new" and not TASK_ID.match(got):
        return "a task id is 'T-' and four digits."
    return None


def _usage(cmd):
    """Built from OPTS, so a usage line cannot describe a command the parser no longer implements - a
    hand-written one drifts, and a wrong usage line is worse than none because it is believed."""
    flags = " ".join(f"[--{o} V]" for o in sorted(OPTS[cmd]))
    return " ".join(x for x in ("usage: queue.py", cmd, NEEDS_ARG.get(cmd, ""), flags) if x)


def main(argv):
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print(__doc__)
        return 2
    cmd, rest = argv[1], list(argv[2:])
    # These four read rest[0] directly, so calling one with no argument raised IndexError and printed a
    # traceback instead of usage. Found while adding `review`; `claim`, `lock` and `new` have had it since
    # they were written. A tool that answers a typo with a stack trace teaches people to stop reading its
    # output, which is expensive in a repo whose whole premise is that output gets read.
    #
    # Counting the arguments is not enough. The count-only version of this guard was defeated by the next
    # mistake along: `new --touches ops/lib/queue.py` has three arguments, so it passed, and cmd_new wrote
    # queue/backlog/T-0088-touches.md TITLED "--touches"; `new ""` and `new "   "` wrote task files with an
    # empty title and an empty slug. Silent garbage in the queue is worse than a stack trace, because
    # nobody reads queue/backlog until they need it.
    #
    # The OPTIONS are the neighbouring half and were open until T-0084 was folded in here: guarding the
    # operand and then handing the rest to a parser that validates nothing moves the silence one word to
    # the right. Both halves are decided BEFORE any cmd_* runs, so a refusal cannot half-write a task file.
    operand = None
    if cmd in NEEDS_ARG:
        operand = rest[0] if rest else ""
        why = _bad_operand(cmd, operand)
        if why:
            print(_usage(cmd))
            print(f"refused {operand!r}: {why}")
            return 2
        rest = rest[1:]
    opts, why = _opts(rest, cmd)
    if why:
        print(_usage(cmd))
        print(f"refused: {why}")
        return 2
    return globals()[f"cmd_{cmd}"](operand, opts) or 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
