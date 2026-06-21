# Teleon is a CONTROL / METADATA plane, not a compute plane (2026-06-21)

> Owner clarification: running capability units on Cloudflare (and using Cloudflare's own LLMs) makes demos +
> infrastructure dramatically easier — it makes **Teleon a thin metadata + orchestration layer, not the computation
> unit**. Teleon may still run the LLMs that *improve* a unit, but it does not run the final unit over time — and it
> doesn't even need to run the improvement runs: **it tracks the results + metadata to guide improvement.**

This is the stronger version of the thesis, and it's what the codebase already implements. Stated plainly:

## The split

| Plane | Who | What it does | Where it runs |
|---|---|---|---|
| **Control / metadata (Teleon)** | us | SELECT (which model/backend/DAG path), GOVERN (receipts, serves_truth, promotion boundary), and **LEARN** (the descent brain — what worked, the metadata that guides the next improvement) | a lightweight always-on control plane |
| **Data / compute (external)** | customer / edge | run the **final capability unit** AND (optionally) the **improvement runs** | Cloudflare Workers + Workers AI, the customer's account (BYO key), or the edge |

**Teleon's moat is the accumulated descent brain (the learning + governance), NOT the compute.** Compute is a
commodity you rent on Cloudflare or the customer's account; *knowing which bounded configuration is cheapest-that-meets
for a capability, with receipts to prove it,* is not.

## What this means concretely

1. **The final unit runs externally, forever.** Teleon COMPILES the unit (`src/teleon/compiler/{compile,emit}.py`)
   and dispatches it to an external backend behind `ExecutionProviderPort` — e.g. `CloudflareWorkersProvider` (BYO via
   a customer API key, `compute_ownership=customer_account`). Teleon does not host the running unit.
2. **Even the improvement LLMs can run on Cloudflare.** Cloudflare Workers AI is a model lane
   (`architecture/lowcost_llm_endpoint_registry.json`) — the cheap brain that proposes conversions can run there, not
   on our compute.
3. **Teleon need not run the improvement runs at all.** The descent brain
   (`src/teleon/evolution/descent_attempt_store.py`) is the canonical, append-only, lossless record of every attempt.
   `src/teleon/evolution/external_outcomes.py` records an EXTERNAL run's result + metadata (axes from its receipt) into
   the brain, and `guide_next()` returns the brain's recommended next descent move — **Teleon guides improvement from
   tracked telemetry of runs it never executed.**

## Invariants (unchanged)

- **The brain + FleetLedger + receipts stay Teleon's truth** even when all compute is external (the customer runs it;
  we record + govern it). A backend/run never owns truth (`serves_truth=false`).
- **Data residency / cost shift to the customer** when compute is on their account (the `locality` descent axis; their
  bill) — a feature, not a compromise.
- **Lossless:** the brain keeps every attempt incl. external + negatives; nothing is overwritten.

## Why it matters

- **Demos + infra get radically simpler** — no fleet of our own workers to run the final units; spin them up on
  Cloudflare. The always-on surface is just the control plane (cf. the flywheel operating model: lightweight control
  plane 24/7, expensive workers scale-to-zero / run elsewhere).
- **It sharpens the wedge:** Teleon sells *governed selection + the learning*, billed on value, while compute is the
  customer's commodity — higher margin, lower our-side cost, easier trust (their data on their account).

## Realized by

`ExecutionProviderPort` + `architecture/execution_backend_policy_matrix.json` (`compute_ownership`) ·
`src/teleon/runtime/execution_providers/cloudflare_workers.py` · the Cloudflare Workers AI lane ·
`src/teleon/evolution/descent_attempt_store.py` + `external_outcomes.py` · `scripts/check_teleon_control_plane.py`.
See also `docs/architecture/cloud-architecture.md`, `architecture/surface_map.json`.
