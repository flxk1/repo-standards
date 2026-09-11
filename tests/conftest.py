# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
DATA = ROOT / "data" / "family.json"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(TOOLS))


def run(tool, *args):
    r = subprocess.run([sys.executable, str(TOOLS / tool), *[str(a) for a in args]],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def rows(out):
    """Parse a verify_text table into {name: (state, problems)}; the sha column may be empty."""
    parsed = {}
    for line in out.splitlines():
        if not line.strip() or re.match(r"^\d+ OK / \d+$", line.strip()):
            continue
        name, rest = line.split(None, 1)
        if rest.startswith("NO README"):
            parsed[name] = ("NO README", "")
            continue
        state, tail = rest.split(None, 1)
        parsed[name] = (state, re.search(r"neg\d+\s*(.*)$", tail).group(1).strip())
    return parsed


@pytest.fixture(scope="session")
def fix(tmp_path_factory):
    """Fixtures copied outside the repo: git calls then report no branch, sha or dirt."""
    d = tmp_path_factory.mktemp("fixtures") / "fixtures"
    shutil.copytree(FIXTURES, d, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
    return d
