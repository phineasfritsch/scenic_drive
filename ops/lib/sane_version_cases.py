"""check-sane-prod's v- rows (T-0402): ops/sane --prod's version row over a FIXTURE git history.

Each row builds a scratch repo: a live commit (BASE, plus this checkout's ops/lib/sane_prod.py so the quota row can
answer) and one commit on top applying the row's changes. The fake Worker answers /__version with the live commit;
the SHIPPED ops/sane (check-sane-prod's --sane, default this checkout's) runs with its cwd in the scratch repo, so it
judges the scratch history with its own rules. A row compares the exit code and the WHOLE `version` line to what is
typed here - the expected counts are written per row, never read back through ops/lib/sane_version.py.
v-real-tree commits every path this checkout tracks under services/api (empty) and must leave 0 unclassified.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from sane_prod_fake import STATE, rows, wire

BASE = {
    "services/api/src/index.ts": 'import la from "../../etl/regions/la/region.json";\n'
                                 'import shared from "../test/fixtures/shared.json";\nexport default { la, shared };\n',
    "services/api/src/util.ts": "export const x = 1;\n",
    "services/api/wrangler.jsonc": '{\n  "name": "scenic-api",\n  "main": "src/index.ts",\n'
                                   '  "vars": { "ROUTER_URL": "https://a.invalid" }\n}\n',
    "services/api/package.json": '{"name": "scenic-api"}\n',
    "services/api/package-lock.json": '{"lockfileVersion": 3}\n',
    "services/api/tsconfig.json": '{"compilerOptions": {}}\n',
    "services/api/vitest.config.ts": "export default {};\n",
    "services/api/test/a.test.ts": "// a\n",
    "services/api/test/fixtures/shared.json": "{}\n",
    "services/api/migrations/0001_places.sql": "create table p (id int);\n",
    "services/etl/regions/la/region.json": '{"id": "la"}\n',
    "services/etl/other.py": "x = 1\n",
    "ops/deploy": "#!/usr/bin/env bash\n",
}
SEED = "services/api/test/fixtures/seed-places/places-0001.sql"
A = "services/api/"
# name -> (changes on top of BASE, want exit, counted paths in git's order, bundle, unclassified, not bundled)
CASES: dict[str, tuple[dict[str, str], int, list[str], int, int, int]] = {
    "v-none": ({}, 0, [], 0, 0, 0),
    "v-fixture": ({SEED: "insert into p values (1);\n"}, 0, [], 0, 0, 1),
    "v-test": ({A + "test/a.test.ts": "// b\n"}, 0, [], 0, 0, 1),
    "v-vitest": ({A + "vitest.config.ts": "export default { x: 1 };\n"}, 0, [], 0, 0, 1),
    "v-outside": ({"services/etl/other.py": "x = 2\n"}, 0, [], 0, 0, 0),
    "v-src": ({A + "src/util.ts": "export const x = 2;\n"}, 3, [A + "src/util.ts"], 1, 0, 0),
    "v-src-new": ({A + "src/new.ts": "export {};\n"}, 3, [A + "src/new.ts"], 1, 0, 0),
    "v-wrangler-var": ({A + "wrangler.jsonc": BASE[A + "wrangler.jsonc"].replace("a.invalid", "b.invalid")}, 3,
                       [A + "wrangler.jsonc"], 1, 0, 0),
    "v-package": ({A + "package.json": '{"name": "scenic-api", "version": "1"}\n'}, 3, [A + "package.json"], 1, 0, 0),
    "v-lock": ({A + "package-lock.json": '{"lockfileVersion": 4}\n'}, 3, [A + "package-lock.json"], 1, 0, 0),
    "v-tsconfig": ({A + "tsconfig.json": '{"compilerOptions": {"strict": true}}\n'}, 3, [A + "tsconfig.json"], 1, 0, 0),
    "v-deploy": ({"ops/deploy": "#!/usr/bin/env bash\nexit 0\n"}, 3, ["ops/deploy"], 1, 0, 0),
    "v-migration": ({A + "migrations/0002_x.sql": "select 1;\n"}, 3, [A + "migrations/0002_x.sql"], 1, 0, 0),
    "v-fixture-and-src": ({SEED: "-- s\n", A + "src/util.ts": "export const x = 3;\n"}, 3, [A + "src/util.ts"], 1, 0, 1),
    "v-region": ({"services/etl/regions/la/region.json": '{"id": "la2"}\n'}, 3,
                 ["services/etl/regions/la/region.json"], 1, 0, 0),
    "v-imported-test": ({A + "test/fixtures/shared.json": '{"a": 1}\n'}, 3, [A + "test/fixtures/shared.json"], 1, 0, 0),
    "v-newdir": ({A + "lib/x.ts": "export {};\n"}, 3, [A + "lib/x.ts"], 0, 1, 0),
    "v-newfile": ({A + "worker-configuration.d.ts": "export {};\n"}, 3, [A + "worker-configuration.d.ts"], 0, 1, 0),
    "v-real-tree": ({}, 3, [], 0, 0, 0),  # changes and counts computed from this checkout's tracked paths
}


def git_env(home: str) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    cfg = os.path.join(home, "gitconfig")
    open(cfg, "w").close()
    env.update({"GIT_CONFIG_GLOBAL": cfg, "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "fixture",
                "GIT_AUTHOR_EMAIL": "fixture@invalid", "GIT_COMMITTER_NAME": "fixture",
                "GIT_COMMITTER_EMAIL": "fixture@invalid"})
    return env


def write_tree(repo: str, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = os.path.join(repo, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)


def commit(repo: str, env: dict, msg: str) -> str:
    def g(*a: str) -> str:
        return subprocess.run(["git", *a], cwd=repo, env=env, capture_output=True, text=True, check=True).stdout.strip()
    g("add", "-A", ".")
    g("commit", "-q", "--allow-empty", "-m", msg)
    return g("rev-parse", "HEAD")


def real_tree(root: str) -> tuple[dict[str, str], list[str], int, int]:
    """Every tracked services/api path, emptied; expected (changes, counted, bundle, not bundled), typed here."""
    paths = subprocess.run(["git", "ls-files", "-z", "services/api"], cwd=root, capture_output=True,
                           text=True, check=True).stdout.split("\0")
    paths = sorted(p for p in paths if p)
    ignored = [p for p in paths if p.startswith(A + "test/") or p == A + "vitest.config.ts"]
    counted = [p for p in paths if p not in ignored]
    return {p: "" for p in paths}, counted, len(counted), len(ignored)


def expected_line(case: tuple, live: str, head: str) -> str:
    _, rc, counted, nb, nu, ni = case
    if rc == 0:
        msg = f"live {live} == Worker inputs at HEAD {head} ({ni} not-bundled path(s) changed)"
        return f"{'version':<9} {'ok':<6} {msg}"
    msg = (f"Worker inputs changed since live {live} -> deploy pending: {' '.join(counted[:3])} "
           f"({nb} bundle, {nu} unclassified, {ni} not bundled)")
    return f"{'version':<9} {'FAIL':<6} {msg}"


def version_case(root: str, sane: str, base: str, name: str, health: dict) -> list[str]:
    case = CASES[name]
    with tempfile.TemporaryDirectory(prefix="t0402-v-") as d:
        repo = os.path.join(d, "repo")
        os.makedirs(repo)
        env = git_env(d)
        subprocess.run(["git", "init", "-q", "-b", "main", repo], env=env, check=True)
        write_tree(repo, BASE)
        os.makedirs(os.path.join(repo, "ops", "lib"))
        shutil.copyfile(os.path.join(root, "ops", "lib", "sane_prod.py"), os.path.join(repo, "ops", "lib", "sane_prod.py"))
        live = commit(repo, env, "live")
        if name == "v-real-tree":
            changes, counted, nb, ni = real_tree(root)
            case = (changes, 3, counted, nb, 0, ni)
        write_tree(repo, case[0])
        head = commit(repo, env, name)
        short = [subprocess.run(["git", "rev-parse", "--short", s], cwd=repo, env=env, capture_output=True,
                                text=True, check=True).stdout.strip() for s in (live, head)]
        STATE.clear()
        STATE["/__health"] = (200, wire(health))
        STATE["/__version"] = (200, wire({"git_sha": live, "built_at": "2026-10-17T00:00:00Z"}))
        run_env = {k: v for k, v in env.items() if k not in ("CORPUS_MANIFEST_URL", "TILES_MANIFEST_URL", "SANE_CORPUS")}
        run_env.update({"SANE_SCOPE": "prod", "API_URL": base})
        p = subprocess.run(["bash", sane, "--prod"], cwd=repo, env=run_env, capture_output=True, text=True)
    lines = [ln.rstrip("\r") for ln in p.stdout.splitlines() if ln.startswith("version ")]
    want = expected_line(case, *short)
    problems = []
    if p.returncode != case[1]:
        problems.append(f"exit {p.returncode}, want {case[1]}")
    if lines != [want]:
        problems.append(f"version line {lines!r}, want [{want!r}]")
    stray = sorted(r for r, st in rows(p.stdout).items() if "FAIL" in st and r != "version")
    if stray:
        problems.append(f"unexpected FAIL rows {stray}")
    if problems:
        problems.append("ops/sane printed: " + " | ".join(ln for ln in p.stdout.splitlines() if ln.strip()))
    return problems
