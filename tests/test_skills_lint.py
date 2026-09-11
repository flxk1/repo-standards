# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""One fixture skill tree per Agent Skills rule the linter enforces."""
import pytest

try:  # the real-YAML branch of skills_lint only exists when a parser is installed
    import yaml  # noqa: F401
    HAVE_YAML = True
except ImportError:  # pragma: no cover
    HAVE_YAML = False
yaml_required = pytest.mark.skipif(not HAVE_YAML, reason="PyYAML not installed (see requirements-dev.txt)")

from conftest import run

CASES = {
    "good": (0, "1/1 skills conform"),
    "triggers-plural": (0, "1/1 skills conform"),  # "Triggers on …" is a trigger clause too
    "no-frontmatter": (1, "no frontmatter"),
    "bad-yaml": (1, "frontmatter is not valid YAML"),
    "extra-key": (1, "key not in standard: version"),
    "bad-name": (1, "name not [a-z0-9-] <= 64"),
    "name-mismatch": (1, "name 'other' != folder 'demo'"),
    "no-description": (1, "description missing"),
    "long-description": (1, "> 1024"),
    "no-when": (1, "description does not say when to use it"),
    "platform-root": (1, "platform-only path root"),
    "missing-path": (1, "referenced path missing: scripts/run.py"),
    "empty": (2, "no SKILL.md found"),
}


@pytest.mark.parametrize("name", CASES)
def test_rule(fix, name):
    if name == "bad-yaml" and not HAVE_YAML:
        pytest.skip("PyYAML not installed (see requirements-dev.txt)")
    want_rc, want = CASES[name]
    rc, out = run("skills_lint.py", fix / "skills" / name)
    assert rc == want_rc, out
    assert want in out


@yaml_required
def test_only_the_conformant_fixtures_conform(fix):
    """Every fixture but `good` and `triggers-plural` breaks exactly one rule."""
    rc, out = run("skills_lint.py", fix / "skills")
    assert rc == 1
    found = list((fix / "skills").glob("*/skills/*/SKILL.md"))  # `empty` holds none
    assert f"2/{len(found)} skills conform" in out, out
