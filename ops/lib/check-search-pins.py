#!/usr/bin/env python3
"""T-0359 A6: services/search builds only from pinned bytes.

    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-search-pins.py
    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-search-pins.py --prove-red

A WHITELIST of what may fetch, never a list of bad spellings:
  * every Dockerfile FROM names its image by @sha256:<64 hex>;
  * every Dockerfile ADD or COPY whose source is a URL carries --checksum=sha256:<64 hex>;
  * no Dockerfile RUN fetches anything (curl, wget, git, apt-get, apk, pip, npm) - the only download is the pinned ADD;
  * every compose `image:` names its image by @sha256:<64 hex>, and every compose service has an image or `build: .`.

EXITS. 0 every rule holds. 1 a refusal, named. 2 fail-closed: a file missing, or nothing found to check (no FROM, no
service) - an empty file is not a pinned one. --prove-red applies three one-line mutants in memory (a tag-only FROM, a
tag-only compose image, the jar checksum dropped) and exits 0 only when each is refused and the pristine files are not.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "services" / "search" / "Dockerfile"
COMPOSE = ROOT / "services" / "search" / "compose.yaml"

DIGEST = re.compile(r"@sha256:[0-9a-f]{64}(\s|$)")
CHECKSUM = re.compile(r"--checksum=sha256:[0-9a-f]{64}(\s|$)")
FETCHERS = re.compile(r"\b(curl|wget|git|apt-get|apt|apk|pip|pip3|npm|yarn)\b")


class Unreadable(Exception):
    pass


def instructions(text: str) -> list:
    """The Dockerfile's instructions, continuation lines joined, comments and blanks dropped."""
    out, current = [], ""
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not current and (not line or line.startswith("#")):
            continue
        if line.endswith("\\"):
            current += line[:-1] + " "
            continue
        out.append(current + line)
        current = ""
    if current:
        out.append(current)
    return out


def dockerfile_problems(text: str) -> list:
    problems, froms = [], 0
    for ins in instructions(text):
        word = ins.split(None, 1)[0].upper()
        if word == "FROM":
            froms += 1
            if not DIGEST.search(ins):
                problems.append("Dockerfile FROM without @sha256: %s" % ins)
        elif word in ("ADD", "COPY") and re.search(r"\bhttps?://", ins):
            if not CHECKSUM.search(ins):
                problems.append("Dockerfile %s of a URL without --checksum=sha256: %s" % (word, ins))
        elif word == "RUN" and FETCHERS.search(ins):
            problems.append("Dockerfile RUN fetches outside the pinned ADD: %s" % ins)
    if froms == 0:
        raise Unreadable("no FROM in the Dockerfile")
    return problems


def compose_problems(text: str) -> list:
    problems, services, current, sources = [], [], None, {}
    in_services = False
    for raw in text.replace("\r\n", "\n").split("\n"):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0:
            in_services = line == "services:"
            current = None
            continue
        if in_services and indent == 2 and line.endswith(":"):
            current = line[:-1]
            services.append(current)
            sources[current] = []
            continue
        if in_services and current is not None and indent == 4:
            if line.startswith("image:"):
                sources[current].append("image")
                if not DIGEST.search(line + " "):
                    problems.append("compose service %s image without @sha256: %s" % (current, line))
            elif line.startswith("build:"):
                sources[current].append("build" if line == "build: ." else "other build")
    if not services:
        raise Unreadable("no services in compose.yaml")
    for name in services:
        if sources[name] not in (["image"], ["build"]):
            problems.append("compose service %s is not exactly one pinned image or `build: .`: %s" % (name, sources[name]))
    return problems


def check(docker_text: str, compose_text: str) -> list:
    return dockerfile_problems(docker_text) + compose_problems(compose_text)


def read() -> tuple:
    for path in (DOCKERFILE, COMPOSE):
        if not path.is_file():
            raise Unreadable("missing %s" % path.relative_to(ROOT).as_posix())
    return DOCKERFILE.read_text(encoding="utf-8"), COMPOSE.read_text(encoding="utf-8")


def mutate(text: str, pattern: str, replacement: str) -> str:
    out, n = re.subn(pattern, replacement, text, count=1)
    if n != 1:
        raise Unreadable("prove-red anchor not found: %s" % pattern)
    return out


def prove_red(docker_text: str, compose_text: str) -> int:
    arms = [
        ("a tag-only FROM", mutate(docker_text, r"(FROM \S+?)@sha256:[0-9a-f]{64}", r"\1"), compose_text),
        ("a tag-only compose image", docker_text, mutate(compose_text, r"(image: \S+?)@sha256:[0-9a-f]{64}", r"\1")),
        ("the jar checksum dropped", mutate(docker_text, r"--checksum=sha256:[0-9a-f]{64} ", ""), compose_text),
    ]
    refused = 0
    for label, d, c in arms:
        found = check(d, c)
        sys.stdout.write("PROVE-RED %-28s %s\n" % (label, found[0] if found else "NOT REFUSED - THIS ARM FAILED"))
        refused += 1 if found else 0
    control = check(docker_text, compose_text)
    sys.stdout.write("PROVE-RED %-28s %s\n" % ("CONTROL: pristine", control[0] if control else "clean, as required"))
    ok = refused == len(arms) and not control
    sys.stdout.write("SEARCH-PINS PROVE-RED %s: %d of %d arms refused\n" % ("OK" if ok else "FAILED", refused, len(arms)))
    return 0 if ok else 1


def main(argv) -> int:
    try:
        docker_text, compose_text = read()
        if "--prove-red" in argv:
            return prove_red(docker_text, compose_text)
        problems = check(docker_text, compose_text)
    except Unreadable as e:
        sys.stdout.write("SEARCH-PINS UNREADABLE: %s\n" % e)
        return 2
    for p in problems:
        sys.stdout.write("REFUSED %s\n" % p)
    sys.stdout.write("SEARCH-PINS %s\n" % ("ok" if not problems else "FAILED (%d)" % len(problems)))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
