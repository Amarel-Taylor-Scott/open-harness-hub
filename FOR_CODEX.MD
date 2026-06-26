# FOR_CODEX.MD - the review brief (read this first)

> You are a GPT-5.6 Codex reviewer opening this repository. This is your operating manual: what the repo is,
> the one command that says if it is healthy, and - the point of this file - **how to actively review it** across
> five dimensions (correctness, contracts, context rot, context management, verification honesty), with the exact
> commands to run and what a real finding looks like. Read this, then `docs/BIBLE.md` (north star) and `CLAUDE.md`
> (agent operating rules). If a doc disagrees with the BIBLE, the BIBLE wins. Do not just read - run the checks,
> trace the claims, and report findings as `file_path:line` with the contract or dimension each one violates.

---

## 1. What this repo is

A holding brand, **AI Done Right** (`aidoneright.dev`), over three product layers plus a usage tool:

| Pillar | What it is | Code | Web surface |
|---|---|---|---|
| **AI Done Right** | parent / holding brand + landing | - | `web/context-is-everything/` |
| **Teleon** (`teleon.dev`) | the eval-gated, self-adaptive compute **runtime** (the optimizing compiler for autonomous work) | `src/teleon/` | `web/teleon/` |
| **Baltor** (`baltor.ai`) | the applied, customer-facing **context** product, powered by Teleon | `src/baltor/` | `web/baltor/` |
| **OpenHubForAI** (`openhubforai.io`) | the open **store** both products consume + the open CapabilityTask spec; ~240 reconciled registries | `src/teleon/registry/` | `web/harness-hub/` |
| **AIDevObserver** | reviews how a team uses AI coding agents (the SESSION, not the code) | `src/teleon/observer/` | `web/aidevobserver/` |

> Folder names are legacy and decoupled from display brands ON PURPOSE: `web/context-is-everything/` serves
> "AI Done Right"; `web/harness-hub/` serves "OpenHubForAI". This is intentional, not rot. Do not "fix" it.
> **Architectural law** (enforced, see §5): Baltor depends on Teleon depends on OpenHubForAI, never the reverse.

## 2. The one command that says if it is healthy

```bash
PYTHONPATH=. python3 scripts/run_proofs.py        # runs EVERY registered proof's --self-test; exit code = number RED
```

Every module carries a `--self-test`; `run_proofs.py` runs them all and is the single source of "is it green."
As of this writing it is **all green** (run it for the live count). "It's green" is **necessary, not sufficient** -
§8 is about whether the greens are honest.

## 3. Architecture in one screen

- **Runtime (Teleon).** `src/teleon/` is an optimizing compiler for autonomous work: a request becomes a verified
  DAG over a registry of components, then descends "make it work -> make it cheap -> deterministic substitution."
  Seams: `synthesis/` (intent -> DAG), `dag/`, `economics/` (cost/routing), `components/` (uniform `invoke`),
  `registry/` (federated registries: `browse`/`port`/`compose`/`search`), `observer/` (AIDevObserver), `inference/`.
- **Capability ladders.** Every capability is a cost-ordered, **deterministic-first** descent ladder
  (`architecture/capability_ladders.json`). The LLM is the last rung, not the first.
- **The registries.** ~240 reconciled registries (single source `architecture/*.json`). A registry is a **pointer
  plus a shape**, not asserted truth; records come from population engines, not hand-building.
- **Surfaces.** Five web apps under `web/<brand>/` on ONE shared kit (`web/<brand>/kit/`, React 18 + in-browser
  Babel, no build step), differing only in accent + copy. SERVED (not rebuilt) by the showcase
  (`OH_PRODUCT=<brand> python3 -m scripts.showcase --port N`). Frontends call same-origin seams (`/api/identity/`,
  `/registry/`, `/api/observer/`, ...) proxied to local services (`scripts/*_local_service.py`, ports in
  `architecture/local_service_registry.json`). Standard: `docs/INTEGRATION-BIBLE.md`; design: `docs/DESIGN-BIBLE.md`.

---

## 4. How to review this repo (five dimensions)

This is not a normal app. It is a context/capability platform with self-imposed governance. Review it across:
**(A) correctness** (does the code do what it says), **(B) contracts** (§5), **(C) context rot** (§6),
**(D) context management** (§7 - the repo is a context platform, so audit its own context hygiene), and
**(E) verification honesty** (§8 - are the greens real). The step-by-step protocol is §9.

## 5. The contracts (audit each; a violation is a finding, not the rule)

Each row: the contract, where it is defined/enforced, and what a violation looks like.

| Contract | Defined / enforced by | A violation looks like |
|---|---|---|
| **serves_truth=false except governed Baltor** | per-module self-tests; `truth_authority=false` on stores | a response asserting a fact as truth outside Baltor, or a flagged candidate presented as verified |
| **Honest-unavailable / descent** | `architecture/capability_ladders.json`; honest "MISSING" returns | giving up at a blocked rung without escalating, or faking a result instead of returning honest-unavailable |
| **Lossless distillation** | `docs/codex/lossless-distillation.md` | a compression/promotion/optimization that drops the raw layer, lineage, held-out/rejected items, or rollback; no rehydration proof |
| **No magic values** | `docs/codex/no-magic-values.md`; `scripts/audit_magic_numbers.py` | a repo count/dimension/port/model-id typed twice or hardcoded in prose that can drift from the computed source |
| **Change-verification warrant** | `docs/codex/change-verification-contract.md` (+ its decision ledger) | a change with no cited warrant; a design/brand/strategy/pricing change made unilaterally (those need clear user intent) |
| **Dependency law** | `scripts/check_portfolio_dependency_law.py` over `architecture/portfolio_dependency_law.json` | Teleon importing Baltor, or OpenHubForAI importing either (the arrow only points down) |
| **Move, never delete** | `scripts/archive_legacy_docs.py`; `archive/legacy/_manifest.jsonl` + README | a superseded file deleted/untracked instead of moved to `archive/legacy/` with a status marker |
| **Design bundle -> web port** | `scripts/port_full_design_to_web.py --check` | a `web/` file hand-edited out of sync with `dist/sites/openharness-design/` (it must match byte-for-byte) |
| **Codegraph change-audit** | `scripts/codegraph.py --audit <file\|symbol>`; `docs/codex/codegraph-change-audit-protocol.md` | a changed API whose load-bearing callers were not updated in the same change |
| **Scope guards** | code + review | real PII/secrets in the tree; `_reference/` republished; new insurance-vertical work |

```bash
PYTHONPATH=. python3 scripts/check_portfolio_dependency_law.py --self-test   # the arrow only points down
python3 scripts/audit_magic_numbers.py                                       # hardcoded values that should be computed
python3 scripts/port_full_design_to_web.py --check                          # web/ == design bundle, byte-for-byte
PYTHONPATH=. python3 scripts/codegraph.py --audit <symbol>                  # blast radius of a change
```

## 6. Context-rot audit (stale / contradictory / unverifiable content)

This repo's #1 self-identified risk is rot: docs that say superseded things as if current, "current-state"
snapshots frozen at an old state, and claims that name a file/flag/function that no longer exists. Hunt it:

```bash
python3 scripts/archive_legacy_docs.py --scan        # superseded-marked docs still sitting in the live tree
PYTHONPATH=. python3 scripts/run_proofs.py check_handoff_docs_freshness     # the handoff bundle is fresh
PYTHONPATH=. python3 scripts/run_proofs.py check_context_freshness          # canonical/context docs are fresh
# brand/vocab rot (exclude archive/legacy, _reference, node_modules, .git):
grep -rnE "Open Harness Hub|ContextIsEverything|Purpose Runtime|knowledge pack|rule pack" docs/ src/ web/ --include=*.md
```

What to flag (with `file:line`):
- A LIVE doc (not under `archive/legacy/`) presenting a superseded brand/vocab/structure as current (see §11 for
  what is intentionally kept vs. what is rot).
- A "current-state / status / snapshot" doc whose content contradicts the code or a newer canonical doc
  (orphaned contradiction: a decision was superseded but the old artifact was left live - the contract says update
  or delete the stale artifact in the SAME change).
- **A claim that names a file, flag, function, or count that no longer matches reality.** A memory/doc that says
  "X lives in `path`" or "the flag is `--y`" is a claim about a PAST state - re-verify it before trusting it. This
  is the highest-value rot to find.
- The known generated-doc-source rot (recorded, not yet fixed): old brand strings live in DATA/scripts, not the
  generated output - `catalog/**/*.yaml` provenance strings, `scripts/emit/*`, `scripts/build_index_page.py`, and
  the `LOCKED_BRANDS` constant in `scripts/check_prelaunch.py`. Fixing the generated `.md` directly would be wrong;
  flag the SOURCE.

## 7. Context-management audit (the repo is a context platform - audit its own context hygiene)

The product governs context, so its own context system is fair game and is the most on-theme thing to review:

- **The non-fragile context pack:** `scripts/context_pack_builder.py` builds a layered, whole-repo context that
  resists truncation hallucinations. Audit: does it preserve answer-critical facts + source handles; does it stay
  fresh; does it keep tenant-private lineage out of any global pack?
- **Rot / debt / compression / graph:** `scripts/ingest/context_rot.py`, `scripts/context_debt.py`,
  `scripts/context_compress.py`, `scripts/context_graph.py`, `scripts/context_swarm.py`. Audit: does compression
  shrink only the text surface while keeping answer-critical facts + source handles + held-out warnings (the
  lossless rule, §5)? does it detect oversized / duplicate context?
- **Cache-shaped context / prompt-ABI:** `docs/architecture/prompt-abi-and-cache-shaped-context.md`,
  `docs/architecture/trajectory-fragment-cache.md`, `docs/architecture/context-control-loop.md`.
- **Dogfood AIDevObserver** (it exists to catch wasted context). Run it over a session and see if it flags
  oversized/duplicate context and reinvention - then ask whether THIS repo's own context construction would pass:

```bash
python3 -m src.teleon.observer.cli review --latest      # observer over the latest local session (read-only)
```

A good finding here: context that is compressed lossily (a fact or source handle dropped), oversized/duplicated
context that the system itself would flag, or a context pack that has drifted from the repo it claims to describe.

## 8. Verification-honesty audit (are the greens real)

"Green" is necessary, not sufficient. Look for false confidence:

- **The no-op trap:** `scripts/flywheel_proof_modules.py` is only the registry/LIST of proofs - running or importing
  it proves nothing. Only `scripts/run_proofs.py` actually executes the self-tests. A "suite passed" that only ran
  the list is a false green.
- **Hollow proofs:** a `--self-test` that asserts nothing meaningful, passes because the thing it checks is absent,
  or asserts a hardcoded number instead of a computed one (drifts silently). Spot-check 3-5 `check_*` / `--self-test`
  blocks and confirm each exercises the behavior it names.
- **Warrant:** every change carries one (clear user intent / >=2 agreeing sources / an established principle), matched
  to blast radius; design/brand/strategy/pricing need user intent, never a unilateral single-agent call. Check recent
  commits + the decision ledger (`docs/codex/change-verification-contract.md`).
- **Lossless rehydration:** for any distillation, the contract requires PROVING the raw layer rehydrates - confirm
  the proof exists, not just the claim.

## 9. The review protocol (do these in order)

1. **Health.** Run the gate (§2). Note any RED. Spot-check 3 proofs for real assertions (§8).
2. **Contracts.** Run the §5 commands; spot-audit each contract; record violations.
3. **Context rot.** Run §6; verify the claims in the canonical docs (`docs/BIBLE.md`, `CLAUDE.md`, `docs/CURRENT-STATE.md`)
   against the code; flag any name/flag/count that no longer matches.
4. **Context management.** Audit §7; dogfood AIDevObserver; check compression is lossless.
5. **Architecture.** Trace ONE capability end-to-end (intent -> DAG -> cheapest rung) in `src/teleon/`; verify the
   dependency law holds in code, not just in the doc.
6. **Surfaces.** Bring up the five surfaces (showcase + the local services); confirm seam wiring + 0 console errors;
   confirm `web/` matches the bundle (§5).
7. **Truth discipline.** `grep -rn "serves_truth.*[Tt]rue\|truth_authority.*[Tt]rue" src/ scripts/` and confirm every
   hit is governed Baltor truth output, not a candidate dressed as fact.
8. **Synthesize.** Report findings (§10).

## 10. How to return your review

Highest-value findings, in order: (a) a place that asserts truth without provenance (§5 serves_truth), (b) a lossy/
destructive change with no preserved raw layer or rehydration proof (§5 lossless), (c) a hardcoded value that should
be computed (§5 no-magic-values), (d) a doc/claim that names a file/flag/function/count that no longer matches reality
(§6), (e) a `web/` file out of sync with the bundle (§5 port), (f) a proof that passes without exercising the behavior
it names (§8). Format each as:

```
[severity] file_path:line  -  <dimension/contract>  -  <one-line claim>
  evidence:  <what you ran / saw>
  fix:       <smallest change that resolves it>
```

This repo runs a multi-model review board: `scripts/context_pack_builder.py` builds the whole-repo context pack and
`scripts/external_review.py` / `scripts/panel_review.py` drive lens-based cross-review. A GPT-5.6 Codex pass is one lane.

## 11. Known in-flight (so you do not over-report)

- **Brand de-rot is in progress.** The open ecosystem was renamed from "Open Harness Hub" / "OpenHarnessHub" and the
  placeholder "Open\*Hubs" to **OpenHubForAI**; the parent from "ContextIsEverything" to **AI Done Right**. The
  CANONICAL names are in §1 and `docs/BIBLE.md`. **Intentionally kept (NOT rot):** (a) the dependency-law direction
  tokens `Baltor -> Teleon -> OpenHarnessHub` (matching `architecture/portfolio_dependency_law.json`); (b) the
  individual method-spine / harness registries (OpenHarnessHub as a named registry, OpenReconciliationHub,
  OpenContextHub, OpenSkillsHub, ...) - those live UNDER OpenHubForAI and are real names; (c) `OpenHarnessHub
  Prototype.html` filenames; (d) "ContextIsEverything" where framed as the legacy founding thesis; (e) the
  `Open*Hubs are registries` boundary phrase that `check_handoff_docs_freshness` requires verbatim.
- **Generated-doc sources** still carry old brand strings in DATA/scripts (see §6, last bullet) - flag the source,
  not the generated output.
- **Two self-marked historical snapshots** (`docs/portfolio-web-surface-inventory.md`,
  `docs/codex/codebase-review-2026-06-09.md`) are kept in the live tree with explicit "SUPERSEDED / snapshot"
  headers; they can later move to `archive/legacy/`.
