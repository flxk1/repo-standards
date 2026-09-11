#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""README canon verify: word budget, negations, marketing words, H1, section order, Family,
description length, badges/emoji, Problem (verbatim against a plan table), Example in/out,
Language section + card, llms.txt drift.

  verify_text.py <repo-dir> [--kind K] [--name N] [--plan F] [--descriptions D]
                            [--llms-dir D] [--skills-dir D] [--repos family.json]
  verify_text.py [--repos family.json]      # sweep every repo the data file lists

<repo-dir> mode checks one repo standalone: --kind, and whether a language card is
required, are read from the data file when the repo is listed there, else --kind wins and
the default budget applies. The Problem-verbatim and description checks run only when
--plan / --descriptions name them. Exit 1 on any FAIL.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES = HERE.parent / "data" / "rules.json"
FAMILY = HERE.parent / "data" / "instance.json"  # this machine's repo list; see instance.example.json
LLMS = HERE / "llms_txt.py"
DEFAULT_KIND = "spec"

MARKET = r"\b(robust|powerful|flexible|comprehensive|production-grade|enterprise-ready|elegant|seamless|sophisticated|novel|innovative|best-in-class|groundbreaking)\b"
NEG = r"\b(does not|is not|never|unlike|rather than|no )\b"
ORDER = ["Problem", "Install|Read", "Usage", "Example", "Language", "Interface|Contracts|API", "Family", "Status", "License"]


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
    # single-repo mode needs only the rules; a sweep needs an instance file naming the repositories
    raw = json.loads(Path(path).read_text()) if Path(path).exists() else {}
    fam = _with_rules(raw)
    base = Path(path).resolve().parent
    root = Path(fam.get("root") or base)
    if not root.is_absolute():
        root = (base / root).resolve()
    return fam, root


def resolve(root: Path, templates: list[str], entry: dict) -> Path:
    sub = {"name": entry["name"], "dir": entry.get("dir", entry["name"])}
    cands = [root / t.format(**sub) for t in templates]
    return next((c for c in cands if c.exists()), cands[-1])


def git_sha(d: Path) -> str:
    return subprocess.run(["git", "-C", str(d), "log", "-1", "--format=%h"],
                          capture_output=True, text=True).stdout.strip()


def check_readme(repo: Path, name: str, kind: str, budgets: dict, *, plan_text=None, desc_len=None,
                 desc_max=160, language_card=False, llms_dir=None, skills_dir=None):
    """Repo-relative README canon check. Returns (probs, words, neg) or None when there is no README."""
    rd = repo / "README.md"
    if not rd.exists():
        return None
    body = "\n".join(l for l in rd.read_text().splitlines() if not l.startswith("<!--"))
    words = len(body.split())
    neg = len(re.findall(NEG, body, re.I))
    market = len(re.findall(MARKET, body, re.I))
    h1 = re.search(r"^# (.+)$", body, re.M)
    h1ok = bool(h1) and h1.group(1).strip() == name
    heads = re.findall(r"^## (.+)$", body, re.M)
    fam = any(h.strip().startswith("Family") for h in heads)
    seq = [next((i for i, o in enumerate(ORDER) if re.match(o, h.strip())), None) for h in heads]
    seq = [s for s in seq if s is not None]
    badge = ("shields.io" in body) or bool(re.search(r"[\U0001F300-\U0001FAFF]", body))
    budget = budgets.get(kind, budgets.get(DEFAULT_KIND))

    probs = []
    if words > budget:
        probs.append(f"words {words}>{budget}")
    if neg > 1:
        probs.append(f"neg {neg}")
    if market:
        probs.append(f"marketing {market}")
    if not h1ok:
        probs.append("H1")
    if not fam:
        probs.append("no Family")
    if seq != sorted(seq):
        probs.append("order")
    if desc_len is not None:
        if desc_len < 0:
            probs.append("no description")
        elif desc_len > desc_max:
            probs.append(f"desc {desc_len}")
    if badge:
        probs.append("badge/emoji")
    if not any(h.strip() == "Problem" for h in heads):
        probs.append("no Problem")
    elif plan_text:
        sec = re.search(r"^## Problem\n(.*?)(?=^## )", body, re.S | re.M)
        ptxt = " ".join(sec.group(1).split()) if sec else ""
        row = next((l for l in plan_text.splitlines() if l.startswith(f"| {name} |")), None)
        if row:
            cells = [c.strip() for c in row.strip("|").split("|")]
            if len(cells) >= 3 and not (cells[1] in ptxt and cells[2] in ptxt):
                probs.append("Problem not verbatim")
    if not any(h.strip() == "Example" for h in heads):
        probs.append("no Example")
    elif not (re.search(r"^in\s*:", body, re.M) and re.search(r"^out\s*:", body, re.M)):
        probs.append("Example lacks in/out")
    if language_card:
        if not any(h.strip() == "Language" for h in heads):
            probs.append("no Language")
        if not (repo / "docs" / "language-card.md").exists():
            probs.append("no card")
    probs += check_llms(llms_dir or repo, skills_dir)
    return probs, words, neg


def check_llms(llms_dir: Path, skills_dir=None) -> list[str]:
    args = [sys.executable, str(LLMS), str(llms_dir), "--check"]
    if skills_dir:
        args += ["--skills-dir", str(skills_dir)]
    r = subprocess.run(args, capture_output=True, text=True)
    if not r.returncode:
        return []
    return ["llms.txt missing" if "missing" in r.stdout else "llms.txt drift"]


def row(name: str, res, sha: str):
    if res is None:
        return (name, "NO README", "")
    probs, words, neg = res
    return (name, f"{'OK' if not probs else 'FAIL'} {sha} {words}w neg{neg}", "; ".join(probs))


def render(rows, total=True) -> str:
    w = max(len(r[0]) for r in rows)
    out = [f"{r[0]:<{w}}  {r[1]:<24} {r[2]}" for r in rows]
    if total:
        out.append(f"\n{sum(1 for r in rows if r[1].startswith('OK'))} OK / {len(rows)}")
    return "\n".join(out)


def sweep(fam: dict, root: Path) -> list[tuple]:
    budgets = fam["budgets"]
    cfg = fam.get("text", {})
    search = cfg.get("search", ["{name}"])
    lang = set(fam.get("language_repos", []))
    exempt = set(fam.get("language_card_exempt", []))
    plan = root / fam["plan"] if fam.get("plan") else None
    plan_text = plan.read_text() if plan and plan.exists() else None
    ddir = root / fam["descriptions"] if fam.get("descriptions") else None
    ddir = ddir if ddir and ddir.exists() else None
    rows = []
    for e in fam.get("repos", []):
        name = e["name"]
        d = resolve(root, search, e)
        sub = {"name": name, "dir": e.get("dir", name)}
        desc_len = None
        if ddir:
            f = ddir / f"{name}.txt"
            desc_len = len(f.read_text().strip()) if f.exists() else -1
        cands = [root / t.format(**sub) for t in cfg.get("llms_search", [])] + [d]
        ld = next((c for c in cands if (c / "llms.txt").exists()), d)
        sd = root / cfg["skills_dir"].format(**sub) if cfg.get("skills_dir") else None
        sd = sd if sd and sd.is_dir() and not (ld / "skills").is_dir() else None
        res = check_readme(d, name, e["kind"], budgets, plan_text=plan_text, desc_len=desc_len,
                           desc_max=fam.get("description_max", 160),
                           language_card=name in lang and name not in exempt,
                           llms_dir=ld, skills_dir=sd)
        rows.append(row(name, res, git_sha(d)))
    return rows


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=True, description=__doc__)
    ap.add_argument("repo", nargs="?")
    ap.add_argument("--repos", default=str(FAMILY))
    ap.add_argument("--name")
    ap.add_argument("--kind")
    ap.add_argument("--plan")
    ap.add_argument("--descriptions")
    ap.add_argument("--llms-dir")
    ap.add_argument("--skills-dir")
    a = ap.parse_args(argv)
    fam, root = load_family(Path(a.repos))
    if a.repo is None:
        rows = sweep(fam, root)
    else:
        d = Path(a.repo).resolve()
        name = a.name or d.name
        e = next((x for x in fam.get("repos", []) if x["name"] == name), {})
        kind = a.kind or e.get("kind", DEFAULT_KIND)
        desc_len = None
        if a.descriptions:
            f = Path(a.descriptions) / f"{name}.txt"
            desc_len = len(f.read_text().strip()) if f.exists() else -1
        card = name in set(fam.get("language_repos", [])) and name not in set(fam.get("language_card_exempt", []))
        res = check_readme(d, name, kind, fam["budgets"],
                           plan_text=Path(a.plan).read_text() if a.plan else None,
                           desc_len=desc_len, desc_max=fam.get("description_max", 160),
                           language_card=card,
                           llms_dir=Path(a.llms_dir) if a.llms_dir else None,
                           skills_dir=Path(a.skills_dir) if a.skills_dir else None)
        rows = [row(name, res, git_sha(d))]
    print(render(rows, total=a.repo is None))
    return 0 if all(r[1].startswith("OK") for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
