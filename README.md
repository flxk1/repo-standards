# repo-standards

The rule set every repository in this account is held to, and the four tools that check it.

`STANDARDS.md` is the rule text (layers, README canon, licensing, manifest discipline).
`topology.md` / `topology.yaml` state which repo belongs to which plane and which way the
dependencies point. `data/family.json` is this account's instance of the rules — the repo
list, the kinds, the word budgets, the skeleton root sets. The tools read that file; none of
them hardcodes a repo.

## Tools

| tool | checks |
| --- | --- |
| `tools/verify_text.py` | README canon: word budget per kind, negation budget, marketing words, H1, section order, Family, description length, badges/emoji, Problem (verbatim against the plan table), Example `in :` / `out:`, Language section + card, llms.txt drift |
| `tools/skills_lint.py` | Agent Skills conformance: frontmatter, allowed keys, `name` = folder, description length and trigger, no platform-only path roots, referenced paths exist |
| `tools/llms_txt.py` | generates `llms.txt` from the README; `--check` fails on drift |
| `tools/verify_layout.py` | skeleton root set: required entries present, forbidden entries absent, unlisted entries reported |

## Run them on one repo

```
git clone https://github.com/flxk1/repo-standards /tmp/standards
python3 /tmp/standards/tools/verify_text.py .
python3 /tmp/standards/tools/skills_lint.py .
python3 /tmp/standards/tools/llms_txt.py . --check
python3 /tmp/standards/tools/verify_layout.py .
```

Each exits 1 on a finding. `verify_text.py` takes the repo's kind from `data/family.json`
when the repo is listed there, else `--kind`; the Problem and description checks need
`--plan` / `--descriptions` pointing at the account's planning files.

## Sweep the family

```
python3 tools/verify_text.py            # every repo in data/family.json
python3 tools/verify_layout.py
python3 tools/verify_text.py --repos other-family.json
```

## Tests

```
python3 -m pytest -q
```

`tests/fixtures/` holds one fixture repo per rule — a conformant one and a broken one for
every check the tools make.

## License

Apache-2.0 for the tools and tests, CC-BY-4.0 for the rule text.
