# NORTHSTAR — the single current-truth entry point

> **Canonical sources — `docs/BIBLE.md`** (the comprehensive vision + laws) + **`docs/DESIGN-BIBLE.md`** (design/UX) — those
> two are canonical now; read them + `CLAUDE.md` first. This file is a deliberately-kept quick index, not a superseded doc. Last reconciled **2026-06-25**.

## The five brand pillars (single source: `architecture/surface_capability_spec.json`)

A holding company, **AI Done Right** (`aidoneright.dev`, "AI, done right."), over three product layers + the wedge:

| Pillar | What it is | Canonical surface |
|---|---|---|
| **AI Done Right** | parent / holding brand | `web/context-is-everything` |
| **Teleon.dev** | the purpose-driven, eval-gated, self-adaptive compute **runtime** | `web/teleon` |
| **AIDevObserver** | watches AI **usage** — reviews the SESSION (post) + helps intra-session (renamed from *Teleon Observer* 2026-06-25) | `src/teleon/observer` (web surface + demo queued) |
| **Baltor.ai** | managed, verified, provable **context**, powered by Teleon | `web/baltor` |
| **OpenHubForAI** | the open **store** both products consume + the open CapabilityTask spec | `web/harness-hub` |

**Architectural law** (enforced by `scripts/check_portfolio_dependency_law.py`): Baltor → Teleon → OpenHarnessHub,
**never the reverse**. Naming/architecture detail: `docs/strategy/teleon-baltor-openharnesshub-portfolio.md` (canonical,
unchanged). Foundational law (the four filters): `architecture/substrate_layers.json`.

## Surfaces are durable + northstar (the 2026-06-25 pass)

- **One design system** (owner 2026-06-25): Baltor · Teleon · AIDevObserver · OpenHubForAI share the SAME layout /
  HTML / CSS / fonts — the shared kit (`shared/oh-site.jsx` + `oh-tokens/components/site.css`) — and differ ONLY in
  color scheme + copy. Enforced by `check_northstar_design` (kit-consistency). AIDevObserver still needs its shared-kit
  surface (today it has a standalone functional `/demo` only).
- The high-fidelity **design source `dist/sites/openharness-design/` is now TRACKED in git** (was caught by `/dist/*`
  ignore → root cause of recurring "the design is gone"). It is the source `port_full_design_to_web.py` ports → `web/`.
- One launcher landing page: `scripts/landing_server.py` → reads live tunnel URLs per request → one URL, all pillars.
- Every surface gets a guided **`/demo`** (owner-directed). Prototypes are hash-routed (`useHashRoute()`).

## The contracts that keep it northstar (gate-enforced — `scripts/run_proofs.py`)

| Contract | File | Guards |
|---|---|---|
| Surface + dev | `scripts/check_surface_and_dev_contract.py` | each pillar's built-out surface EXISTS (not emptied) |
| **Northstar** | `scripts/check_northstar_design.py` | **no placeholder / dummy / side designs** in any surface |
| Dependency law | `scripts/check_portfolio_dependency_law.py` | Baltor→Teleon→OpenHarnessHub only |
| Lossless distillation | `docs/codex/lossless-distillation.md` | distillation never deletes the raw layer |
| No magic values | `docs/codex/no-magic-values.md` | every repo number is computed, not typed twice |
| Change verification | `docs/codex/change-verification-contract.md` | every change carries a warrant |
| Archive (move-not-delete) | `scripts/archive_legacy_docs.py` | outdated docs move to `archive/legacy/`, never deleted |

## What's canonical to KEEP reading (everything else in `docs/strategy/` is point-in-time → archivable)

- `CLAUDE.md` / `AGENTS.md` — agent operating rules.
- `docs/strategy/teleon-baltor-openharnesshub-portfolio.md` — the architecture.
- `docs/strategy/teleon-naming-and-domain.md` + `brand-architecture.md` — naming/brand.
- `docs/strategy/north-stars.md` — the capability-gap selection bar.
- `docs/concepts/*` — the canonical vocabulary (component taxonomy, capability valleys).
