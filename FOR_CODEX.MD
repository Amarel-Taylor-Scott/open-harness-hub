# FOR_CODEX.MD - the review entrypoint (read this first)

> You are a GPT-5.6 Codex reviewer opening this repository. This file orients you fast: what the repo is,
> the one command that tells you if it is healthy, the canonical-vs-legacy map, the rules every change here
> must respect (so you flag real problems, not intended behavior), and where to look. Read this, then
> `docs/BIBLE.md` (the north star) and `CLAUDE.md` (the agent operating rules). If a doc disagrees with the
> BIBLE, the BIBLE wins.

## 1. What this repo is

A holding brand, **AI Done Right** (`aidoneright.dev`), over three product layers plus a usage tool:

| Pillar | What it is | Code | Web surface |
|---|---|---|---|
| **AI Done Right** | parent / holding brand + landing | - | `web/context-is-everything/` |
| **Teleon** (`teleon.dev`) | the eval-gated, self-adaptive compute **runtime** (the optimizing compiler for autonomous work) | `src/teleon/` | `web/teleon/` |
| **Baltor** (`baltor.ai`) | the applied, customer-facing **context** product, powered by Teleon | `src/baltor/` | `web/baltor/` |
| **OpenHubForAI** (`openhubforai.io`) | the open **store** both products consume + the open CapabilityTask spec; ~240 reconciled registries | `src/teleon/registry/` | `web/harness-hub/` |
| **AIDevObserver** | reviews how a team uses AI coding agents (the SESSION, not the code) | `src/teleon/observer/` | `web/aidevobserver/` |

> Folder names are legacy and decoupled from display brands on purpose: `web/context-is-everything/` serves
> "AI Done Right"; `web/harness-hub/` serves "OpenHubForAI". This is intentional, not rot. Do not "fix" it.

**Architectural law** (enforced, see §4): Baltor depends on Teleon depends on OpenHubForAI, **never the reverse**.

## 2. The one command that tells you if it is healthy

```bash
PYTHONPATH=. python3 scripts/run_proofs.py        # runs EVERY registered proof's --self-test; exit code = number RED
```

Every module carries a `--self-test`; `run_proofs.py` runs them all and is the single source of "is it green."
As of this commit it is **all green** (run it for the live count). Two traps to know:

- `scripts/flywheel_proof_modules.py` is only the **registry/list** of proofs - importing or running it is a
  no-op. `run_proofs.py` is what actually executes them. A green from the list alone is a false green.
- "It's green" is necessary, not sufficient. Changes here also carry a **warrant** (§4, change-verification).

Fast inner loop for catalog/page edits is in `CLAUDE.md` ("Default Fast Path"); full gate for schema/vocab changes.

## 3. Architecture in one screen

- **Runtime (Teleon).** `src/teleon/` is an optimizing compiler for autonomous work: a request becomes a
  verified DAG over a registry of components, then descends "make it work -> make it cheap -> deterministic
  substitution." Key seams: `synthesis/` (intent -> DAG), `dag/` (steps), `economics/` (cost/routing),
  `components/` (uniform `invoke` over bespoke ports), `registry/` (the federated registries + `browse`/`port`/
  `compose`/`search`), `observer/` (AIDevObserver engine), `inference/` (model routing).
- **Capability ladders.** Every capability is a cost-ordered, **deterministic-first** descent ladder
  (`architecture/capability_ladders.json`). The LLM is the last rung, not the first.
- **The registries.** ~240 reconciled registries form the spine (`src/teleon/registry/`, single source
  `architecture/*.json`). A registry is a **pointer plus a shape**, not asserted truth. Records come from
  population engines, not hand-building.
- **Surfaces.** Five web apps under `web/<brand>/`, all built on ONE shared kit (`web/<brand>/kit/`,
  React 18 + in-browser Babel, no build step) and differing only in accent + copy. They are SERVED (not
  rebuilt) by the showcase: `OH_PRODUCT=<brand> python3 -m scripts.showcase --port N`. Frontends call
  same-origin seams (`/api/identity/`, `/registry/`, `/api/observer/`, ...) that the showcase proxies to
  local backend services (`scripts/*_local_service.py`, ports in `architecture/local_service_registry.json`).
  Cloud overrides via `OH_SEAM_*_BASE`. The standard is `docs/INTEGRATION-BIBLE.md`; the design system is
  `docs/DESIGN-BIBLE.md` (layout primitives `OhLayout`/`OhTable`, page components `OhBilling`/`OhUsage`/...).

## 4. The rules every change here respects (so you flag real issues, not intended behavior)

These are enforced by checks and/or contracts; treat a violation as a finding, but do not flag the rule itself:

1. **serves_truth=false everywhere except governed Baltor truth output.** Discovery is not trust. A flagged
   conflict is a CANDIDATE a human verifies, never an assertion. `truth_authority=false` on projection stores.
2. **Honest-unavailable is correct.** When a cheap rung is blocked, the code ESCALATES (API -> browser ->
   stealth -> vision) and only then reports unavailable, naming the next rung. An honest "MISSING / not
   reachable" is the intended behavior, not a bug.
3. **Lossless distillation** (`docs/codex/lossless-distillation.md`). Any compression/promotion/optimization
   creates a NEW versioned layer and PRESERVES the raw layer, lineage, held-out + rejected items, rollback.
4. **No magic values** (`docs/codex/no-magic-values.md`). Repo numbers (counts, dimensions, ports, model IDs)
   are computed or single-sourced, never typed twice. A hardcoded count drifting from reality is a classic bug.
5. **Change-verification warrant** (`docs/codex/change-verification-contract.md`). Every change cites clear
   user intent, >=2 agreeing sources, or an established principle - matched to blast radius. Design / brand /
   strategy / pricing changes need user intent, never a unilateral single-agent call.
6. **Move, never delete** (`scripts/archive_legacy_docs.py`). Superseded files move to `archive/legacy/<path>`
   with a status marker; they stay in git for lineage. Generated `web/` files are NOT hand-edited - they are
   ported from the design bundle `dist/sites/openharness-design/` by `scripts/port_full_design_to_web.py`,
   and `check_port_full_design_to_web` enforces byte-for-byte parity. Edit the bundle and re-port.
7. **Scope guards.** Synthetic/public data only (never real PII/secrets). Do not republish `_reference/`.
   Avoid insurance verticals (enforced in code). Per-product auth realms with NO cross-product SSO.

## 5. Where to look

- `docs/BIBLE.md` - the canonical vision + the five pillars + laws (read after this file).
- `CLAUDE.md` / `AGENTS.md` - agent operating rules + the foundational law (the four filters).
- `docs/DESIGN-BIBLE.md` + `docs/INTEGRATION-BIBLE.md` - the design system + the FE<->BE seam standard.
- `src/teleon/` - the runtime engine (start at `registry/`, `synthesis/`, `observer/`, `economics/`).
- `scripts/` - the local services (`*_local_service.py`), the proofs (`check_*.py`, `*--self-test`), and the
  factory tooling. `scripts/run_proofs.py` is the gate; `scripts/codegraph.py --audit <sym>` is the
  change-impact tool.
- `architecture/*.json` - the single-source configs (ladders, registries, service plane, dependency law).
- `dist/sites/openharness-design/` - the design bundle (SOURCE of the `web/` surfaces; do not edit `web/` directly).

## 6. Recently landed (good places to review the patterns end to end)

- **Layout primitives.** `OhLayout` (variants: sidebar / one-col / two-col / no-sidebar) + `OhTable`
  (sortable, click-through) in the shared kit. Every page declares its shape through `OhLayout`.
- **AIDevObserver app** (`web/aidevobserver/aidevobserver-main.jsx`): a logged-in app on
  `OhLayout variant="sidebar"` + `OhTable`, wired to the real observer backend (`scripts/observer_local_service.py`)
  over `/api/observer/*`. Plus four form factors of ONE engine (`src/teleon/observer/`): MCP server, editor
  extension, CLI, and a PreToolUse hook (`scripts/aidevobserver_hook.py`) for live coaching. Read-only; never
  blocks; fail-open.
- **OpenHubForAI registry browser** (`web/harness-hub/proto-registry-browser.jsx`, route `/registries`): a
  faceted `OhTable` browser over the real ~240-registry spine via the seam route `/api/openhub/registries`
  (added to `scripts/registry_local_service.py`, the same engine `src/teleon/registry/browse.py` exposes).

## 7. Known in-flight (so you do not over-report)

- **Brand de-rot is in progress.** The open ecosystem was renamed from "Open Harness Hub" / "OpenHarnessHub"
  and the placeholder "Open\*Hubs" to **OpenHubForAI**, and the parent from "ContextIsEverything" to
  **AI Done Right**. Some docs (and a few surface labels) may still show the old names. The CANONICAL names are
  in this file and `docs/BIBLE.md`. The individual method-spine registries (OpenReconciliationHub,
  OpenHardeningHub, OpenEnrichmentHub, OpenOptimizationHub, OpenVerificationHub, OpenRoutingHub, ...) are REAL
  registry names that live under OpenHubForAI - those are not renamed.

## 8. How to return your review

This repo runs a multi-model review board: `scripts/context_pack_builder.py` builds a non-fragile, whole-repo
context pack; `scripts/external_review.py` / `scripts/panel_review.py` drive lens-based cross-review. A GPT-5.6
Codex pass fits as one lane. Highest-value findings: (a) a place that asserts truth without provenance
(violates §4.1), (b) a hardcoded value that should be computed (§4.4), (c) a destructive/lossy change with no
preserved raw layer (§4.3), (d) a `web/` file hand-edited out of sync with the bundle (§4.6), (e) a proof that
passes without actually exercising the behavior it names. Cite `file_path:line`.
