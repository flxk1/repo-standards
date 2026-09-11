# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Every fixture repo under fixtures/text isolates one README-canon rule."""
import pytest

from conftest import rows, run

EXPECTED = {
    "conformant": ("OK", ""),                                  # one negation is the allowed budget
    "over-budget": ("FAIL", "words 283>220"),
    "two-negations": ("FAIL", "neg 2"),
    "marketing": ("FAIL", "marketing 1"),
    "bad-h1": ("FAIL", "H1"),
    "no-family": ("FAIL", "no Family"),
    "wrong-order": ("FAIL", "order"),
    "badge-emoji": ("FAIL", "badge/emoji"),
    "no-problem": ("FAIL", "no Problem"),
    "problem-drift": ("FAIL", "Problem not verbatim"),
    "no-example": ("FAIL", "no Example"),
    "example-no-in-out": ("FAIL", "Example lacks in/out"),
    "no-description": ("FAIL", "no description"),
    "long-description": ("FAIL", "desc 177"),
    "llms-drift": ("FAIL", "llms.txt drift"),
    "llms-missing": ("FAIL", "llms.txt missing"),
    "no-language": ("FAIL", "no Language"),
    "no-card": ("FAIL", "no card"),
    "lang-exempt": ("OK", ""),                                 # listed language repo, card exempt
    "no-readme": ("NO README", ""),
}


@pytest.fixture(scope="module")
def sweep(fix):
    rc, out = run("verify_text.py", "--repos", fix / "text" / "family.json")
    return rc, rows(out)


@pytest.mark.parametrize("name", EXPECTED)
def test_rule(sweep, name):
    assert sweep[1][name] == EXPECTED[name]


def test_sweep_covers_every_fixture_and_fails(sweep):
    rc, parsed = sweep
    assert set(parsed) == set(EXPECTED)
    assert rc == 1


def test_single_repo_pass(fix):
    rc, out = run("verify_text.py", fix / "text" / "conformant", "--repos", fix / "text" / "family.json")
    assert rc == 0 and "conformant" in out and "OK" in out


def test_single_repo_fail(fix):
    rc, out = run("verify_text.py", fix / "text" / "bad-h1", "--repos", fix / "text" / "family.json")
    assert rc == 1 and "H1" in out


def test_single_repo_needs_no_family_file(fix):
    """A repo nobody listed still gets checked, on the default kind."""
    rc, out = run("verify_text.py", fix / "text" / "conformant")
    assert rc == 0


def test_kind_flag_sets_the_budget(fix):
    d = fix / "text" / "over-budget"
    fam = fix / "text" / "family.json"
    assert run("verify_text.py", d, "--repos", fam)[0] == 1
    assert run("verify_text.py", d, "--repos", fam, "--kind", "spec")[0] == 0


def test_plan_flag_drives_the_verbatim_check(fix):
    d = fix / "text" / "problem-drift"
    fam = fix / "text" / "family.json"
    assert "Problem not verbatim" not in run("verify_text.py", d, "--repos", fam)[1]
    rc, out = run("verify_text.py", d, "--repos", fam, "--plan", fix / "text" / "plan.md")
    assert rc == 1 and "Problem not verbatim" in out


def test_descriptions_flag_drives_the_description_check(fix):
    d = fix / "text" / "long-description"
    fam = fix / "text" / "family.json"
    assert "desc " not in run("verify_text.py", d, "--repos", fam)[1]
    rc, out = run("verify_text.py", d, "--repos", fam, "--descriptions", fix / "text" / "descriptions")
    assert rc == 1 and "desc 177" in out


def test_name_flag_overrides_the_directory_name(fix):
    rc, out = run("verify_text.py", fix / "text" / "bad-h1", "--name", "wrong-name")
    assert "H1" not in out


def test_check_readme_is_importable(fix):
    import verify_text

    probs, words, neg = verify_text.check_readme(
        fix / "text" / "two-negations", "two-negations", "spec", {"spec": 450})
    assert probs == ["neg 2"] and neg == 2 and words > 0


def test_check_readme_reports_missing_readme(fix):
    import verify_text

    assert verify_text.check_readme(fix / "text" / "no-readme", "no-readme", "spec", {"spec": 450}) is None
