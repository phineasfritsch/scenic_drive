#!/usr/bin/env python3
"""Repo work queue. State IS the directory; every transition is a git commit (and a push, for claims).

  queue.py new "<title>" [--touches a,b] [--exclusive x,y] [--depends T-0001,...] [--state backlog|ready]
  queue.py check              exit 1 on any protocol violation (reviewer == owner, review/ without reviewer, ...)
  queue.py sweep              move expired claimed/ tasks back to ready/, release their LOCKS, append to ## Log
  queue.py review ID --reviewer NAME   claimed/ -> review/, assign the reviewer, release its LOCKS
  queue.py next               print the next unblocked ready/ task id
  queue.py claim T-0007 --owner agent/x --session <id> [--worktree ../wt/T-0007] [--hours 2]
  queue.py lock T-0007 [--owner agent/x]   acquire locks a claimed task declares but does not hold

No PyYAML: front matter is parsed by a deliberately small reader (scalars, [flow, lists], and `- ` block lists).
"""
import datetime as dt
import os
import hashlib
import re
import subprocess
import sys
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


def dump(fm, body):
    lines = ["---"]
    for k, v in fm.items():
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


def _ids_in_refs():
    """Task ids visible on every remote-tracking branch, not just this worktree.

    Without this, two branches allocate the same id: T-0015 was created on task/T-0007 and again on
    task/T-0011 because the first was pushed but unmerged, and `queue-check` only notices once both land.
    Scanning remote refs catches every id that has been pushed. Two agents allocating offline at the same
    instant can still collide - the push is the compare-and-swap that settles that, exactly as for claims.
    """
    ids = set()

    def warn(what, detail):
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


def next_id():
    ids = {int(str(fm.get("id")).split("-")[1]) for _, _, fm, _ in tasks()
           if TASK_ID.match(str(fm.get("id")))} | _ids_in_refs()
    return f"T-{(max(ids) + 1 if ids else 1):04d}"


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
def cmd_new(argv):
    title = argv[0]
    opts = _opts(argv[1:])
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
    tid = next_id()
    state = opts.get("state", "backlog")
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
    minutes apart differ by exactly that much. `body` is the text after the front matter, hashed whole -
    T-0066 and T-0067 were byte-identical there. An UNWRITTEN body is never compared; see cmd_check.
    """
    norm = re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()
    # The body is the text AFTER the front matter, so it never contains an `id:` line: the filter that
    # used to sit here was dead, and the message it fed said "identical but for the id line", which was
    # false in both directions. Reported by the reviewer of PR #50.
    return norm, hashlib.sha256((body or "").encode("utf-8")).hexdigest()


def cmd_check(_argv):
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
        else:
            # An empty-normalising title exempted a task from the duplicate check entirely, so two files
            # for one finding passed green by having no usable title at all.
            problems.append(f"{rel}: title {fm.get('title')!r} normalises to nothing, so it cannot be "
                            "compared against any other task")
        # An UNWRITTEN brief is not evidence of duplicated work: ops/new-task writes the same placeholder
        # into every task it creates, so hashing it made any two fresh tasks a duplicate pair. Measured on
        # task/T-0040 - `QUEUE OK (61 tasks)` became QUEUE CHECK FAIL naming T-0032, T-0033 and T-0034,
        # three unrelated tasks whose only shared text was the template, and three real pushed branches
        # regressed from exit 0 to exit 1. Found by an independent reviewer of PR #50.
        # brief_is_unwritten() matches on SHAPE (T-0056), so this does not re-anchor on the placeholder
        # wording: rephrasing the template cannot silently switch the guard off.
        if not brief_is_unwritten(_raw.get(rel, '')):
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
            problems.append(f"{len(paths)} tasks share one written brief: "
                            + ", ".join(paths))
    for key, paths in sorted(by_title.items()):
        # Reported separately from the body match: two briefs that diverged after being filed twice
        # still describe one piece of work, and that is the state worth catching before either is claimed.
        # Only suppress when this EXACT set was already reported as a shared brief. The subset test let any
        # superset body group silence a real title duplicate, naming an innocent third task instead.
        if len(paths) > 1 and not any(set(paths) == set(q) for q in by_body.values() if len(q) > 1):
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


def cmd_sweep(_argv):
    moved = 0
    for state, p, fm, _ in list(tasks()):
        if state != "claimed" or not fm.get("lease_expires_at"):
            continue
        exp = dt.datetime.fromisoformat(fm["lease_expires_at"].replace("Z", "+00:00"))
        if exp < now():
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
    print(f"SWEEP done ({moved} moved)")
    return 0


def cmd_next(_argv):
    done = {fm.get("id") for s, _, fm, _ in tasks() if s == "done"}
    for state, p, fm, _ in tasks():
        if state != "ready":
            continue
        if all(d in done for d in (fm.get("depends_on") or [])):
            print(fm.get("id"), "-", fm.get("title"))
            return 0
    print("(no unblocked ready task)")
    return 0


def cmd_claim(argv):
    tid = argv[0]
    opts = _opts(argv[1:])
    owner = opts.get("owner") or "agent/unknown"
    hours = float(opts.get("hours", "2"))
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


def cmd_review(argv):
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
    tid = argv[0]
    opts = _opts(argv[1:])
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


def cmd_lock(argv):
    """Acquire the locks a CLAIMED task declares but does not hold.

    `claim` creates every declared lock, but a task whose `exclusive:` list is edited AFTER it was claimed
    has no lock and no way to get one. That happened on T-0011 (exclusive: [floors] added post-claim);
    queue-check caught it, but only after the window in which a concurrent write could have been lost.
    """
    tid = argv[0]
    opts = _opts(argv[1:])
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


def _opts(argv):
    out = {}
    i = 0
    while i < len(argv):
        if argv[i].startswith("--"):
            out[argv[i][2:]] = argv[i + 1] if i + 1 < len(argv) else "true"
            i += 2
        else:
            i += 1
    return out


def _list(v):
    return [x.strip() for x in v.split(",") if x.strip()] if v else []


COMMANDS = ("new", "check", "sweep", "next", "claim", "lock", "review")
NEEDS_ARG = ("new", "claim", "lock", "review")


def main(argv):
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print(__doc__)
        return 2
    # These four read argv[0] directly, so calling one with no argument raised IndexError and printed a
    # traceback instead of usage. Found while adding `review`; `claim`, `lock` and `new` have had it since
    # they were written. A tool that answers a typo with a stack trace teaches people to stop reading its
    # output, which is expensive in a repo whose whole premise is that output gets read.
    if argv[1] in NEEDS_ARG and len(argv) < 3:
        print(f"usage: queue.py {argv[1]} <id> [options]")
        return 2
    return globals()[f"cmd_{argv[1]}"](argv[2:]) or 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
