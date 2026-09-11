#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Skeleton verify: compare a repo's root listing against the skeleton root set.

  verify_layout.py <repo-dir> [--name N] [--repos family.json]
  verify_layout.py [--repos family.json]     # sweep every repo the data file lists

Common = must be present. Leave = allowed. Forbid = must not be present. Anything else is
reported as unknown (a listing the skeleton does not rule on). Exit 1 on any DEVIATES.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES = HERE.parent / "data" / "rules.json"
FAMILY = HERE.parent / "data" / "instance.json"  # this machine's repo list; see instance.example.json


def _with_rules(fam: dict) -> dict:
    """Generic rules live in data/rules.json; the instance file names repositories and paths."""
    if RULES.exists():
        rules = json.loads(RULES.read_text())
        for k, v in rules.items():
            if k == "_":
                continue
            if k == "layout" and isinstance(fam.get("layout"), dict):
                fam["layout"] = {**v, **fam["layout"]}
            else:
                fam.setdefault(k, v)
    return fam


def load_family(path: Path):
    import json
    fam = _with_rules(json.loads(Path(path).read_text()))
    base = Path(path).resolve().parent
    root = Path(fam.get("root") or base)
    if not root.is_absolute():
        root = (base / root).resolve()
    return fam, root


def git(d: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(d), *args], capture_output=True, text=True).stdout.strip()


def ignored(d: Path, names: set[str]) -> set[str]:
    """Root entries git ignores. They exist only in a working copy, so they say nothing
    about the published layout; a CI clone has none of them."""
    if not names or not (d / ".git").exists():
        return set()
    out = subprocess.run(["git", "-C", str(d), "check-ignore", "--", *sorted(names)],
                         capture_output=True, text=True).stdout.split()
    return {Path(x).parts[0] for x in out}


def check_root(d: Path, sets: dict):
    """Repo-relative skeleton check. Returns (state, detail, dirty, branch, sha)."""
    common, leave, forbid = (set(sets.get(k, [])) for k in ("common", "leave", "forbid"))
    br = git(d, "branch", "--show-current")
    sha = git(d, "log", "-1", "--format=%h %s")[:60]
    dirty = git(d, "status", "--short")
    root = {p.name for p in d.iterdir()}
    root -= ignored(d, root)  # a build artefact a CI clone never sees is not a layout deviation
    bad = sorted(root & forbid)
    missing = sorted(common - root)
    unknown = sorted(root - common - leave - forbid)
    state = "OK" if not bad and not missing and not dirty else "DEVIATES"
    return state, f"forbidden={bad} missing={missing} unknown={unknown}", dirty, br, sha


def row(name: str, d: Path | None, sets: dict):
    if d is None or not d.exists():
        return (name, "NOT STARTED", "", "")
    state, detail, dirty, br, sha = check_root(d, sets)
    return (name, f"{state} [{br}] {sha}", detail, "DIRTY" if dirty else "")


def render(rows) -> str:
    w = max(len(r[0]) for r in rows)
    out = []
    for r in rows:
        out.append(f"{r[0]:<{w}}  {r[1]}")
        if r[2] and ("DEVIATES" in r[1]):
            out.append(" " * (w + 2) + r[2] + ("  " + r[3] if r[3] else ""))
    return "\n".join(out)


def sweep(fam: dict, root: Path) -> list[tuple]:
    cfg = fam["layout"]
    dirs = {e["name"]: e.get("dir", e["name"]) for e in fam["repos"]}
    rows = []
    for source in ("worktrees", "clones"):
        tmpl = cfg["search"]["worktree" if source == "worktrees" else "clone"]
        for name in cfg.get(source, []):
            d = root / tmpl.format(name=name, dir=dirs.get(name, name))
            rows.append(row(name, d if d.exists() else None, cfg))
    return rows


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=True, description=__doc__)
    ap.add_argument("repo", nargs="?")
    ap.add_argument("--repos", default=str(FAMILY))
    ap.add_argument("--name")
    a = ap.parse_args(argv)
    fam, root = load_family(Path(a.repos))
    if a.repo is None:
        rows = sweep(fam, root)
    else:
        d = Path(a.repo).resolve()
        rows = [row(a.name or d.name, d, fam["layout"])]
    print(render(rows))
    return 1 if any(r[1].startswith("DEVIATES") for r in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
