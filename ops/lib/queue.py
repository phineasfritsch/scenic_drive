#!/usr/bin/env python3
"""Repo work queue. State IS the directory; every transition is a git commit (and a push, for claims).

  queue.py new "<title>" [--touches a,b] [--exclusive x,y] [--depends T-0001,...] [--state backlog|ready]
  queue.py check              exit 1 on any protocol violation (reviewer == owner, review/ without reviewer, ...)
  queue.py sweep              move expired claimed/ tasks back to ready/, release their LOCKS, append to ## Log
  queue.py next               print the next unblocked ready/ task id
  queue.py claim T-0007 --owner agent/x --session <id> [--worktree ../wt/T-0007] [--hours 2]
  queue.py lock T-0007 [--owner agent/x]   acquire locks a claimed task declares but does not hold

No PyYAML: front matter is parsed by a deliberately small reader (scalars, [flow, lists], and `- ` block lists).
"""
import datetime as dt
import os
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
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n" + body.lstrip("\n")


# ----------------------------------------------------------------------------- helpers
def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def iso(t):
    return t.isoformat().replace("+00:00", "Z")


def tasks():
    """yield (state, path, fm, body) for every task file."""
    for state in STATES:
        d = Q / state
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("T-*.md")):
            fm, body = parse(p.read_text(encoding="utf-8"))
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
    ids = {int(fm["id"].split("-")[1]) for _, _, fm, _ in tasks()} | _ids_in_refs()
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


def cmd_check(_argv):
    problems = []
    seen = {}
    for state, p, fm, _ in tasks():
        rel = p.relative_to(ROOT).as_posix()
        tid = fm.get("id")
        if tid in seen:
            problems.append(f"duplicate id {tid}: {rel} and {seen[tid]}")
        seen[tid] = rel
        if fm.get("state") != state:
            problems.append(f"{rel}: state field '{fm.get('state')}' != directory '{state}'")
        if state in ("review", "done"):
            if not fm.get("reviewer"):
                problems.append(f"{rel}: in {state}/ without a reviewer")
            elif fm.get("reviewer") == fm.get("owner"):
                problems.append(f"{rel}: reviewer == owner ({fm.get('owner')}) - a worker may not grade its own work")
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
        if state == "done":
            for dep in fm.get("depends_on") or []:
                pass  # done tasks may reference anything
    # locks held by non-claimed tasks
    if LOCKS.is_dir():
        claimed_ids = {fm["id"] for s, _, fm, _ in tasks() if s == "claimed"}
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
    done = {fm["id"] for s, _, fm, _ in tasks() if s == "done"}
    for state, p, fm, _ in tasks():
        if state != "ready":
            continue
        if all(d in done for d in (fm.get("depends_on") or [])):
            print(fm["id"], "-", fm["title"])
            return 0
    print("(no unblocked ready task)")
    return 0


def cmd_claim(argv):
    tid = argv[0]
    opts = _opts(argv[1:])
    owner = opts.get("owner") or "agent/unknown"
    hours = float(opts.get("hours", "2"))
    for state, p, fm, body in tasks():
        if fm["id"] != tid:
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


def cmd_lock(argv):
    """Acquire the locks a CLAIMED task declares but does not hold.

    `claim` creates every declared lock, but a task whose `exclusive:` list is edited AFTER it was claimed
    has no lock and no way to get one. That happened on T-0011 (exclusive: [floors] added post-claim);
    queue-check caught it, but only after the window in which a concurrent write could have been lost.
    """
    tid = argv[0]
    opts = _opts(argv[1:])
    for state, p, fm, _ in tasks():
        if fm["id"] != tid:
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


def main(argv):
    if len(argv) < 2 or argv[1] not in ("new", "check", "sweep", "next", "claim", "lock"):
        print(__doc__)
        return 2
    return globals()[f"cmd_{argv[1]}"](argv[2:]) or 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
