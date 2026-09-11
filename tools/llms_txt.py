#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""llms.txt from README: `llms_txt.py <repo> [--write | --check] [--skills-dir DIR]`. --check exits 1 on drift."""
import re, sys
from pathlib import Path

SECTIONS = [("Problem",), ("Install", "Read"), ("Usage",), ("Interface", "Contracts"), ("Family",)]
LIMIT = 60
FENCE = re.compile(r"^(```|~~~)")
EXEMPT_HEAD, EXEMPT_CITE = "# Loomground", "standard/spec/SPEC.md"


def exempt(path):
    if not path.exists():
        return False
    t = path.read_text()
    return t.startswith(EXEMPT_HEAD) and EXEMPT_CITE in t


def parse(readme):
    lines = [l.rstrip() for l in readme.read_text().splitlines() if not l.lstrip().startswith("<!--")]
    name, intro, sections, cur, fence = None, [], {}, None, False
    for l in lines:
        if FENCE.match(l):
            fence = not fence
        if not fence and l.startswith("# ") and name is None:
            name = l[2:].strip(); continue
        if not fence and l.startswith("## "):
            cur = l[3:].strip(); sections[cur] = []; continue
        (sections[cur] if cur else intro).append(l)
    return name, intro, sections


def one_liner(intro):
    paras, buf = [], []
    for l in intro + [""]:
        if l.strip():
            buf.append(l.strip())
        elif buf:
            paras.append(" ".join(buf)); buf = []
    plain = [p for p in paras if not (p.startswith("**") and p.endswith("**"))]
    return (plain or paras or [""])[0]


def tidy(lines):
    out = []
    for l in lines:
        if l.strip() or (out and out[-1].strip()):
            out.append(l)
    while out and not out[-1].strip():
        out.pop()
    return out


def frontmatter(skill_md):
    t = skill_md.read_text().splitlines()
    if not t or t[0].strip() != "---":
        return []
    body = []
    for l in t[1:]:
        if l.strip() == "---":
            break
        body.append(l)
    tools, grab = [], False
    for l in body:
        if l.startswith("allowed-tools:"):
            v = l.split(":", 1)[1].strip()
            if v:
                tools += re.split(r"[,\s]+", v.strip("[]"))
            grab = not v
        elif grab and l.startswith(("-", " ")):
            tools.append(l.strip().lstrip("- ").strip())
        else:
            grab = False
    return [t for t in tools if t]


def render(repo, skills_dir=None):
    name, intro, sections = parse(repo / "README.md")
    out = [f"# {name}", "", f"> {one_liner(intro)}"]
    for alts in SECTIONS:
        head = next((h for h in alts if h in sections), None)
        if head is None:
            continue
        body = tidy(sections[head])
        if body:
            out += ["", f"## {head}"] + body
    extras = ["Language: loomground — guide https://github.com/flxk1/loomground/blob/main/llms.txt (the .lg language an agent reads, emits, validates); catalogue https://github.com/flxk1/loomground/blob/main/CATALOGUE.json"]
    if (repo / "docs" / "language-card.md").exists():
        extras.append("Language card: docs/language-card.md")
    sd = Path(skills_dir) if skills_dir else repo / "skills"
    skills = sorted(p.parent.name for p in sd.glob("*/SKILL.md")) if sd.is_dir() else []
    tools = sorted({t for p in sd.glob("*/SKILL.md") for t in frontmatter(p)}) if skills else []
    if skills:
        extras.append("Skills: " + ", ".join(skills))
    if tools:
        extras.append("MCP tools: " + ", ".join(tools))
    if extras:
        out += [""] + extras
    return "\n".join(fit(out)) + "\n"


def fit(lines):
    while len(lines) > LIMIT:
        heads = [i for i, l in enumerate(lines) if l.startswith("## ")]
        h, e = max(zip(heads, heads[1:] + [len(lines)]), key=lambda s: s[1] - s[0])
        while e > h + 1 and lines[e - 1] == "":
            e -= 1
        want = e - (len(lines) - LIMIT) - 1
        cands = [i for i in range(h + 2, e - 1) if lines[i - 1] != "…"]
        if not cands:
            break
        cut = max([i for i in cands if i <= want], default=cands[0])
        fence = [l for l in lines[h + 1:cut] if FENCE.match(l)]
        close = [fence[0][:3]] if len(fence) % 2 else []
        lines = lines[:cut] + close + ["…"] + lines[e:]
    return lines


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    flags = [a for a in argv if a.startswith("--")]
    if not args:
        print(__doc__); return 2
    repo = Path(args[0]).resolve()
    skills_dir = None
    if "--skills-dir" in flags:
        skills_dir = args[1]
    target = repo / "llms.txt"
    if exempt(target):
        print(f"{repo.name}: llms.txt hand-written (exempt)", file=sys.stderr); return 0
    text = render(repo, skills_dir)
    if "--check" in flags:
        if not target.exists():
            print(f"{repo.name}: llms.txt missing"); return 1
        if target.read_text() != text:
            print(f"{repo.name}: llms.txt drifts from README"); return 1
        print(f"{repo.name}: llms.txt ok ({text.count(chr(10))} lines)"); return 0
    if "--write" in flags:
        target.write_text(text); print(f"{target} ({text.count(chr(10))} lines)"); return 0
    sys.stdout.write(text); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
