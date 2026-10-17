#!/usr/bin/env python3
"""T-0392 (P-COST-03, source half): the routing box answers only the Worker, and only on what the Worker sends.

    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-routing-front-door.py
    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-routing-front-door.py --prove-red

A WHITELIST over services/routing/Caddyfile and services/routing/compose.yaml, never a list of bad spellings:
  * every `reverse_proxy` sits in a `handle @m` whose matcher @m is EXACTLY: the secret header equal to
    {env.ROUTER_SECRET}, the README placeholder refused, one method, one path - and the (method, path) pairs over
    all of them are exactly the Worker's: POST /route, GET /isochrone, GET /info. Each such handle strips the
    secret header and proxies to graphhopper:8989 and nothing else;
  * the last top-level handle is the catch-all `respond 404`; the global block says `admin off`; no `log`;
  * compose has exactly the services graphhopper (built here, no ports, internal network only, running the
    server main on config.yml) and front (caddy by @sha256 digest, ROUTER_SECRET only from the environment with
    `:?`); the internal network is `internal: true`.

EXITS. 0 every rule holds. 1 a refusal, named. 2 fail-closed: a file missing or unparseable. --prove-red applies
one-line mutants in memory and exits 0 only when each is refused and the pristine files are not.
"""
from __future__ import annotations

import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
CADDYFILE = ROOT / "services" / "routing" / "Caddyfile"
COMPOSE = ROOT / "services" / "routing" / "compose.yaml"

HEADER = "x-scenic-router-secret"
PLACEHOLDER = "REPLACE_WITH_THE_WORKER_ROUTER_SECRET"
UPSTREAM = "graphhopper:8989"
WORKER_CALLS = {("POST", "/route"), ("GET", "/isochrone"), ("GET", "/info")}
DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")
SERVER_COMMAND = ["java", "-cp", "/app/scenic-router.jar", "com.scenicdrive.routing.ScenicServerApplication",
                  "server", "/app/config.yml"]


def lines(text: str) -> list:
    """Non-blank lines with comments dropped (a whole-line `#` comment only: Caddy has no inline ones here)."""
    out = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = " ".join(raw.split())
        if line and not line.startswith("#"):
            out.append(line)
    return out


def blocks(text: str):
    """(top-level block head, [its body lines]) pairs; nested blocks come back as head + inner lines, flattened
    as `head {`, ..., `}` inside the body so a handle's or matcher's lines can be read in order."""
    top, depth, head, body = [], 0, None, []
    for line in lines(text):
        opens, closes = line.endswith("{"), line == "}"
        if depth == 0:
            if not opens:
                top.append((line, []))
                continue
            head, body = line[:-1].strip(), []
        elif not (closes and depth == 1):
            body.append(line)
        depth += 1 if opens else 0
        depth -= 1 if closes else 0
        if depth < 0:
            raise ValueError("unbalanced braces")
        if depth == 0 and closes:
            top.append((head, body))
    if depth != 0:
        raise ValueError("unbalanced braces")
    return top


def inner(body: list) -> list:
    """The body's own nested blocks as (head, [lines]) - matchers and handles of a site block."""
    out, i = [], 0
    while i < len(body):
        line = body[i]
        if line.endswith("{"):
            depth, j, sub = 1, i + 1, []
            while depth:
                if body[j].endswith("{"):
                    depth += 1
                if body[j] == "}":
                    depth -= 1
                if depth:
                    sub.append(body[j])
                j += 1
            out.append((line[:-1].strip(), sub))
            i = j
        else:
            out.append((line, None))
            i += 1
    return out


def caddy_problems(text: str) -> list:
    problems = []
    top = blocks(text)
    if not top or top[0] != ("", ["admin off"]):
        problems.append("Caddyfile: the first block must be the global `{ admin off }`")
    sites = [b for b in top[1:]]
    if len(sites) != 1:
        return problems + ["Caddyfile: exactly one site block expected, found %d" % len(sites)]
    entries = inner(sites[0][1])
    if any(line.split()[0] == "log" for line in lines(text)):
        problems.append("Caddyfile: a `log` directive - the requests carry coordinates; no access log")
    matchers = {head.split()[0]: sub for head, sub in entries if head.startswith("@") and sub is not None}
    handles = [(head, sub) for head, sub in entries if head.split()[0] == "handle"]
    proxied, proxies = set(), 0
    want_guard = ["header %s {env.ROUTER_SECRET}" % HEADER, "not header %s %s" % (HEADER, PLACEHOLDER)]
    for head, sub in handles:
        body = sub or []
        if not any(line.startswith("reverse_proxy") for line in body):
            continue
        words = head.split()
        name = words[1] if len(words) == 2 and words[1].startswith("@") else None
        rules = matchers.get(name) if name else None
        if rules is None or len(rules) != 4 or rules[:2] != want_guard \
                or not rules[2].startswith("method ") or not rules[3].startswith("path ") \
                or len(rules[2].split()) != 2 or len(rules[3].split()) != 2:
            problems.append("Caddyfile: `%s` proxies without the exact secret matcher (header, placeholder "
                            "refusal, one method, one path): %s" % (head, rules))
            continue
        if body != ["request_header -%s" % HEADER, "reverse_proxy %s" % UPSTREAM]:
            problems.append("Caddyfile: `%s` must strip the secret and proxy to %s only: %s" % (head, UPSTREAM, body))
        proxied.add((rules[2].split()[1], rules[3].split()[1]))
    proxies = sum(line.startswith("reverse_proxy") for line in lines(text))
    if proxies != len(proxied) or proxied != WORKER_CALLS:
        problems.append("Caddyfile: proxied (method, path) pairs %s with %d reverse_proxy lines; want exactly %s"
                        % (sorted(proxied), proxies, sorted(WORKER_CALLS)))
    if not handles or handles[-1] != ("handle", ["respond 404"]):
        problems.append("Caddyfile: the last handle must be the catch-all `handle { respond 404 }`")
    return problems


def compose_problems(text: str) -> list:
    doc = yaml.safe_load(text) or {}
    services = doc.get("services") or {}
    problems = []
    if sorted(services) != ["front", "graphhopper"]:
        return ["compose: services must be exactly front and graphhopper, found %s" % sorted(services)]
    gh, front = services["graphhopper"], services["front"]
    if gh.get("build") != "." or "image" in gh:
        problems.append("compose: graphhopper must be `build: .` (this directory's pinned Dockerfile)")
    if "ports" in gh or "expose" in gh or gh.get("network_mode"):
        problems.append("compose: graphhopper publishes or exposes a port - only the front door may")
    if gh.get("networks") != ["internal"]:
        problems.append("compose: graphhopper must be on the internal network only, found %s" % gh.get("networks"))
    if gh.get("entrypoint") != SERVER_COMMAND:
        problems.append("compose: graphhopper must run %s, found %s" % (SERVER_COMMAND, gh.get("entrypoint")))
    if not DIGEST.search(str(front.get("image", ""))):
        problems.append("compose: front image not pinned by @sha256: %s" % front.get("image"))
    secret = str((front.get("environment") or {}).get("ROUTER_SECRET", ""))
    if not re.fullmatch(r"\$\{ROUTER_SECRET:\?[^}]*\}", secret):
        problems.append("compose: front's ROUTER_SECRET must be `${ROUTER_SECRET:?...}` from the environment: %r" % secret)
    if ((doc.get("networks") or {}).get("internal") or {}).get("internal") is not True:
        problems.append("compose: the internal network must be `internal: true`")
    return problems


def problems_of(caddy: str, compose: str) -> list:
    return caddy_problems(caddy) + compose_problems(compose)


MUTANTS = [
    ("placeholder refusal dropped", "caddy", "\t\tnot header x-scenic-router-secret REPLACE_WITH_THE_WORKER_ROUTER_SECRET\n", ""),
    ("route opened to GET", "caddy", "method POST", "method GET"),
    ("secret header line dropped", "caddy", "\t\theader x-scenic-router-secret {env.ROUTER_SECRET}\n", ""),
    ("catch-all proxies", "caddy", "\t\trespond 404", "\t\treverse_proxy graphhopper:8989"),
    ("secret forwarded upstream", "caddy", "\t\trequest_header -x-scenic-router-secret\n", ""),
    ("access log on", "caddy", "\tadmin off\n", "\tadmin off\n\tlog\n"),
    ("graphhopper port published", "compose", "    networks: [internal]\n", "    networks: [internal]\n    ports: [\"8989:8989\"]\n"),
    ("secret literal in compose", "compose", "${ROUTER_SECRET:?", "x${ROUTER_SECRET:?"),
    ("caddy by tag only", "compose", "@sha256:", "-tag-only-"),
]


def prove_red(caddy: str, compose: str) -> int:
    if problems_of(caddy, compose):
        print("PROVE-RED: the pristine files are refused:", problems_of(caddy, compose))
        return 1
    bad = 0
    for name, which, old, new in MUTANTS:
        source = caddy if which == "caddy" else compose
        if source.count(old) < 1:
            print("PROVE-RED: mutant %r does not apply (%r not found)" % (name, old))
            bad += 1
            continue
        mutated = source.replace(old, new, 1)
        got = problems_of(mutated, compose) if which == "caddy" else problems_of(caddy, mutated)
        print("%s mutant %s" % ("REFUSED" if got else "MISSED ", name))
        bad += 0 if got else 1
    print("PROVE-RED %s: %d/%d mutants refused" % ("OK" if not bad else "FAILED", len(MUTANTS) - bad, len(MUTANTS)))
    return 0 if not bad else 1


def main(argv: list) -> int:
    try:
        caddy = CADDYFILE.read_text(encoding="utf-8")
        compose = COMPOSE.read_text(encoding="utf-8")
        if "--prove-red" in argv:
            return prove_red(caddy, compose)
        problems = problems_of(caddy, compose)
    except (OSError, ValueError, yaml.YAMLError, AttributeError, IndexError) as error:
        print("ROUTING FRONT DOOR UNREADABLE: %s" % error)
        return 2
    for problem in problems:
        print("ROUTING FRONT DOOR REFUSED: %s" % problem)
    if not problems:
        print("ROUTING FRONT DOOR OK: %d proxied calls, all behind the secret" % len(WORKER_CALLS))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
