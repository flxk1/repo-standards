# Topology manifest schema (v1)

The portable, machine-readable contract for a **topology manifest** — the file
that declares a multi-module system's planes, repos, and the permitted /
prohibited dependency edges between them. This document is the normative
specification of that manifest's shape and evaluation semantics. `topology.md`
is the *rationale* for one instance of it (this workspace); this schema is the
*generic form* any adopter can target.

The manifest is a small deontic knowledge graph: nodes (repos) typed by plane
and role, edges (dependencies) each permitted or prohibited. The value is not the
declaration but that the declaration is **held** — a declared dependency
direction is enforced.

**Portability contract.** The schema is stdlib-only and engine-agnostic. A
conforming reader needs no third-party dependency: a restricted-subset YAML
(plain scalars, lists of maps; no anchors, aliases, or folded/multiline blocks)
is loadable by a dependency-free parser, and every field below is a plain scalar,
a list of scalars, or a list of flat maps. Nothing in v1 requires a knowledge
graph, a solver, or any external service to validate or evaluate. The reserved
fields (below) are the seams along which a later grounding/solver step attaches
**without a breaking migration** — a v1 reader that ignores them and a later
reader that consumes them read the same file.

---

## TIER

> **TIER: build-time static — no runtime denial, no dynamic-import detection**

This is the honest ceiling of a v1 manifest and its evaluator. The manifest is
checked at build time against declared package dependencies. It does **not** deny
a cross-plane action as it happens at runtime, and it does **not** trace
dynamic imports, reflection, plugin loading, or other indirection that a static
read of declared dependencies cannot see. An adopter whose platform offers more
(a runtime seam that can deny a live cross-plane action) may enforce at a higher
tier, but such enforcement is a separate mechanism layered on top of this
manifest — it is not promised by this schema, and a manifest that claims it must
name the tier it actually runs at.

---

## Top-level shape

A manifest is a single map with these top-level keys:

| key | required | type | purpose |
|---|---|---|---|
| `version` | yes | integer | schema version this file targets |
| `planes` | yes | list of maps | the dependency strata |
| `repos` | yes | list of maps | the nodes, each assigned to a plane and role |
| `allowed_edges` | yes | list of maps | permitted dependency directions |
| `denied_edges` | yes | list of maps | explicit prohibitions, made legible |
| `scan` | no | map | how repos are discovered on disk |

Field-by-field definitions follow.

### `version`

Integer. The schema version the file targets. For this specification,
`version: 1`. A reader that does not recognise the value must refuse the file
rather than guess. Bumping `version` is reserved for a change that alters the
meaning of an existing field; adding a reserved field (below) does **not** bump
it, because a v1 reader validates-but-ignores those fields.

### `planes` — list of `{ id, name }`

Each plane is one stratum in the dependency ordering. Fields:

- **`id`** (string, required) — the stable identifier used by `repos` and by
  edge rules (`from_plane` / `to_plane`). Must be unique across `planes`.
  Treated as an **engine-agnostic stable identifier** (see the note at the end):
  it is an opaque token, never parsed for meaning, so renaming a plane is a
  deliberate manifest change, not something an evaluator infers.
- **`name`** (string, required) — a human-legible label for the plane. Free
  prose; not referenced by any rule.

A plane carries no direction of its own. Direction lives entirely in the edge
rules; `planes` only names the strata those rules range over.

### `repos` — list of `{ id, plane, role, packages }`

Each repo is one node in the graph. Fields:

- **`id`** (string, required) — the repo's stable identifier, unique across
  `repos`. Engine-agnostic and opaque, like a plane id.
- **`plane`** (string, required) — the `id` of the plane this repo belongs to.
  Must match a `planes[].id`; an unknown plane is a validation error.
- **`role`** (string, required) — the repo's role within its plane, drawn from
  the core role vocabulary (below) or an adopter extension. Used by edge rules
  via `from_role` / `to_role`.
- **`packages`** (list of strings, required) — the distribution/import names this
  repo publishes. This is the bridge from the declared graph to observed
  dependencies: an evaluator maps an observed dependency on one of these package
  names back to this repo (and thus to its plane and role). List every alias a
  consumer might pin (e.g. both a hyphenated distribution name and its
  underscored import name).

### `allowed_edges` / `denied_edges` — list of edge patterns

Both lists hold **edge patterns** drawn from one shared key vocabulary. An edge
pattern is a map with any subset of these four keys:

- **`from_plane`** (string, optional) — matches when the *source* repo's plane
  id equals this value.
- **`to_plane`** (string, optional) — matches when the *target* repo's plane id
  equals this value.
- **`from_role`** (string, optional) — matches when the *source* repo's role
  equals this value.
- **`to_role`** (string, optional) — matches when the *target* repo's role
  equals this value.

**Match semantics.** A pattern matches an observed edge when **every key present
in the pattern** equals the corresponding attribute of the edge. Absent keys are
wildcards. A pattern with a single key (`{ to_plane: X }`) therefore matches
every edge into plane `X` regardless of source — the broadest useful rule. An
empty pattern (no keys) matches everything and is a validation error, to prevent
an accidental allow-all or deny-all.

`allowed_edges` states the permitted dependency directions. `denied_edges`
states explicit prohibitions — redundant against deny-by-default, but present so
the prohibition is human-legible and greppable rather than implied by absence.

### `scan` — optional `{ root, max_depth, skip_dirs }`

Controls repo discovery on disk (see **Scan rules** below). All keys optional;
the whole block optional.

- **`root`** (string) — the directory under which repos are discovered. Relative
  paths resolve against the manifest's location, never against a hardcoded
  workspace path — this is what keeps the manifest portable. Default: the
  manifest's own directory.
- **`max_depth`** (integer) — how many directory levels below `root` the walk
  descends before stopping. Bounds the search so a discovery run over a deep
  tree is predictable. This is a **scope-narrowing** field (see Named review).
- **`skip_dirs`** (list of maps) — directories excluded from discovery. Each
  entry is a map `{ name, reason }` (or `{ pattern, reason }`): `name`/`pattern`
  identifies the directory to skip and **`reason`** (string, required on every
  entry) states why. `skip_dirs` narrows what is scanned, so each entry must
  carry a `reason` — an unreasoned skip is a validation error. Typical reasons:
  a staging/build directory that is not source, a vendored tree, a virtual
  environment.

---

## Evaluation — deny-by-default and the exact precedence

Enforcement is **deny-by-default**: any observed dependency edge that is not
positively permitted is denied. An edge is evaluated by walking these rungs **in
this exact order** and stopping at the first that decides:

1. **allowed** — if the edge matches any `allowed_edges` pattern, it **passes**.
2. **denied** — else, if the edge matches any `denied_edges` pattern, it
   **fails**.
3. **intra-plane-same-role auto-pass** — else, if the edge's source and target
   share the same plane **and** the same role, it **passes**. This spares an
   adopter from enumerating every same-plane-same-role edge, while leaving it
   *below* `denied` so an explicit prohibition still overrides it.
4. **none (deny-by-default)** — else, the edge **fails**.

The ordering is load-bearing. `allowed` sits above `denied` so an explicit
permission wins over an overlapping broad prohibition (e.g. a specific
`vertical → engine` allow standing above a broad `to_plane` deny). The auto-pass
rung sits below both so it is a convenience, never an escape hatch: any edge an
adopter genuinely wants blocked can be named in `denied_edges` and it will lose
to that deny even when source and target share a plane and role.

Edges the evaluator cannot resolve to a declared repo (a dependency on a package
not listed in any repo's `packages`) are **out of scope** for the topology
verdict — they are neither an intra-graph edge to permit nor to deny — and should
be reported separately, not silently passed as if permitted.

### Verdict slots

A v1 evaluation is a binary **pass / fail** per edge, aggregated to a
pass/fail for the manifest as a whole (any failing edge fails the run).

A third verdict slot, **`escalate`**, is **reserved** (see below) for a later
tier that can hand a boundary-relevant edge to a human or a governance authority
rather than deciding it outright. The three slots map onto the governance
authority's verdicts as: **pass → GO**, **escalate → CONDITIONAL**,
**fail → NO-GO**. A v1 reader that does not implement `escalate` treats the
manifest exactly as pass/fail; declaring the mapping now is what lets a later
step add the middle slot without changing the schema version.

---

## Scan rules — how repos are discovered

The nodes of the graph are on-disk repositories. Discovery must read **declared
source**, not incidental working-tree content, or it will mistake staging output
for structure. The rules, in order of preference:

1. **Git-tracked-only discovery (preferred).** Where a repo is a git working
   copy, discover its members and packaging from **git-tracked files only**
   (equivalently, the committed tree). Untracked and ignored files are not part
   of the declared structure and must not be read as such. This makes discovery
   reproducible from the committed state and immune to whatever transient files
   happen to sit in the working tree.

2. **Skip staging directories.** Discovery excludes build/staging/vendor
   directories even when they are (accidentally) tracked or present — driven by
   the `scan.skip_dirs` list, each entry reasoned. Reading a staging area as
   structure is the known failure mode a portable manifest must design out, not
   patch around: a staging tree can contain copies of source that would read as
   phantom repos or phantom edges.

3. **Filesystem-walk fallback (non-git working copies).** Where a tree is not a
   git working copy (an exported snapshot, a checkout lacking a `.git`
   directory, a subtree vendored without history), fall back to a plain
   filesystem walk
   under `scan.root`, bounded by `scan.max_depth` and filtered by
   `scan.skip_dirs`. The fallback is strictly less trustworthy than
   git-tracked discovery — it cannot distinguish tracked source from stray
   working files — so it is the last resort, and a run that used it should say so.

Discovery is separable from evaluation: a discovery pass may *propose* a
plane/role mapping for a human to confirm, but the manifest an evaluator reads is
always the confirmed, declared one — discovery never silently rewrites the
declared graph.

---

## Core roles — the portable normative vocabulary

Every repo carries a `role`. The **core role vocabulary is normative** and
portable across adopters — an evaluator understands these four without any
adopter-specific knowledge, and they express the dependency-direction intent on
their own:

| role | meaning |
|---|---|
| **`root`** | the base of a plane stack: depended upon, depends on nothing above it. Nothing points back at a `root` from a higher stratum. |
| **`leaf`** | a consumer at the outer edge: may depend downward on lower strata; nothing depends back on a `leaf`. |
| **`shared`** | a shared member within a plane, available to its plane peers; carries no cross-plane direction of its own. |
| **`boundary`** | a deliberate seam that depends downward on a lower plane's base — the sanctioned cross-plane edge, declared, not a violation. |

These four are the vocabulary an adopter should reach for first, because an
evaluator can reason about direction from them directly.

### Adopter-role layer — explicitly NON-NORMATIVE

Adopters **may** extend `role` with their own names for readability (a role that
reads as the domain rather than as an abstract stratum). This adopter-role layer
is **non-normative**: an evaluator attaches no built-in meaning to an adopter
role, and any direction such a role implies must be spelled out in
`allowed_edges` / `denied_edges` rather than assumed.

This workspace's own roles — for instance `engine` and `vertical` — are named
here **only as an instance extension**, to show the shape of an adopter layer.
They are **not part of the core vocabulary** and must not be treated as portable:
another adopter's manifest neither inherits them nor needs them. When an adopter
role stands in for a core one, mapping it to the nearest core role in prose
(e.g. an `engine`-like role behaves as a `root`; a `vertical`-like role behaves
as a `leaf`) keeps the intent legible without making the extension normative.

---

## Reserved forward-compat fields — validate-but-v1-ignored

The following are **reserved**. A conforming v1 reader **validates their shape if
present but otherwise ignores them** — they carry no v1 semantics. They exist so a
later grounding/solver step can attach without a breaking schema migration: the
same file is read by a v1 evaluator (which ignores them) and by a later evaluator
(which consumes them), and neither has to rewrite the other's manifest.

- **`repos[].obligations`** — a per-repo list, **default `[]`**. Reserved to
  carry deontic obligations attached to a repo (duties a later governance step
  resolves). Validated as a list if present; ignored by a v1 evaluator.
- **`repos[].risk_tier`** — a per-repo scalar, **default `null`**. Reserved to
  carry a risk classification a later step consumes. Validated as scalar-or-null
  if present; ignored by a v1 evaluator.
- **The `escalate` verdict slot** — the third verdict alongside `pass` / `fail`,
  mapping to the governance authority's **CONDITIONAL** (pass → GO, escalate →
  CONDITIONAL, fail → NO-GO). Reserved: a v1 evaluator emits only pass/fail and
  never escalates. Declaring the slot now reserves the middle verdict so a later
  tier adds it without a version bump.
- **Engine-agnostic stable identifiers** — all `id` fields (plane ids, repo ids)
  are opaque, stable tokens with no meaning parsed out of them and no engine
  assumed behind them. A later step may bind an id to a knowledge-graph node or a
  solver symbol, but the manifest neither names nor requires any particular
  engine. Keeping ids engine-agnostic is what lets the same manifest be evaluated
  by the stdlib v1 checker today and by a grounded solver later, unchanged.

---

## Named review — changes are reviewed, narrowing is reasoned

The manifest is a governed artifact, not a convenience file. Two rules bind
changes to it:

1. **Reviewer distinct from author.** Any change to `planes`, `repos`, or the
   edge rules (`allowed_edges` / `denied_edges`) requires a **reviewer who is not
   the author** of the change. Widening what the graph permits, adding or
   re-planing a repo, or moving a plane boundary is a topology decision, and a
   topology decision is not self-approved.
2. **Scope-narrowing requires a stated reason.** Any field that **narrows what is
   scanned or enforced** must carry a reason recorded in the manifest itself. In
   v1 this is enforced concretely on `scan.skip_dirs` — every skip entry carries a
   required `reason` — and it is the general rule for any future narrowing field:
   a narrowing without a stated reason is a validation error. A narrowing is where
   coverage silently disappears, so it is exactly where the reason must be
   visible.

---

## Adopter template

A minimal, portable manifest for a hypothetical layered application. **The role
and plane names below are placeholders** chosen to be generic — they are not this
workspace's roles. They use the core role vocabulary (`root` / `leaf` /
`shared` / `boundary`) precisely because that vocabulary is the portable,
normative one an adopter should start from.

```yaml
# Topology manifest — adopter template (illustrative placeholders).
version: 1

planes:
  - id: platform
    name: Platform
  - id: product
    name: Product

repos:
  # Platform plane: a shared base plus a boundary seam onto it.
  - id: core-lib
    plane: platform
    role: root
    packages: [example-core, example_core]
  - id: platform-utils
    plane: platform
    role: shared
    packages: [example-utils, example_utils]

  # Product plane: leaf consumers, plus a boundary that may reach down.
  - id: web-app
    plane: product
    role: leaf
    packages: [example-web, example_web]
  - id: product-gateway
    plane: product
    role: boundary
    packages: [example-gateway, example_gateway]

  # Reserved fields shown for illustration; validated-but-v1-ignored.
  - id: reporting
    plane: product
    role: leaf
    packages: [example-reporting, example_reporting]
    obligations: []      # reserved (default [])
    risk_tier: null      # reserved (default null)

allowed_edges:
  # Product may depend downward on the platform base.
  - from_plane: product
    to_plane: platform
  # The boundary seam is the sanctioned cross-plane edge.
  - from_role: boundary
    to_role: root

denied_edges:
  # Nothing in the platform base depends back up on the product plane.
  - from_plane: platform
    to_plane: product
  # Leaf consumers do not depend on one another.
  - from_role: leaf
    to_role: leaf

scan:
  root: .
  max_depth: 3
  skip_dirs:
    - name: build
      reason: build output, not declared source
    - name: .venv
      reason: virtual environment, not part of the package graph
    - name: staging
      reason: staging area can mirror source and read as phantom repos
```

Read against the precedence: a `product → platform` dependency matches an
`allowed_edges` pattern and passes at rung 1; a `platform → product` dependency
matches a `denied_edges` pattern and fails at rung 2; two `shared` platform
repos depending on each other pass at rung 3 (same plane, same role) with no
explicit rule; anything else falls through to rung 4 and is denied.
