# Multi-agent swarms — evaluation & positioning for Baltor (2026-06-05)

Owner asked to "test OpenHive and other swarms of agents." Per **verify-first** every repo below was
web-confirmed. **Constraint honored:** I did NOT `pip install` or execute OpenHive (or any of these) —
no-pip / no-untrusted-exec rules + the promo's astroturf framing. Evaluation = read the source, verify
claims, position vs Baltor; any hands-on goes in the `experiments/` skunkworks on **our own bus**, never
their runtime.

## Baltor's swarm thesis (the lens)
Baltor already ships an in-house **`context_swarm`**: bounded agents that verify a context object, find
contradictions, **route** a review, and **propose (not apply)** a fix — *no canonical mutation*,
deterministic, on the event bus. Thesis: **small models + narrow scope + DETERMINISTIC harnesses;
Baltor owns the governed contract, orchestration is swappable infra.** That is the bar these are judged
against.

## OpenHive — `github.com/aden-hive/hive` ✓ REAL, but hype-inflated
- **What it is:** a `uv`-workspace Python runtime (~88% Py) where a "queen" agent spins up worker/colony
  agents and **compiles a graph execution DAG** via LiteLLM (100+ providers). Sells production concerns:
  state mgmt, crash recovery, observability, human-in-the-loop, MCP tools. "Self-healing" = on failure it
  **evolves the graph and redeploys**. Apache-2.0. ~10.5k★ / ~5.7k forks; active (v0.11.0, May 2026). YC
  company = **Aden** (YC page confirmed; exact batch inconsistent → unverified).
- **Substance verdict: REAL code, oversized costume.** Red flags:
  - **Zero benchmarks** behind "production"/"deterministic fault tolerance" claims.
  - **Internal contradiction:** a topology the LLM *rewrites at runtime* ("self-healing/evolves") is the
    opposite of "deterministic." Both are headline claims; neither is proven.
  - **Astroturf signal:** arrived via a Facebook group + `#HermesAgent #OpenClaw`; community threads report
    distrust of that ecosystem for suspected astroturfing; "default marketing queen" commit + high
    fork:star ratio = growth-hacked launch.
  - **Credential path:** writes `~/.hive/credentials` + offers a hosted "Hive LLM" provider (a route for
    your keys/traffic); telemetry undocumented → treat as present.
- **Verdict for Baltor: REFERENCE / FOIL — Track-B comparison only, never runtime.** It is the *exact*
  failure mode Baltor rejects. Don't run it; don't depend on it.

## Comparison set (all verified)
| Repo | What | ~★ | State | Baltor verdict |
|---|---|---|---|---|
| `langchain-ai/langgraph` | graph/state-machine agent runtime, checkpointing, durable state, HITL | ~34k | active | **ADOPT-PATTERN** — closest to Baltor's deterministic-DAG + persisted-state; harvest checkpoint/HITL patterns; swappable as infra |
| `microsoft/autogen` | pioneer conversational MAS; **maintenance mode** → `microsoft/agent-framework` | ~50k | frozen | **REFERENCE** — canonical patterns, don't build on it |
| `openai/openai-agents-python` | production successor to (deprecated) `openai/swarm`; handoffs + guardrails | ~26k | active | **REFERENCE** — study guardrail/handoff primitives; provider-agnostic like our backend |
| `crewAIInc/crewAI` | role-playing collaborative crews | ~52k | active | **OUT-OF-SCOPE** — role-RP autonomy over governed determinism (counter-thesis) |
| `openai/swarm` | educational handoff framework | ~20k | **deprecated** | **OUT-OF-SCOPE** — superseded |
| `BUPT-GAMMA/MASFactory` | graph-centric MAS via "Vibe Graphing", 7-benchmark eval (arXiv:2603.06007) | ~156 | research | **REFERENCE (Track-B)** — already our queued experiment; benchmark-backed |

## The takeaway (Baltor's swarm story writes itself)
OpenHive markets "self-evolving topologies + self-healing agents," can't reconcile that with its own
"deterministic" claim, ships no benchmarks, and launched on astroturf. **That is undifferentiated,
unverifiable, race-to-the-frontier orchestration.** Baltor's durable position: a **deterministic harness
over a governed context contract** — a bounded `context_swarm` (no canonical mutation, routes review,
proposes not applies) where *topology generation is a swappable, MEASURED Track-B experiment*. The
credible benchmarks to measure against are **LangGraph** (determinism/state) and **MASFactory**
(graph compilation), not OpenHive.

## What we'll actually do (safe, on-thesis)
- **No runtime adoption, no untrusted exec.** OpenHive/crewAI/autogen stay read-only references.
- **Track-B skunkworks (already seeded):** `experiments/masfactory_context_swarm/` models a generated
  topology onto **our** bus. If we extend it, add a LangGraph-pattern checkpoint comparison there —
  offline, no external runtime, proven by the experiments-isolation check.
- **Differentiation doc:** fold the "deterministic harness vs self-evolving topology" line into the
  swarm positioning. Relates to [[small-models-need-narrow-scope-and-deterministic-harnesses]].
