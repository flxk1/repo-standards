# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Agent Skills conformance (agentskills.io): one SKILL.md per skill dir.

Checks: frontmatter present; only allowed keys (name, description, license,
allowed-tools, metadata, compatibility, plus governance per skill-governance-block); name = lowercase [a-z0-9-], <= 64,
equals the folder name; description <= 1024 and states when to use it; no
platform-only path roots (${CLAUDE_PLUGIN_ROOT}); every relative path the body
references exists next to SKILL.md. Exit 1 on any finding; 2 if no skills found.
Usage: python3 skills_lint.py <root>... """
from __future__ import annotations
import re, sys
from pathlib import Path

ALLOWED = {"name", "description", "license", "allowed-tools", "metadata", "compatibility",
           "governance"}  # governance: the skill-governance-block binding (flxk1/skill-governance-block); runtimes ignore it
NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
WHEN_RE = re.compile(r"\b(use (this )?(skill )?when|when (the )?user|triggers?|use for|use it (to|when)|activates?|should be used when)\b", re.I)
PLATFORM_ROOT = re.compile(r"\$\{?CLAUDE_PLUGIN_ROOT\}?|~/\.claude/|\.claude-plugin/")
REL_PATH = re.compile(r"(?<![\w/.$])((?:references|scripts|assets|docs)/[A-Za-z0-9_./-]+)")
SKIP_DIRS = {"node_modules", ".venv", "venv", "work", "_archive", ".git", "__pycache__", ".circle", ".cube"}


def frontmatter(text: str):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm: dict[str, str] = {}
    key = None
    for line in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if mm:
            key = mm.group(1)
            val = mm.group(2).strip()
            fm[key] = "" if val in (">", ">-", "|", "|-") else val
        elif key and (line.startswith(" ") or line.startswith("\t")):
            fm[key] = (fm[key] + " " + line.strip()).strip()   # folded / literal continuation
    return fm


def check(skill: Path) -> list[str]:
    out = []
    text = skill.read_text(errors="replace")
    fm = frontmatter(text)
    if fm is None:
        return ["no frontmatter"]
    try:  # real YAML parse when a parser is available; the line reader above is the fallback
        import yaml  # type: ignore
        raw = re.match(r"^---\n(.*?)\n---\n", text, re.S).group(1)
        parsed = yaml.safe_load(raw)
        if not isinstance(parsed, dict):
            out.append("frontmatter is not a YAML mapping")
    except ImportError:
        pass
    except Exception as e:  # noqa: BLE001
        out.append(f"frontmatter is not valid YAML: {str(e).splitlines()[0][:80]}")
    for k in fm:
        if k not in ALLOWED:
            out.append(f"key not in standard: {k} (put it under metadata)")
    name = fm.get("name", "")
    if not NAME_RE.match(name):
        out.append(f"name not [a-z0-9-] <= 64: {name!r}")
    if name != skill.parent.name:
        out.append(f"name {name!r} != folder {skill.parent.name!r}")
    desc = fm.get("description", "")
    if not desc:
        out.append("description missing")
    elif len(desc) > 1024:
        out.append(f"description {len(desc)} > 1024")
    elif not WHEN_RE.search(desc):
        out.append("description does not say when to use it")
    body = text.split("\n---\n", 1)[-1]
    if PLATFORM_ROOT.search(body):
        out.append("platform-only path root (${CLAUDE_PLUGIN_ROOT} / ~/.claude / .claude-plugin)")
    for rel in sorted(set(REL_PATH.findall(body))):
        p = skill.parent / rel.rstrip("/").rstrip(".")
        if not p.exists() and not (skill.parent / rel.rstrip("/")).exists():
            out.append(f"referenced path missing: {rel}")
    return out


def main(argv: list[str]) -> int:
    roots = [Path(a) for a in argv] or [Path(".")]
    skills = []
    for r in roots:
        for s in r.rglob("SKILL.md"):
            if any(part in SKIP_DIRS for part in s.parts):
                continue
            skills.append(s)
    if not skills:
        print("no SKILL.md found"); return 2
    bad = 0
    for s in sorted(skills):
        findings = check(s)
        if findings:
            bad += 1
            print(f"FAIL {s}")
            for f in findings:
                print(f"     - {f}")
    print(f"{len(skills) - bad}/{len(skills)} skills conform")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
