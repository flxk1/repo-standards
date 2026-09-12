# Repository standards — flxk1

The per-repo standard for every repository in this account. Modelled on the
sindresorhus discipline — centralize the human ceremony once, make every repo's
mechanical surface byte-predictable, keep the per-repo footprint minimal — and
adapted to this workspace's own rules (REUSE licensing, conformance gates,
governance-grade releases), which are deliberately stricter than the model.

The `repo-standards` skill in this repo applies and audits this document.

## Layer 0 — set once, here (account level)

GitHub serves these to every repo that does not carry its own copy:

- `contributing.md` — the contribution policy (maintainer-time protection).
- `code-of-conduct.md` — Contributor Covenant v2.1, contact `f@nullpunktrec.eu`.
- `SECURITY.md` — default private-disclosure policy. A repository's own
  security policy takes precedence.
- `.github/ISSUE_TEMPLATE/` — bug + idea forms, config routing questions to email.
- Funding is a per-account choice and currently intentionally absent (this
  workspace monetises by commercial licence, not sponsorship).
- The account profile page (its own repository, named after the account) is the storefront, not here.

## Layer 1 — identical in every repo

1. **`.github/workflows/main.yml` is the test workflow.** One name everywhere:
   `main.yml` answers "is this repo green?". Release automation
   (`release-please.yml`), CodeQL, and other workflows live beside it under
   their own names. The workflow stays thin — the repo's own gates/tests do the
   work.
2. **Commit discipline** (CI-enforced in core repositories; the norm
   everywhere): subject ≤ 72 chars; AI assistance is attributed in the body as
   `Assisted by Claude (Anthropic).`
   — never as a `Co-Authored-By` trailer. Squash-merge; atomic commits allowed.
3. **README canon** (lowercase `README.md` or `readme.md`, consistent per repo):
   one-line imperative description → *Install* → *Usage* → *API / Contracts* →
   ***Family*** → *License*. The Family section states the repo's place in the
   plane map — what it consumes, what consumes it — with links, so the graph is
   navigable from any node. The GitHub repo **description** is the same one
   imperative sentence; **topics** are filled in. The account listing is the
   catalog.
4. **Licensing**: product repos are REUSE-compliant — SPDX header in every
   file, a root `LICENSE` for GitHub detection, `LICENSES/` dir, `NOTICE`,
   `REUSE.toml`. Pre-licence repositories
   carry the uniform header
   `Copyright 2026 flxk1 - all rights reserved. License to be determined.`
   until the licence is decided.
5. **Manifest discipline — the manifest is the package's policy patch.** In
   this workspace the manifest is not metadata; it is where the loomground
   mission (local-first, deterministic, auditable, human-authored) becomes
   machine-checkable:
   - `description` = the same one imperative sentence as the README first
     line and the GitHub description — one source for the one-liner.
   - `requires-python` pinned; version single-sourced (`_version.py`),
     managed by release automation.
   - **Dependencies come in three classes only.** (a) None — stdlib-first is
     the default and a feature: local-first means installable offline, and an
     empty dependency tree is the most auditable one. (b) Sibling planes, as
     *published pinned ranges* (`loomground-governance>=0.8,<0.9`) or
     full-SHA git pins pre-publication — never a floating branch, so any
     release can be reinstalled identically. (c) Earned third-party deps —
     each passes the supply-chain gate's licence allow-list and lands in the
     SBOM; if it can't be named why it's there, it isn't.
   - `authors` names the human author(s) only. Generative-AI tools that
     assisted are not authors or copyright holders (RELEASE-DoD rule,
     account-wide).
   - `license` matches `LICENSES/` (REUSE alignment); explicit package
     includes ship the contract, not the workshop — tests, gates, and docs
     stay out of the wheel (the Python `files` whitelist).
   - **Import-time purity is part of the contract**: importing the package
     reads no env, disk, or network. Host couplings ride an optional extra
   (`[host]`), and namespaced entry points (`loomground.adapters`) are the only sanctioned
     ambient discovery — declared in the manifest, where they are visible
     and auditable, never hidden in code.
6. **Shared tooling is consumed, not vendored.** Lint/test/gate configuration
   enters a repo as a dependency or a reusable action, not as a copied file.
   (Known standing violation: `tools/supply_chain_gate.py` is vendored in nine
   repos and drifting — its extraction target is this repo.)
7. **Actions pinned**: by full commit SHA with a version comment; tag-pins are
   the accepted minimum, SHA-pinning is
   the hardening step.
8. **Releases**: repos that release carry `RELEASING.md` + release automation
   (release-please) + a `CHANGELOG.md`. Governance-grade repos keep the
   changelog ledger — the sindresorhus no-changelog habit is deliberately **not**
   adopted. Repos that do not release say so in one line in the README.

### README canon (Layer 1, item 3 — applied to the 33 loomground-family repos 2026-09-10)

Sections, in this order, no others: one-liner under the H1 (= GitHub description = manifest
description) · Problem (≤ 25 words: without this repo, …) · Install | Read · Usage · Example
(executed, `in :` / `out:` verbatim) · Language (+ `docs/language-card.md`; language repos only) ·
Interface | Contracts · Family · Status · License.
Prose rules: declarative sentences; one claim per sentence; no adjective unless technically
defined; no rhetorical questions; no marketing words; no future promises; at most one boundary
negation per README; no architecture rationale (→ docs/); paths, interfaces and examples over prose.
Word budgets (H1 to end): language 450 · engine 420 · agent 370 · contract 320 · measure 220.
Metadata: description non-empty and equal to the one-liner; topics = `loomground` + family topic
(`language-plane`, `evidence-pipeline`, `diagnostic-operator`, `assurance`, `interface`).
Discovery: `llms.txt` generated from the README (`tools/llms_txt.py`, drift-checked); the two
normative repos (loomground, loomground-governance) keep a hand-written language guide.
Skills: Agent Skills format (`skills/<name>/SKILL.md`, `name` = folder, `description` with
"Use when", `allowed-tools` = MCP tool names, relative paths only); checked by `tools/skills_lint.py`.
Audit: `tools/verify_text.py` (budgets, negations, H1, section order, Problem, Example in/out,
Language + card, llms.txt drift) and `tools/verify_layout.py` (skeleton S/P/M/A root set) — both
in this repo, both reading the family instance from `data/family.json`, both runnable against a
single repo (`verify_text.py <repo-dir>`) from a consumer's CI.
Public artefacts never name a private repository (index, catalogue, marketplace, history).

## Layer 2 — per repo

The test command inside `main.yml`, conformance gates, `docs/` (only once the
README overflows), release cadence, and licence choice.

## The narrow-repo footprint (element-grade repos)

For a repo at the single-element grain — one verb-noun, one closed function
family — the target footprint is the p-map ideal mapped to Python:

```
.github/workflows/main.yml   # the one test workflow
src/<package>/               # or a flat module while it fits in one file
tests/
pyproject.toml               # the whole contract
readme.md                    # the docs (canon order, Family section)
LICENSES/  NOTICE  REUSE.toml
CHANGELOG.md                 # only if the repo releases
```

Nothing else until the repo earns it. No `docs/` before the README overflows,
no `src/` layering before a second module exists, no vendored tooling ever.
Every repo looking identical is the scaling mechanism: maintenance becomes
muscle memory and scriptable.

## What green means

`main.yml` green = the repo's own definition of done holds on a clean
checkout. A red main.yml is information, not shame — it is allowed to start
red when it makes real drift visible, and the fix is a
code change, never a gate deletion.
