# Repo topology — the three-plane system

The operating model has three planes: **ctrl orchestrates · RVND enforces ·
Loomground grounds.** That is a *runtime* relationship (a task flows
orchestrate → govern → ground). The repos answer a different question —
ownership, release cadence, who consumes what. This document states which repos
belong to which plane and, above all, which way the dependencies point.

The planes are a **lens over independent repos**, not a repo layout. Nothing
here collapses the repos into three; each stays its own tree with its own
cadence and owner.

## The three planes

### 1. Orchestration plane — ctrl (the *how*; the outer ring)

Plugin directories at `Projects/` top level, delivered through a marketplace
rather than as engine repos:

- `ctrl-engineering/` — the core: skills, gates, `team-charter.md`, hooks,
  `pyproject.toml`. The standing-team machinery.
- `ctrl-arena/`, `ctrl-panel/`, `ctrl-build-arena/` — the mode plugins.
- Delivery: `loomground-writing/_ctrl-marketplace/` + the `install-ctrl-family`
  tool. (See the marketplace decision below — this is slated to move out.)

ctrl is not a peer of the other two — it *consumes* them: the
`policy-compliance` role calls RVND, the `grounding` role calls Loomground.

### 2. Governance plane — RVND (what work is *governed by*)

`rvnd-repos/` — eight independent repos, `flxk1/*` remotes. One engine plus a
fan of verticals that depend on it (the verticals are not peers of the planes):

- Engine: `RVND/`
- Oversight: `rvnd-oversight/`
- Verticals / packs: `rvnd-music/`, `rvnd-judiciary/`, `rvnd-education/`,
  `rvnd-employment/`, `rvnd-family/` (no remote yet), `rvnd-pack/`

### 3. Knowledge plane — Loomground (what work is *grounded in*)

`loomground-repos/` — the versum knowledge graph, deontic planes, and the
editorial/marketplace stack. Many repos; owned by **separate sessions** and
released on their own cadence. Representative members (not exhaustive):

- Substrate: `versum/`, `loomground-governance/`, `loomground-patchbay/`,
  `loomground-proof/`, `loomground-epistemic/`, `loomground-factual/`,
  `loomground-falsifiability/`, `loomground-multiversum/`, `loomground-workspace/`
- Delivery / editorial: `loomground-plugins/` (marketplace index),
  `loomground-writing/` (editorial + the ctrl marketplace, for now)

> `Loomground/` and `Loomground Blog/` at `Projects/` top level are separate
> again and remain hands-off.

## What makes it a *system*: dependency direction

The system is the direction the arrows point, not co-location. This is already
the honest shape; the job is to state it and hold to it.

```
                 ┌─────────────────────────────┐
                 │   ctrl  (orchestration)      │   outer ring
                 │   ctrl-engineering + modes   │
                 └──────┬───────────────┬───────┘
             uses       │               │      uses
        (policy-        │               │   (grounding)
         compliance)    ▼               ▼
        ┌───────────────────┐   ┌────────────────────┐
        │ RVND (governance) │   │ Loomground         │
        │ engine + verticals│   │ (knowledge)        │
        └─────────▲─────────┘   └────────────────────┘
                  │ depend on
        ┌─────────┴──────────┐
        │  rvnd-* verticals   │
        └────────────────────┘
```

Rules the arrows imply. The single invariant is directional: **dependencies
point one way, toward the base — nothing depends backwards.**

1. **ctrl may depend on RVND and Loomground.** Nothing depends back on ctrl.
2. **RVND depends on Loomground.** RVND is a governance *seam* built on the
   Loomground base — it pins Loomground packages directly (solver, versum,
   governance language, deontic, …). This downward edge is the architecture, not
   a violation.
3. **Loomground never depends backwards.** It is the base: it never depends on
   RVND or ctrl. So the flow is `ctrl → RVND → Loomground` (and `ctrl →
   Loomground`), with no edge pointing back up and no cycles.
4. **Verticals depend only on the RVND engine** — not on each other and not on ctrl.
5. **Intra-plane edges are fine.** A plane's repos may depend on each other (ctrl
   modes on the ctrl core; Loomground's index and editorial on the Loomground
   base). The only intra-plane exception is rule 4's vertical → vertical.

## Enforcement — Level 2, as a real RVND gate

The topology is not advisory. The three arrow-rules above are enforced by a
**first-class RVND gate** — a new entry in `make gates` alongside the existing
`surface`, `lock-boundary`, `egress-guard`, `patchbay-consumption` checks — not a
lookalike check living elsewhere. A violation (an upward or sideways cross-plane
dependency) **fails the gate** and blocks the PR, exactly as the other gates do.

Design note (to settle when the gate is built): the repos are independent, not
submodules, so the gate cannot walk imports across trees directly. It checks
each repo against a **declared topology manifest** — the plane each repo belongs
to and its allowed cross-plane edges — and fails when a repo's actual
dependencies exceed what its plane permits. The manifest is the machine-readable
form of this document; this document is its rationale. Building the gate is a
scoped RVND engineering task: route through ctrl orchestration, `make gates`
green before any PR.

## Decisions on file

- **Enforcement level:** Level 2 — map **plus** an enforced dependency rule,
  implemented as an RVND gate (above), not merely "in the spirit of" one.
- **Home:** this file (`repo-standards/topology.md`), with a one-line pointer
  from `Projects/CLAUDE.md`. repo-standards is the one place already sitting
  above individual repos.
- **ctrl marketplace:** to move out of `loomground-writing/` so the planes stay
  clean — delivery-coupling of the orchestration plane to the knowledge plane is
  a wrinkle, not a keeper. Execution is a reserved restructuring step (repo/dir
  moves are Felix's to run); recorded here as the agreed direction, not yet done.

## What this does NOT do

- No repo is created, moved, merged, renamed, or restructured by this document.
- `rvnd-repos/`, `loomground-repos/`, `Loomground/`, `Loomground Blog/` are
  untouched — independent and separately owned.
- No monorepo; no literal three-repo collapse.
- Nothing is pushed. Repo creation, moves, and releases stay reserved for Felix.
