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
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = HERE.parent / "data" / "family.json"


def load_family(path: Path):
    import json
    fam = json.loads(Path(path).read_text())
    base = Path(path).resolve().parent
    root = Path(fam.get("root") or base)
    if not root.is_absolute():
        root = (base / root).resolve()
    return fam, root


def git(d: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(d), *args], capture_output=True, text=True).stdout.strip()


def check_root(d: Path, sets: dict):
    """Repo-relative skeleton check. Returns (state, detail, dirty, branch, sha)."""
    common, leave, forbid = (set(sets.get(k, [])) for k in ("common", "leave", "forbid"))
    br = git(d, "branch", "--show-current")
    sha = git(d, "log", "-1", "--format=%h %s")[:60]
    dirty = git(d, "status", "--short")
    root = {p.name for p in d.iterdir()}
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
