#!/usr/bin/env python3
"""pins/PINS.yaml must load under a strict YAML loader (yaml.safe_load), not only under ops/lib/pins.py.

  check-pins-yaml.py [PATH]      (default: pins/PINS.yaml at the repo root)

ops/lib/pins.py reads PINS.yaml line by line, so a value that is not valid YAML (a plain scalar holding ': ', a
"..." scalar with bare inner quotes) passes every pin run while any real YAML consumer cannot read the file
(T-0301). This check fails closed:
  exit 1  the file does not load - the line and column the loader names are printed;
          or it loads to something other than a non-empty list of mappings;
          or the pin ids it yields differ from the ids ops/lib/pins.py yields (the two readers disagree).
          or any field of any pin differs between the two readers, value AND type (a plain value cut at
          ' #', an unquoted date yaml reads as datetime.date) - every such pin+field is printed.
  exit 2  cannot tell: PyYAML is not importable or the file is missing.
  exit 0  `PINS-YAML ok pins=N path=...`.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def pins_reader():
    spec = importlib.util.spec_from_file_location("pins_reader", ROOT / "ops" / "lib" / "pins.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv):
    path = Path(argv[0]) if argv else ROOT / "pins" / "PINS.yaml"
    try:
        import yaml
    except ImportError:
        print("PINS-YAML CANNOT TELL: PyYAML is not importable (python3 -m pip install pyyaml, or apt python3-yaml)")
        return 2
    if not path.is_file():
        print(f"PINS-YAML CANNOT TELL: {path} is missing")
        return 2
    text = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.MarkedYAMLError as e:
        mark = e.problem_mark
        where = f"line {mark.line + 1}, column {mark.column + 1}" if mark else "unknown position"
        print(f"PINS-YAML FAIL: {path} {where}: {e.problem or e}")
        if mark is not None:
            lines = text.split("\n")
            if 0 <= mark.line < len(lines):
                print(f"  line {mark.line + 1}: {lines[mark.line][:160]}")
        return 1
    except yaml.YAMLError as e:
        print(f"PINS-YAML FAIL: {path}: {e}")
        return 1
    if not isinstance(data, list) or not data or not all(isinstance(p, dict) for p in data):
        print(f"PINS-YAML FAIL: {path} loads to {type(data).__name__}, not a non-empty list of mappings")
        return 1
    yaml_ids = [p.get("id") for p in data]
    try:
        reader_ids = [p.get("id") for p in pins_reader().load(path)]
    except ValueError as e:
        print(f"PINS-YAML FAIL: ops/lib/pins.py cannot read {path}: {e}")
        return 1
    if yaml_ids != reader_ids:
        print(f"PINS-YAML FAIL: {path}: yaml.safe_load yields {len(yaml_ids)} pin ids, ops/lib/pins.py {len(reader_ids)};"
              " first difference:")
        for i, (a, b) in enumerate(zip(yaml_ids + [None] * len(reader_ids), reader_ids + [None] * len(yaml_ids))):
            if a != b:
                print(f"  item {i}: yaml={a!r} pins.py={b!r}")
                break
        return 1
    reader = pins_reader().load(path)
    bad = []
    for ypin, rpin in zip(data, reader):
        pid = rpin.get("id")
        for key in sorted(set(ypin) | set(rpin), key=str):
            if key not in ypin or key not in rpin:
                bad.append(f"  {pid} {key}: present only in {'yaml.safe_load' if key in ypin else 'ops/lib/pins.py'}")
            elif not same(ypin[key], rpin[key]):
                bad.append(f"  {pid} {key}: yaml={describe(ypin[key])} pins.py={describe(rpin[key])}")
    if bad:
        print(f"PINS-YAML FAIL: {path}: {len(bad)} field(s) where yaml.safe_load and ops/lib/pins.py read different values:")
        print("\n".join(bad))
        return 1
    print(f"PINS-YAML ok pins={len(data)} fields={sum(len(p) for p in data)} path={path}")
    return 0


def same(a, b):
    """Full equality including type: yaml's True/1.0/date never equals pins.py's 1/'1.0'/'2026-10-07'."""
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def describe(v):
    if isinstance(v, str):
        return f"str({len(v)} chars) {v[:60]!r}{'...' if len(v) > 60 else ''}"
    return f"{type(v).__name__} {v!r}"[:120]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
