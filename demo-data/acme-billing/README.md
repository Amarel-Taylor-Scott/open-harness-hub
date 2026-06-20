# Acme Billing — Baltor demo dataset (synthetic, public-safe)

A tiny, deterministic, **synthetic** corpus for the Baltor working demo. No real PII, no secrets,
no proprietary data — every file here is invented for demonstration. It is shaped like a real
engineering knowledge base so the demo can show the whole context motion end-to-end:

```
raw sources → context objects + source handles → graph → interrogate → pack → receipt
           → human review → measured lift → swarm-verify an object
```

## What's in the corpus (and why)

| File | Becomes (object_type) | Role in the demo |
|---|---|---|
| `tickets/BILL-782.json` | `work_item` | the task the agent is asked to do (raise the retry ceiling) |
| `decisions/ADR-014-billing-retry-policy.md` | `decision` | the **authority** on the retry policy (max 5 retries) |
| `repo/billing/retry.py` | `file` | code that **implements** the policy (matches the ADR: 5) |
| `repo/billing/test_retry.py` | `test_result` | test that pins the behavior |
| `docs/billing-runbook.md` | `document` | **deliberately stale**: says max 3 — contradicts the ADR + code |
| `incidents/INC-2026-04-retry-storm.md` | `incident` | why the policy exists (a retry storm) |
| `api/billing-api.yaml` | `document_section` | the OpenAPI surface for the billing endpoint |
| `org/OWNERS.md` | `team` | who owns the service (routing for human review) |

Two facts are **planted on purpose** so the demo proves Baltor does something a bare model can't:

1. **A contradiction.** `docs/billing-runbook.md` claims *max 3 retries*; `ADR-014` and `retry.py`
   say *5*. Graph interrogation must surface the conflict, pick the authority (the ADR
   `SUPERSEDES` the runbook), and cite source handles — not silently average or guess.
2. **Staleness.** The runbook's `freshness.staleness = "stale"` and it is `SUPERSEDES`-d by the
   ADR — so a pack built for a *write* action must flag it and route to human review.

The canonical, machine-readable seed (context objects + relationships + assertions, all conforming
to `schemas/context-object`, `context-relationship`, `context-assertion`) is
`seed-graph.json`. `scripts/context_graph.py` loads it, builds the graph, and answers questions
against it (offline-deterministic; a live model route only *phrases* the answer, it never invents
the facts).
