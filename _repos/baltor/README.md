# aidoneright-baltor

Baltor (`baltor.ai`) is the **applied, customer-facing governed-context product** in the AI Done Right
portfolio: fully managed, company-/department-/initiative-wide context that stays **verified, current,
reconciled, traceable, and ready to serve** to whatever agent, RAG system, or workflow platform a customer
already runs. It is **powered by Teleon** as the internal tenant `baltor-internal`, and it **complements
rather than replaces** systems like Jira/Confluence, GitHub/GitLab, Glean, Onyx, Sourcegraph, and the
vector databases.

The product promise, verbatim from the blueprint: *"Any agent can ask for context. Context Fabric returns
the smallest safe, source-linked, versioned, policy-compliant context object or context pack needed for the
task, with relationships, history, lineage, and evidence intact."*

**The moat is governance, not the technique.** Baltor governs what becomes **TRUE**; its durable advantage
is the **governed data + receipts** (provenance, signed facts, source trust, change/revocation handling),
not the algorithm. Method *specifications* can be published to the open store without leaking the moat,
because execution and governed truth stay inside Baltor.

## What this repo is

This is the **context repo** for `aidoneright-baltor` — the standalone, source-cited briefing a Claude Code
session needs to work Baltor edge-aware **without** reading any neighbor repo's internals. It carries the
operating manual (`CLAUDE.md`), the consolidated component context (`context/`), and the published
cross-repo edges (`EDGES.md`). The built-out implementation it describes lives in the parent monorepo under
`src/baltor/` (package root) and `web/baltor/` (the served app); this repo consolidates and cites that,
and is not itself a new authority — if a file here disagrees with the cited source, the source wins.

## Layout

```
_repos/baltor/
├── CLAUDE.md          ← the agent operating manual (fill of the AI Done Right template) — read after the laws
├── README.md          ← you are here
├── EDGES.md           ← the generated cross-repo contract: this repo's role, what it exposes, what it may consume
└── context/           ← the consolidated, source-cited Baltor briefing
    ├── blackbox.md     ← what Baltor internally is, owns, and does (subsystems, invariants, current state)
    ├── edges.md        ← how Baltor connects to the other components (dependency law, seams, contracts)
    └── <topic>/        ← per-subsystem context: contextops/ determinism/ distillation/ native/ runtime/
                          security/ strategy/ status/ ui/ architecture/ backend/ api/ use-cases/ … plus
                          topic briefings (baltor-context-engine-build.md, baltor-determinism-factory.md, …)
```

Its standards are **not copied here** — they live once in
[`../dev-rules-context/standards/`](../dev-rules-context/standards/README.md) (the eight inherited laws) and
the common truth for every component lives in [`../dev-rules-context/_shared/`](../dev-rules-context/_shared/)
(`STANDARDS.md`, `GLOSSARY.md`, `ARCHITECTURE-MAP.md`). `CLAUDE.md` links to them; read from there, never
re-declare them here.

## How to work in this repo

1. Read [`../dev-rules-context/standards/README.md`](../dev-rules-context/standards/README.md) in order —
   the two headline laws (Change Verification, Lossless Distillation) first.
2. Read [`CLAUDE.md`](CLAUDE.md) — the operating layer and Baltor's moat-mechanic invariants.
3. Read [`context/blackbox.md`](context/blackbox.md) + [`context/edges.md`](context/edges.md) +
   [`EDGES.md`](EDGES.md) — what Baltor is/owns and its published edges. Then open the `context/<topic>/`
   folder for the subsystem you are touching.
4. Work the change on the **default fast path**: change one thing, validate/index only the changed paths,
   run the `run_proofs` umbrella; carry a **warrant** proportional to blast radius; audit dependency
   neighbors before and after. Reuse before you build.
5. Honor the Baltor invariants: dependency direction (`Baltor → Teleon → OpenHubForAI`, never reverse);
   agents propose, Baltor disposes; ≥2-source (or authoritative-source-of-record) fact adoption;
   projection-only dashboards; tenant isolation; native format preservation; graceful degrade when Teleon
   is down.

## Edges (from `EDGES.md` — the only cross-repo context a session here needs)

**This repo's role:** the applied, customer-facing CONTEXT product, powered by Teleon (a TENANT).
Governance / provenance / signed facts / CDC is the moat.

**This repo exposes:** `/api/baltor`, `context-engine`, `governance`, `customer-workflows`, `receipts`.

**You may consume (via their published interface only — never read/import their source):**

- **dev-rules-context** (`aidoneright-dev-rules-context`) — `standards/*`,
  `contracts/surface-registry.json`, `tools/check_*.py`, `_shared/*`.
- **shared-backend-components** (`aidoneright-shared-backend-components`) — registry, primitives,
  codegraph, eval-harness, storage-tiers, credential-plane.
- **openhubforai** (`aidoneright-openhubforai`) — capabilitytask-spec, eval-harnesses, task-templates,
  conformance-tests, skills. (Method **specs only** as candidates — discovery ≠ trust; execution + governed
  truth stay in Baltor.)
- **teleon** (`aidoneright-teleon`) — `/api/teleon`, PurposeTask, runtime-selector, evidence-ledger,
  promotion-gate, assurance-portal. Called only through the versioned tenant client as `baltor-internal`,
  with graceful local fallback.

**Who consumes you (keep these interfaces stable):** `aidoneright` (the holding company / parent brand,
which owns no runtime code and no customer data — Baltor exposes nothing "up" to it).
