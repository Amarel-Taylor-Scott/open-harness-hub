# Future ideas — prioritized backlog (refreshed 2026-06-04)

Ideation FOLLOWS shipped proof. Source for this batch: the verified external-repos brief
(`research/external-repos-brief-2026-06-04.md`). Each item names the verified source, the concrete
lift, and a warrant note. Highest-leverage first. **None of these are started** unless marked.

## P0 — strongest leverage, on-thesis
1. **Mirror Anthropic's "AI drafts, humans sign off" framing in compliance copy/positioning.**
   Source: `anthropics/financial-services` (~30k★). Baltor already *implements* this (review queue,
   no canonical mutation). Gap is making it the explicit, industry-credible headline on the
   compliance beachhead, then differentiating on continuous verification / freshness-CDC / portable
   receipts / measured fidelity (what Anthropic leaves to the firm). **Warrant: strategy/positioning
   → needs owner intent or ≥2 sources before any site/strategy edit. Flagged, not unilateral.**
2. **Evaluator-optimizer loop for the verification rail.** Source: `anthropics/claude-cookbooks`
   `patterns/agents/` + "Building Effective Agents". Map our continuous-verification + adversarial-
   validation rail onto the canonical generate→independent-evaluate→refine pattern; document the
   correspondence in `docs/` and tighten the rail to match. Warrant: established repo principle.
3. **Memory Block skill (anti-drift).** Source: `nidhinjs/prompt-master` (~8.7k★). ✅ DONE:
   `scripts/context_memory_block.py` — deterministically reconciles a decision log → pinned block
   (digestible-front / expandable-back lineage; later-supersedes-earlier), bus-capable (9th connected
   engine), in the flywheel as `context_memory_block`. **Remaining (optional next): fold it into the
   autonomous build loop (feed the goal-loop receipts → pin current decisions) + a `Skill`-format
   wrapper so it's invocable as a slash-command.** Warrant: principle.

## P1 — high value, scoped
4. **Design-token drift checker + single `tokens.css`.** Source: `VoltAgent/awesome-design-md`
   schema. ✅ DONE: `docs/standards/DESIGN.md` + `scripts/check_design_tokens.py` (reporter, in the
   flywheel as `check_design_tokens`; `--strict` ready for CI; found 11 drifting palette tokens).
   **Remaining (owner sign-off — brand decision): pick the canonical palette → converge to one
   imported `_repos/baltor/frontend/tokens.css` → flip the reporter to `--strict` in CI.** See DESIGN.md §Known-drift.
5. **Skill router (trigger-in-frontmatter).** Source: `obra/superpowers`. Adopt the convention where a
   skill's `description` frontmatter encodes its trigger condition, + a meta "router" skill that gates
   each turn into the right sub-skill. Hardens skill discovery in the autonomous loop. Warrant: principle.
6. **Production-hardening checklist for the ops dashboard.** Source: `NirDiamant/agents-towards-
   production` (~20.6k★). Borrow its tracing + eval + security-test structure (LangSmith-style
   tracing, LlamaFirewall/Apex-style adversarial tests) to extend the verification rail + dashboard.

## P2 — reference / evaluate later
7. **Versioned RAG library + 3-layer memory** as a comparison point for our source-linked, CDC-tracked
   context packs. Source: `HKUDS/DeepTutor` (~24.6k★, REFERENCE only — tutoring domain is off-thesis).
8. **KYC Screener template** as a worked compliance example to benchmark verified_context_flow against.
   Source: `anthropics/financial-services` `plugins/vertical-plugins/operations/`.

## P0/P1 — from the 2026-06-05 swarms + text-transformation research (verified)
9. **LLMLingua-2 behind `context_compress` as an optional Provider (primary stays the deterministic
   ladder; LLMLingua-2 = higher-ratio fallback).** Source: `microsoft/LLMLingua`✓. Frozen, self-hostable.
   Caveat: upstream quiet since Apr 2024 → pin + vendor (no-pip). First step = define the
   `CompressionProvider` port + labeled SEAM in `context_compress` (deterministic primary), wire the model
   later. See `research/text-transformation-systems-map.md` L12. Warrant: principle.
10. **`dottxt-ai/outlines` as the structured-output Provider on the Verification rail** (fallback
    `mlc-ai/xgrammar` / `noamgat/lm-format-enforcer`) → 100%-valid rewrite/diff verdict JSON. (map L14.) Warrant: principle.
11. **`promptfoo` + `vibrantlabsai/ragas` as a measured-lift / faithfulness harness** feeding the
    `pipeline_score − bare_model_score` gate → automate the lift bar. (map L17.) Warrant: principle.
12. **Diff/change-report output on rewrites** — ✅ DONE: `scripts/context_diff.py` (`diff_text`) emits the
    L18 change-report (word/sentence diffs, per-category entity preservation, worst-first risk_flags incl.
    protected_term_dropped / number_dropped_or_changed / number_introduced / date_dropped, readability
    before/after). Deterministic, bus-capable (10th connected engine), in the flywheel as `context_diff`.
    Catches a rewrite silently dropping a figure/date/sanctioned entity or fabricating a number.
13. **Linguistic-analysis (L3) substrate for entity-safe rewriting** — protect names/numbers/dates/
    citations before any transform (spaCy/regex validators). Closes the Reconciliation gap. Warrant: principle.
14. **Swarm positioning: deterministic harness vs self-evolving topology** — fold the OpenHive-as-foil
    line into the swarm story; extend `experiments/masfactory_context_swarm/` with a LangGraph-pattern
    checkpoint comparison **on our own bus** (offline; no external runtime). Source: `research/multi-agent-swarms-eval.md`.


## P0 — durable runtime (2026-06-05; fixes fragility/non-durableness; plan: docs/architecture/durable-runtime-plan.md)
15. **Durable layer ✅ SHIPPED** — `scripts/durable_store.py` (sqlite3, thread-safe, WAL): durable event
    log (bus survives restart, proven 51→51), durable job queue (lease claim→ack/retry→DLQ), idempotency,
    outbox. Wired opt-in into the admin server (`BALTOR_DURABLE_DB`). In flywheel as `durable_store`.
16. **C26 event envelope contract (NEXT)** — one envelope for every event+command (event_id, schema_version,
    pass_id, tick_id, engine_version, causation/correlation/trace, idempotency_key, priority, evidence) +
    a validator proof. Principle-backed.
17. **C28 per-engine queues + priority lanes** — route commands to `flywheel.commands.<engine>` /
    `flywheel.p0.*` on the durable_store; dashboard reads projection; workers independent of SSE. Principle-backed.
18. **C29 scale one engine** — N stateless workers off one queue, same idempotency key, no dup side effects;
    measure drain time (local threads; KEDA later). Principle-backed.
19. **C30 pass-lifecycle orchestration + C31 human-signoff gate** — lightweight orchestrator (Temporal later);
    "AI drafts → human signoff" as a runtime LANE (gate mechanism principle-backed; compliance COPY parked).


## P1 — decomposition grain (2026-06-05; tested foundation in scripts/ingest/decompose_structured.py)
20. **Wire atomic facts through the pack/serve path** — have demo_cfpb_context_pack (or the gateway) expand
    each context object into `decompose_structured` atomic facts so claims/If-Statements attach to a single
    fact + #field handle, not the whole record. Proven module exists; wire + prove end-to-end. Principle-backed.
21. **Unstructured CFPB/regulatory PDFs via a real ParserProvider (Docling)** — run `document_decompose`
    on real unstructured PDFs behind a Docling adapter (vendor, no-pip → adapter SEAM first). Structured grain
    works first (done); this is the next grain. Principle-backed (+ verified catalog: Docling primary).

## Explicitly OUT-OF-SCOPE (do not pursue — off-thesis)
- Multi-agent **runtimes as our runtime** — OpenHive (`aden-hive/hive`, self-evolving topologies = our
  foil), `crewAIInc/crewAI`, `openai/swarm` (deprecated). Keep as Track-B *comparisons only*, never the
  deterministic runtime path; do NOT pip-install or execute. See `research/multi-agent-swarms-eval.md`.
- Article **spinning/spintax** for product output (`m1/gospin` et al.) + fine-tune-dependent compressors
  (`princeton-nlp/AutoCompressors` breaks the frozen-model rule). Cautionary baselines only.
- Social-media / faceless-content automation (`charlie947/social-media-skills`,
  `cporter202/automate-faceless-content`), music/audio/fine-tune tooling (`opentune*`). Recorded so a
  future pass doesn't re-litigate them. See the brief for why.

## To verify before use
- `ai-boost/awesome-harness-engineering` — topically on-point (harness/evals/MCP/observability) but
  unconfirmed; verify owner/name/quality before citing.
