"""The one `--only` parser every Python driver under ops/mutate/ uses (T-0347).

A typo'd selection must never read as a pass when only the exit status is read, so every refusal here is
EXIT_ONLY_REFUSED (64, sysexits EX_USAGE) - a status no other refusal in these drivers uses (floor, dirty tree,
baseline and build refusals are 2) - and the caller never gets to run anything after it.

    --only A,B   and   --only=A,B      both spellings, repeatable
    a token is an id, never a range    `49-55` is one unknown id and refuses
    EVERY token must select an entry   `--only 1,49-55` refuses; it does not run 1 and drop the rest

A driver with no `--only` calls refuse_unsupported(): ignoring the flag would run the WHOLE population under a
command line that asked for a part of it. ops/lib/check-mutate-only.py runs every driver with a selection that
names nothing and one that does not parse, and refuses unless each exits 64.
"""
from __future__ import annotations

import sys

EXIT_ONLY_REFUSED = 64
FLAG = "--only"


def refuse(why: str) -> None:
    """Print the refusal and leave with EXIT_ONLY_REFUSED; nothing after this call runs."""
    sys.stdout.write("REFUSING TO RUN: %s\n" % why)
    sys.stdout.flush()
    raise SystemExit(EXIT_ONLY_REFUSED)


def only_tokens(argv, split: bool = True) -> list | None:
    """None when argv carries no --only; otherwise every token of every --only, in order. split=False keeps each
    --only value whole (a driver whose entry names contain commas: autopsy, fallback, placeallow)."""
    argv = list(argv)
    tokens = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == FLAG:
            if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
                refuse("%s has no value" % FLAG)
            value, i = argv[i + 1], i + 2
        elif arg.startswith(FLAG + "="):
            value, i = arg[len(FLAG) + 1:], i + 1
        elif arg.startswith(FLAG):
            refuse("%r is not a flag this driver knows; did you mean %s?" % (arg, FLAG))
        else:
            i += 1
            continue
        parts = value.split(",") if split else [value]
        empty = [p for p in parts if p.strip() == "" or p != p.strip()]
        if empty:
            refuse("%s %r has an empty or padded token" % (FLAG, value))
        tokens = (tokens or []) + parts
    return tokens


def select_only(argv, keys, substring: bool = False, split: bool = True) -> set | None:
    """None when argv carries no --only; otherwise the keys it selects. A token selects the keys equal to it
    (or, with substring=True, the keys containing it). Any token that selects nothing refuses."""
    tokens = only_tokens(argv, split)
    if tokens is None:
        return None
    keys = list(keys)
    chosen, unknown = set(), []
    for token in tokens:
        hit = [k for k in keys if (token in k if substring else token == k)]
        if not hit:
            unknown.append(token)
        chosen.update(hit)
    if unknown:
        refuse("%s names no entry of this population: %s (a token is %s, never a range)"
               % (FLAG, ", ".join(unknown), "a fragment of an entry name" if substring else "one entry id"))
    return chosen


def refuse_unsupported(argv) -> None:
    """For a driver with no --only: refuse the flag instead of ignoring it and running the whole population."""
    if any(a.startswith(FLAG) for a in argv):
        refuse("this driver has no %s; ignoring it would run the WHOLE population" % FLAG)
