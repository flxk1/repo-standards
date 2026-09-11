# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Skeleton root sets: one fixture repo per deviation class, checked against the repository data."""
import json

import pytest

from conftest import DATA, run

CASES = {
    "good": (0, []),
    "forbidden": (1, ["forbidden=['LICENSE', 'scripts']"]),
    "missing": (1, ["missing=['NOTICE', 'REUSE.toml']"]),
    "unknown": (0, []),        # an unlisted root entry is reported, not a deviation
}


@pytest.mark.parametrize("name", CASES)
def test_root_set(fix, name):
    rc, out = run("verify_layout.py", fix / "layout" / name)
    want_rc, want = CASES[name]
    assert rc == want_rc
    assert ("OK" if want_rc == 0 else "DEVIATES") in out
    for w in want:
        assert w in out


def test_sweep_reads_the_repo_list(fix, tmp_path):
    fam = json.loads(DATA.read_text())
    fam["root"] = str(fix / "layout")
    fam["repos"] = []
    fam["layout"]["search"] = {"worktree": "{name}", "clone": "{name}"}
    fam["layout"]["worktrees"] = ["good", "forbidden", "missing", "unknown"]
    fam["layout"]["clones"] = ["never-cloned"]
    f = tmp_path / "family.json"
    f.write_text(json.dumps(fam))
    rc, out = run("verify_layout.py", "--repos", f)
    assert rc == 1
    assert out.splitlines()[0].startswith("good ") and "OK" in out.splitlines()[0]
    assert "never-cloned" in out and "NOT STARTED" in out
    assert out.count("DEVIATES") == 2


def test_unknown_root_entry_is_reported(fix):
    import verify_layout

    sets = verify_layout.load_family(DATA)[0]["layout"]  # rules.json merged into the instance
    state, detail, *_ = verify_layout.check_root(fix / "layout" / "unknown", sets)
    assert state == "OK" and "unknown=['attic']" in detail


def test_check_root_is_importable(fix):
    import verify_layout

    sets = verify_layout.load_family(DATA)[0]["layout"]  # rules.json merged into the instance
    state, detail, dirty, br, sha = verify_layout.check_root(fix / "layout" / "good", sets)
    assert state == "OK" and detail == "forbidden=[] missing=[] unknown=[]"
