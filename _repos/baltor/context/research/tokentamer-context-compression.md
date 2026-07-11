# TokenTamer — context compression for the inference plane (fork research)

**Date:** 2026-06-08. **Owner request:** "Research TokenTamer and design a GOVERNED context-compression
integration (fork direction), as research infra." **Verify-first:** the TokenTamer facts below were
web-confirmed from the repository (sources at the bottom); confidence is stated per claim. **Maps to:**
Baltor.ai **Compress** module · the **Context Optimizer** stage of the inference plane (compress before
route) · compression-as-a-**deterministic tool** in the agent gateway · the lossless-distillation law
(`_repos/shared-backend-components/docs/codex/lossless-distillation.md`).

> **LOSSLESS DISTILLATION CLAUSE:** Any distillation, decomposition, compression, optimization,
> reconciliation, promotion, or LLM-to-rule conversion must be lossless at the system level. Never
> overwrite or delete raw/source/intermediate artifacts. Every derived artifact must preserve source
> handles, lineage, transform config, version, receipts, held-out items, rejected candidates, and a
> rollback target. Run side-by-side before promotion, run shadow mode for new rules, monitor after
> promotion, and prove rehydration. Omitted means held out or excluded from a view, never erased.

> **Connect, don't duplicate.** The compression **landscape** (Headroom, LLMLingua/-2, EXIT, the
> reversible-vs-lossy taxonomy, the `compression` capability slot) already lives in
> `_repos/baltor/context/research/context-compression-tools.md`. This doc is narrower and different in **shape**:
> TokenTamer is a **proxy-level code-context skeletonizer** (it rewrites the request payload an agent
> sends), not a chunk/token compressor. The catalog for this shape is
> `_repos/shared-backend-components/architecture/context_compression_provider_catalog.json` (checked by
> `_repos/shared-backend-components/scripts/check_context_compression_catalog.py`); it is deliberately separate from the chunk-compressor
> `compression` slot in `_repos/shared-backend-components/architecture/external_capability_catalog.json`.

---

## 1. What TokenTamer is (verified)

[borhen68/TokenTamer](https://github.com/borhen68/TokenTamer) is a **local FastAPI proxy** that sits between
an AI coding agent (Aider, Cursor, Claude Code, Codex) and the LLM API, rewriting the request payload to cut
tokens **before** it reaches the model. (Confidence: **high** — confirmed from the repo README.)

- **Skeletonization, not summarization.** It identifies which files are **actively being edited** vs.
  **background** context. Active files are left **intact**; background code is **skeletonized** — function
  and method bodies are replaced with `...` while signatures and class structure are preserved. The README's
  example collapses a `calculate_tax(amount: float, region: str) -> float` body to a single `...`. (Confidence: **high**.)
- **Language coverage by mechanism.** Python uses native **`ast`** parsing; JS/TS/Go/Rust/Java/C#/C/C++ use a
  **brace-balance heuristic** (count `{`/`}` to find body spans). So Python skeletonization is structurally
  sound; the non-Python path is a heuristic that can mis-cut on edge cases (strings/comments containing
  braces, macros, template syntax). (Confidence: **high** for the approach; the heuristic's accuracy is **not** measured.)
- **Endpoints intercepted.** OpenAI `/v1/chat/completions` and `/v1/completions`, and Anthropic
  `/v1/messages`, including streaming. Default local port **8000**; the agent's API base URL is pointed at the
  proxy. (Confidence: **high**.)
- **Optional semantic detection.** With `sentence-transformers` installed, it can flag semantically-relevant
  background files via embeddings even when not explicitly named. (Confidence: **medium** — listed as optional;
  quality unmeasured.)
- **Cost claim + dashboard.** Advertises **50–80%** cost reduction (and "up to 90%" token cuts) and ships a
  terminal cost dashboard with per-model pricing config. (Confidence: **medium** — it is a vendor **claim**;
  see §6.)
- **License + maturity.** **MIT.** **Alpha:** ~2 commits, ~7 stars, 1 fork, no releases, 100% Python, Python
  3.10+. (Confidence: **high** for MIT; **high** that it is alpha — exact star/commit counts drift over time.)
- **SSL/MITM mode.** An experimental **HTTPS-interception** mode for agents with hard-coded endpoints:
  generate a **local CA**, **rewrite `/etc/hosts`** so `api.openai.com` / `api.anthropic.com` resolve to
  localhost, and **manually trust the CA** in the system keystore (a DNS/transport **bypass**). (Confidence:
  **high** that this mode exists and works this way.)

---

## 2. Verdict — **worth forking, NOT deploying as-is**

The **idea** is right and complementary to what we already do: a deterministic, structure-aware reduction of
**code context** at the request boundary is exactly the kind of lossless-by-construction compression the
Compress module wants (skeleton + on-demand rehydration ≈ the reversible/CCR pattern we already favor in
`context-compression-tools.md`). But TokenTamer **as-is** fails our bar on three counts:

1. **Governance.** Its headline integration path is **MITM** (local CA + `/etc/hosts` + DNS bypass). That is
   the opposite of an explicit, auditable plane and is **quarantined** here (§4).
2. **Determinism / robustness.** The non-Python path is a **brace heuristic**, not a real parser — it can
   silently mis-cut, which violates "same input ⇒ same, *correct*, output."
3. **Maturity.** Alpha (≈2 commits), no releases, no test corpus we can trust. MIT means we **can** fork.

**Decision:** fork into an internal **ContextTamer** and harden it (status: `research_candidate` in the
catalog; `proof_to_promote` ladder attached). Do **not** pip-install or run the upstream proxy in any shared
path.

---

## 3. The ContextTamer fork design

### 3.1 Remove/quarantine MITM → explicit gateway integration
Drop the MITM mode from the deployed path entirely. ContextTamer is reached by **explicit base-URL routing**
(the agent/plane points at it on purpose), with **product auth** on the hop and **vault-referenced secrets**
(secret *refs* only — never raw keys in config or logs). No trusted-CA install, no `/etc/hosts` rewrite, no
DNS bypass. (The upstream MITM mode survives only as a documented, single-developer **local-dev opt-in** —
see §4.)

### 3.2 Tree-sitter upgrade for non-Python
Replace the brace-balance heuristic with **Tree-sitter** grammars (JS/TS/Go/Rust/Java/C#/C/C++) so body
spans come from a real parse, not `{`/`}` counting. **Pin grammar + library versions** so output is stable
and reproducible. Keep Python on `ast` (also version-pinned). This is what turns "compression" into a
**deterministic tool** (§3.4).

### 3.3 Context **rehydration** tool
The skeleton drops bodies; rehydration brings them back **on demand**. Expose a tool: **given a file +
symbol, send only that symbol's body on the next turn** (not the whole file). This is the reversible half of
the lossless contract — the model can always recover an answer-critical body it turns out to need, so
shrinking the visible surface never means losing the fact. Track the **rehydration rate** as a quality signal
(high rate ⇒ the profile is over-compressing).

### 3.4 Compression **profiles**
Three named profiles (single-sourced in the catalog's `compression_profiles`):
- **conservative** — skeletonize only clearly-background files far from the edit set; widest context, lowest
  false-compression risk, smallest savings. Default for **cheap routes** and ambiguous context.
- **balanced** — skeletonize background; keep active files + semantically-flagged neighbors intact. General
  default.
- **aggressive** — skeletonize all non-active files + prune low-signal neighbors; lean on the rehydration
  tool. Highest savings; reserved for **premium/large-context routes** with rehydration on and the fidelity
  gate watched.

All three **preserve** the same fidelity surface (`answer_critical_facts`, `source_handles`,
`held_out_warnings`); they trade off how much *body* they hide, never whether facts/handles/warnings survive.

### 3.5 Benchmark-before-trust harness
No savings number is believed until it survives a harness on **our** data:
- **Corpus:** a **SWE-bench-lite-style** task set (resolve a real issue with a patch + tests) **plus internal
  agent traces** (real request payloads we'd actually compress).
- **Metrics:** tokens saved, cost delta, latency delta, **patch/test pass rate** (did compression hurt
  task success?), **retry rate**, **rehydration rate**, and **false-compression rate** (a body the task
  needed that was skeletonized and never rehydrated — the lossless-law red metric).
- **Gate:** a profile/version may move past `research_candidate` only if pass-rate is non-regressed within a
  set tolerance AND false-compression ≈ 0. Run **side-by-side** (compressed vs. uncompressed on the same
  snapshot), store both, diff, and keep the rejected candidates (lossless law).

### 3.6 Lossless-law compliance (the contract ContextTamer must satisfy)
- Originals retained; the skeleton is a **view**, never an overwrite.
- The skeleton carries **source handles** back to raw bodies; **held-out warnings** survive.
- **Rehydration is proven** (§3.3), not asserted.
- A **rollback** target exists (drop the compression layer, serve raw).
- Compression output has **no truth authority** and is never auto-promoted.

---

## 4. MITM quarantine (explicit)

TokenTamer's HTTPS-interception mode (local CA + `/etc/hosts` rewrite + DNS bypass + manual CA trust) is
**QUARANTINED**:

- **Never** in a shared, CI, or hosted deployment. No trusted-CA install, no `/etc/hosts` edit, no DNS
  bypass in any path the plane runs.
- Permitted **only** as an explicit, documented, **single-developer local-dev opt-in** for an agent with a
  truly hard-coded endpoint — never the default, never on by config inheritance.
- The supported integration is **explicit base-URL routing + product auth + vault secrets** (§3.1). The
  catalog encodes this as `mitm_mode: "quarantined_local_dev_opt_in_only"`, enforced by
  `_repos/shared-backend-components/scripts/check_context_compression_catalog.py`.

Rationale: a MITM proxy that installs a CA and rewrites name resolution is an **ambient, hard-to-audit
trust grant** on the whole machine — the antithesis of the explicit, receipted, vault-secret plane. We get
the same payload rewrite with none of that risk by routing on purpose.

---

## 5. Where it sits in the plane — the **Context Optimizer**

Compression is a stage **between policy and the router** in the inference plane (`_repos/teleon/backend/src/teleon/inference`):

```
object → preference resolution (OIPS) → policy/gates → [ Context Optimizer (ContextTamer, deterministic) ] → numeric provider router → provider → ModelInvocationReceipt
```

- It runs **before** routing so the chosen route sees the already-compressed payload (compress → then pick
  the cheapest viable model for the smaller context). It is **deterministic** (no LLM at compress time), so
  it does not itself need a model route.
- In the **agent gateway**, the same engine is exposed as a **deterministic tool** (compress / rehydrate) —
  agents call a stable, pinned-version tool instead of burning tokens, and the rehydration tool fetches a
  specific body on demand.
- It is **complementary to provider prompt caching** (Anthropic/OpenAI/Gemini): caching makes repeated
  prefixes cheap; ContextTamer makes the *variable* code context smaller. Use both. (Sequencing note:
  aggressive skeletonization changes the prefix and can *reduce* cache hits — measure the **net** effect in
  the §3.5 harness rather than assuming additivity.)

### 5.1 Compression manifest shape
Every compress call emits a manifest (the lineage + fidelity attestation that makes the view promotable and
rehydratable):

```json
{
  "manifest_id": "...",
  "profile": "balanced",
  "engine": "contexttamer",
  "parser_versions": { "python_ast": "<pinned>", "tree_sitter": "<pinned>", "grammars": { "go": "<pinned>" } },
  "raw_source_handles": ["ctx://repo/path.py#calculate_tax", "..."],
  "files": [
    { "path": "...", "treatment": "intact|skeletonized", "symbols_skeletonized": ["calculate_tax"], "rehydratable": true }
  ],
  "preserved": ["answer_critical_facts", "source_handles", "held_out_warnings"],
  "tokens_before": 0, "tokens_after": 0,
  "fidelity_attestation": "facts+handles+held_out preserved; rehydration available",
  "rehydration": { "tool": "rehydrate(file,symbol)", "available": true },
  "rollback": "serve_raw",
  "no_truth_authority": true
}
```

The manifest is what `_repos/shared-backend-components/scripts/check_context_compression_catalog.py` governs in shape, and what the
benchmark harness reads to compute false-compression / rehydration metrics.

---

## 6. Economic note

- **High ROI on premium routes.** Skeletonizing large background code context before an expensive,
  large-context model is where 50–80%-class savings (**if** they hold on our traces — currently
  `unverified_until_benchmarked`) actually pay. Use the **aggressive** profile here, with rehydration on.
- **Latency + context-window discipline on cheap routes.** On small/cheap models the dollar savings are
  marginal and the compress step adds latency and a mis-cut risk; prefer **conservative** (or skip
  compression) and let prompt caching carry the cost win.
- **Complementary to prompt caching**, not a replacement (§5). The combined, measured effect is what matters.
- **The 50–80% claim is a claim.** It is recorded as `savings_status: unverified_until_benchmarked` and is
  not repeated as fact on any product surface until §3.5 confirms it on our own data.

---

## 7. What this connects to (so we extend, not reinvent)

- **Lossless law:** `_repos/shared-backend-components/docs/codex/lossless-distillation.md` (compression shrinks the text surface only if
  facts + handles + held-out warnings survive + rehydration exists).
- **Compression landscape + `compression` slot:** `_repos/baltor/context/research/context-compression-tools.md` (Headroom /
  LLMLingua / EXIT; reversible-vs-lossy taxonomy). ContextTamer is the **proxy/code-skeleton** shape that
  sits *alongside* those chunk compressors.
- **Inference plane:** `_repos/teleon/backend/src/teleon/inference` (OIPS preference resolution → numeric provider router →
  ModelInvocationReceipt). ContextTamer is the Context Optimizer stage in front of the router.
- **Catalog + checker (this pass):** `_repos/shared-backend-components/architecture/context_compression_provider_catalog.json` +
  `_repos/shared-backend-components/scripts/check_context_compression_catalog.py`.

---

## 8. Honest confidence

- **High:** TokenTamer is an MIT, alpha, local FastAPI proxy that skeletonizes background code (Python `ast`
  / brace-heuristic elsewhere) across OpenAI + Anthropic endpoints and ships a quarantine-worthy MITM mode.
- **Medium:** the 50–80% / "up to 90%" savings (vendor claim, unbenchmarked by us); the semantic-detection
  quality; exact star/commit counts (they drift).
- **Design (ours, not yet built):** ContextTamer fork, Tree-sitter upgrade, rehydration tool, profiles, the
  benchmark harness, and the plane placement are a **proposed** design in this doc — the catalog records the
  governance invariants; the implementation and the §3.5 benchmark are the `proof_to_promote` work, not done.

---

## Sources

- borhen68/TokenTamer — repository + README: https://github.com/borhen68/TokenTamer
- Internal — lossless-distillation law: `_repos/shared-backend-components/docs/codex/lossless-distillation.md`
- Internal — compression landscape & `compression` slot: `_repos/baltor/context/research/context-compression-tools.md`
- Internal — inference plane: `_repos/teleon/backend/src/teleon/inference/` (OIPS, router, receipts)
- Adjacent reversible/CCR compressor for technique comparison: chopratejas/headroom — https://github.com/chopratejas/headroom
