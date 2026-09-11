# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""This repository is public. Two things must never enter it: a path from
somebody's machine, and the name of a repository that is not itself public.

The private names are never listed here — a denylist would be the leak. The
check inverts it: every `<owner>/<repo>` this repository mentions is asked of
the PUBLIC GitHub API, unauthenticated. A repository that answers 404 is
private or absent, and either way must not be named here."""
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
URL = re.compile(r"github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9._-]{1,100})")
BARE = r"(?<![\w/.-])({owners})/([A-Za-z0-9._-]{{1,100}})(?![\w/.-])"
MACHINE = re.compile(r"(/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+|C:\\\\Users\\\\)")
def owners() -> set[str]:
    """Whose repositories this text could be naming: the owner of this repository,
    plus every owner already referenced by a full GitHub URL."""
    url = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"],
                         capture_output=True, text=True).stdout.strip()
    m = URL.search(url)
    return {m.group(1)} if m else set()


def tracked():
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True)
    for name in out.stdout.split():
        p = ROOT / name
        if p.is_file() and "fixtures" not in Path(name).parts:
            try:
                yield name, p.read_text(errors="replace")
            except OSError:  # pragma: no cover
                continue


def test_no_machine_paths():
    bad = {n: MACHINE.findall(t)[:3] for n, t in tracked() if MACHINE.search(t)}
    assert not bad, f"a path from somebody's machine is tracked here: {bad}"


def public(slug: str) -> bool:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "repo-standards-leak-check"}
    token = os.environ.get("GITHUB_TOKEN")  # CI supplies one; it lifts the anonymous rate limit
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"https://api.github.com/repos/{slug}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r).get("private") is False
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        if e.code in (403, 429):  # unauthenticated rate limit
            pytest.skip("the public GitHub API rate-limited this run")
        raise


@pytest.mark.skipif(os.environ.get("NO_NETWORK") == "1", reason="needs the public GitHub API")
def test_every_named_repository_is_public():
    texts = list(tracked())
    who = owners()
    for _, text in texts:
        who |= {o for o, _ in URL.findall(text)}
    bare = re.compile(BARE.format(owners="|".join(sorted(map(re.escape, who))))) if who else None
    slugs = set()
    for _, text in texts:
        pairs = set(URL.findall(text)) | (set(bare.findall(text)) if bare else set())
        for owner, repo in pairs:
            repo = repo.removesuffix(".git")
            if repo.endswith((".md", ".py", ".json", ".txt", ".toml", ".yml", ".yaml")):
                continue
            slugs.add(f"{owner}/{repo}")
    try:
        hidden = sorted(s for s in slugs if not public(s))
    except (urllib.error.URLError, TimeoutError) as e:  # pragma: no cover
        pytest.skip(f"GitHub API unreachable: {e}")
    assert not hidden, ("named here but not public — a private or absent repository "
                        f"must not be named in a public repository: {hidden}")
