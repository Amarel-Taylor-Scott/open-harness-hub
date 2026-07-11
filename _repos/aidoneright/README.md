# aidoneright — the parent brand / portfolio umbrella (`aidoneright-parent`)

The self-contained context repo for **AI Done Right** — the parent brand and holding company of the
portfolio (display brand **AI Done Right**, domain `aidoneright.dev`, tagline **"AI, done right."**; stable
code slug / company id `contextiseverything`). A Claude Code session can open **only this folder** and work
the parent brand fully, edge-aware.

**North star:** be the parent brand and portfolio umbrella that turns open, discoverable AI building blocks
into governed, evidence-backed capability — a house of brands that owns the brands, standards, shared
research/security/governance, and the design system, but **owns no runtime code and no customer data**
(thesis across every property: *discovery is not trust*).

## What this repo is

The parent brand is component **#1** of the six on the portfolio map (`../_shared/ARCHITECTURE-MAP.md`). It
is the legal and strategic umbrella — the brands, the standards strategy, the shared design system and brand
registry, and the cap table — sitting **above** the runtime dependency chain, not inside it. It owns
surfaces, not product logic:

- the **parent portfolio / house-of-brands site** (the "AI Done Right" landing + portfolio index);
- the **Demo Control Tower** (the operator "Start Here" console indexing every site, demo, dashboard, and
  hub, projection-only — it serves no truth);
- the **shared design kit** and the **brand registry** (`products.js`, the single source of brand +
  portfolio identity) that every other surface renders from;
- internal projection consoles (Shared Inference Gateway, Shared Template Registry) — projection-only.

Hard boundary, enforced not asserted: the parent holds `owned_runtime_surfaces == []` and no customer
datastore. Do not add either.

## Layout

- **`CLAUDE.md`** — the agent operating manual for this repo: the project identity, the eight inherited
  laws (linked to `../dev-rules-context/standards/`), the parent's own compatibility contracts, the fast
  path, and safety/scope. Read it before working here.
- **`context/`** — this repo's grounding, self-contained:
  - `blackbox.md` — what the parent **is and owns**: surfaces, subsystems (`products.js`, the capability
    lifecycle spine, the one design law), current state (a high-fidelity design prototype + a live app),
    and pointers to the detailed handoff docs.
  - `edges.md` — how the parent **connects**: where it sits in the dependency law, inbound (design kit +
    brand registry it publishes), outbound (nothing at runtime), the frontend↔backend seams, and the
    compatibility contracts to preserve.
  - `brand/`, `strategy/`, and `contextiseverything-portfolio-infrastructure-split.md` — the detailed
    source material. (The Claude Design family moved to `_repos/_shared/design/aidoneright-claude-design/`;
    the portfolio app-console + sales/lead-funnel briefs to `_repos/_shared/`; the OpenBenchmarkHub brief to
    `_repos/openhubforai/context/`; the old handoff snapshots and 7-site build brief are archived.)
- **`EDGES.md`** — the generated cross-repo edge graph: this repo's role, what it exposes, and the neighbors
  it may consume **via their published interface only**. This is the only cross-repo context a session here
  needs.

## Working in this repo

1. Read `CLAUDE.md`, then `context/blackbox.md`, then `context/edges.md` + `EDGES.md`.
2. Follow the eight inherited laws in `../dev-rules-context/standards/` (they are linked, not copied — the
   standard lives there and wins on any disagreement) plus the parent's own compatibility contracts in
   `CLAUDE.md`.
3. **Reuse-first:** before building anything, check `../_shared/`, a neighbor's published interface
   (`EDGES.md`), or the reference bundle `dist/sites/aidoneright-design/` / `web/context-is-everything/` in
   the main repo. The highest-ROI decision here is *"this already exists, don't rebuild it."*
4. Design changes obey the one design law (edit the shared kit once, differ only by accent + copy); brand /
   strategy / naming changes need clear user intent or strong corroboration — never a unilateral call.

## Edges

This repo's role, from `EDGES.md`: the **parent brand / portfolio umbrella** — it references every surface's
public interface for the portfolio site and owns no product logic.

- **Exposes:** `portfolio-site`, `brand`.
- **May consume (via published interface only):**
  - `aidoneright-dev-rules-context` — `standards/*`, `contracts/surface-registry.json`, `tools/check_*.py`,
    `_shared/*`
  - `aidoneright-teleon` — `/api/teleon`, PurposeTask, runtime-selector, evidence-ledger, promotion-gate,
    assurance-portal
  - `aidoneright-baltor` — `/api/baltor`, context-engine, governance, customer-workflows, receipts
  - `aidoneright-aidevobserver` — `/api/observer`, session-review, mcp-server, cli, extension
  - `aidoneright-openhubforai` — capabilitytask-spec, eval-harnesses, task-templates, conformance-tests,
    skills
- **Downstream consumers:** none yet — but keep `portfolio-site` and `brand` stable regardless.

Consume a neighbor **only** via its exposed interface — never read or import its source. Full map and seam
table: `../_shared/ARCHITECTURE-MAP.md`.
