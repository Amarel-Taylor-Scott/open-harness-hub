# Hierarchical flywheels — how Baltor improves

Baltor is **not one pipeline**; it is a system of **nested, modular, measurable flywheels**. The
pipeline (Source → Reconciliation → Anti-Fragility → Enhancement → Optimization → Consumption +
the Verification rail) is how context **moves**. A flywheel is how context **improves**.

```
System flywheel
 → stage flywheels
   → subsystem flywheels
     → object flywheels
       → worker flywheels
         → AI-agent decision flywheels
```

Every flywheel runs the same loop:
```
sense → decide → act → observe → evaluate → improve → persist → re-trigger
```
and is configurable · queueable · observable · testable · replaceable · auditable · policy-governed
· emits receipts · operates under explicit **decision context**.

## Flywheel Capsule
A **Flywheel Capsule** is a self-contained improvement loop declared by a `FlywheelSpec`
(`schemas/flywheel/flywheel-spec.schema.json`): objective · scope · triggers · inputs · decision-context
requirements · worker steps · outputs · metrics · policy gates · fallbacks · runtime placement ·
receipts emitted · storage · observability · harness refs. A `FlywheelRun` records one execution
(steps, metrics, policy decisions, receipts, lineage, retries).

## Agents participate only inside a DecisionContext
AI agents never run from unbounded context. An L5 agent flywheel acts only inside a bounded
`DecisionContext` (`schemas/flywheel/decision-context.schema.json`) — allowed tools, policy, risk,
evidence handles, cost/latency budgets, stop conditions, human-review triggers — and emits a
`DecisionReceipt` (`schemas/flywheel/decision-receipt.schema.json`) recording the decision, reason,
evidence used, actions proposed/taken/blocked, policy decision, and next trigger. **Durable
workflows, queues, and the policy engine own execution, retries, replay, and audit — not the agent.**

## Levels
- **L0 System** — the whole loop: source change → capture/decompose → reconcile → anti-fragility → enhance → verify → optimize → consume → observe → evaluate → improve → refresh.
- **L1 Stage** — one per macro stage + the verification rail.
- **L2 Subsystem** — Parser/Repo/Skills/Scraping/API managers, Context-Rot, Verification Engine, Pack Builder, Policy, Backend-Tool Routing, Observability+Eval, Sandbox.
- **L3 Object** — SourceHandle, ContextObject, ContextClaim, DocumentObject, RepoObject, ApiObject, ContextPack, ContextReceipt, MemoryItem, ToolAdapter.
- **L4 Worker** — SourceWatcher, DocumentDecomposer, parsers/extractors, RepoIndexer, EntityReconciler, FragilityHunter, ContextEnhancer, ClaimVerifier, AdversarialInterrogator, PackCompressor, ReceiptIssuer, ContextRotSweeper, EvalRunner, BackendAdapterEvaluator.
- **L5 AI-Agent Decision** — Context-Rot, Pack-Refresh, Source-Conflict, Enhancement-Discovery, Backend-Tool-Selection, Human-Review-Routing.

## Worked examples (already partly shipped)
- **Document-decomposition flywheel** — a 1,000-page PDF → recursive object tree
  (`scripts/ingest/document_decompose.py`); re-decompose→diff drives per-node rot.
- **Context-rot flywheel** — TTL + content-hash CDC + ACL + supersession → serve/refresh/block
  (`scripts/ingest/context_rot.py`).
- **Backend-tool-routing flywheel** — adapter run metrics → tool score → route/fallback decision
  (`data/backend-tools.yaml` is the current static version; the flywheel makes it adaptive).
- **Pack-quality flywheel** — eval scores → compression/selection tuning → better packs.
- **AI-agent decision flywheel** — bounded `DecisionContext` → action → `DecisionReceipt` → eval → improve.

The deterministic **flywheel watchdog** (`scripts/baltor_flywheel.py`) is the L0 "stay-green +
watch-freshness" loop in operational form: every tick re-runs all proof self-tests + CDC-watches
live sources, appending a heartbeat to `.agent/flywheel-health.jsonl`.
