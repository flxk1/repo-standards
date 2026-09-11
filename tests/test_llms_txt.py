# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""llms.txt generation and the --check drift gate."""
import pytest

from conftest import run

CASES = {
    "ok": (0, "llms.txt ok"),
    "drift": (1, "drifts from README"),
    "missing": (1, "llms.txt missing"),
    "exempt": (0, "hand-written (exempt)"),
}


@pytest.mark.parametrize("name", CASES)
def test_check(fix, name):
    want_rc, want = CASES[name]
    rc, out = run("llms_txt.py", fix / "llms" / name, "--check")
    assert rc == want_rc, out
    assert want in out


def test_render_is_the_readme_distilled(fix):
    rc, out = run("llms_txt.py", fix / "llms" / "ok")
    assert rc == 0
    assert out.startswith("# ok")
    assert "## Problem" in out and "## Family" in out
    assert "## Example" not in out          # llms.txt carries the contract sections only


def test_skills_and_tools_are_listed(fix):
    rc, out = run("llms_txt.py", fix / "llms" / "with-skills")
    assert "Skills: alpha" in out
    assert "MCP tools: workspace_ask, workspace_lock" in out


def test_skills_dir_flag(fix):
    rc, out = run("llms_txt.py", fix / "llms" / "ok", "--skills-dir",
                  fix / "llms" / "with-skills" / "skills")
    assert "Skills: alpha" in out


def test_write_then_check_is_clean(fix, tmp_path):
    import shutil

    d = tmp_path / "drift"
    shutil.copytree(fix / "llms" / "drift", d)
    assert run("llms_txt.py", d, "--check")[0] == 1
    assert run("llms_txt.py", d, "--write")[0] == 0
    assert run("llms_txt.py", d, "--check")[0] == 0


def test_no_argument_is_usage(fix):
    rc, out = run("llms_txt.py")
    assert rc == 2 and "--check" in out
