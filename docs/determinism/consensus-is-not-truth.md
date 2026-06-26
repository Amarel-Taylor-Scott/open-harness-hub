# Consensus is not truth

## Purpose

State, in one place, the single most load-bearing safety property of the Determinism Factory and show exactly
how it is made **structural** (impossible to violate) rather than merely promised:

> **Multi-LLM consensus is an evidence / ambiguity signal, NOT a label.** No agreement threshold — not even
> unanimity — can serve a fact. A fact is served only by a deterministic validator or an authority/policy
> decision (Baltor reconciliation / the consumption gate). "The models agreed" is never an answer.

## Owner

Engine: `src/baltor/determinism/consensus.py` (the recorder) + `src/baltor/determinism/trace_store.py` (the
verification law) + `src/baltor/determinism/pattern_miner.py` (verified-only mining).

## Why consensus is recorded at all

Consensus is useful as **evidence**, not as truth:

- **High agreement** → still routes to the deterministic validator / authority for the LABEL. It is a cheap
  signal that the input is probably in-distribution; it does not decide the answer.
- **Low agreement** → routes to **human review**. The disagreement is an *ambiguity flag* — exactly the cases
  where a deterministic rule should NOT yet be trusted.

Neither destination is "serve the majority output as the answer." `ConsensusRun.routing()` returns
`deterministic_validator` or `human_review`; there is no third branch that serves a fact.

## How the property is made structural

| Clause | Mechanism (where) |
|---|---|
| Consensus can never serve a fact | `ConsensusRun.can_serve_fact` is a **constant property returning `False`** — not a settable field. No code path, no threshold, not unanimity, flips it. |
| Consensus can never be mined into a rule | `ConsensusRun.to_trace()` writes a `consensus`-kind trace with `verified=False`. The pattern miner reads ONLY verified traces (`mining_set(require_verified=True)`), so a consensus trace is physically invisible to mining. |
| An LLM/consensus trace can never be flagged verified | `TraceStore.append` raises if `verified=True` on an `llm`/`consensus` kind — only `workflow`/`adjudication` traces (source-grounded + receipt-backed) may be verified. |
| Consensus-only can never mint a rule candidate | `rule_candidate_generator.from_pattern` raises `ConsensusOnlyError` when `label_source == "consensus_only"` (or anything not a real producer). |
| `majority_output()` is evidence, not a label | It exists only so a human/validator can INSPECT the largest cluster; returning it does not, and cannot, serve it (`can_serve_fact` stays `False`). |

## Contracts

`ConsensusRun` (records `agreement_score`, `clusters`, `disagreement_clusters`, `routing`,
`can_serve_fact=False`). Projected into the trace store as a `consensus`-kind `WorkflowTrace` with
`verified=False`.

## Inputs / Outputs

- **Inputs**: ≥2 `ModelOutput`s (each a model's structured proposal + `model_id`/`provider_id`/`prompt_hash`
  — the prompt *hash*, never the prompt text).
- **Outputs**: a `ConsensusRun` (agreement score = fraction of outputs in the largest cluster; disagreement
  clusters) and a routing decision. It NEVER outputs a served fact.

## Proofs

- `scripts/check_consensus_recorder.py` — multi-model outputs recorded; agreement computed; disagreement does
  NOT promote truth; consensus alone cannot serve a fact.
- `scripts/check_determinism_full_stack.py` — in the end-to-end motion, `can_serve_fact=False`, the consensus
  trace is excluded from the mined pattern, and the served fact comes from the authority label only.
- `scripts/check_determinism_redteam.py` — the "promote a rule from consensus only" and "even unanimous
  consensus serves a fact" attacks both FAIL SAFELY.

## Commands

```bash
PYTHONPATH=. python3 scripts/check_consensus_recorder.py --self-test
PYTHONPATH=. python3 scripts/check_determinism_full_stack.py --self-test
PYTHONPATH=. python3 scripts/check_determinism_redteam.py --self-test
```

## Limitations

- The recorder clusters outputs by **byte-identical** canonical hash. Semantic-equivalence clustering (two
  phrasings of the same answer) is future work; today two non-identical bodies are distinct clusters.
- Agreement is a pure count; it is deliberately NOT weighted by model quality, because a weighting could
  smuggle "trust the better model" back toward treating agreement as truth.

## Next

Surface consensus runs (and their disagreement clusters) in the deferred `/determinism` UI as an
ambiguity-signal panel — clearly labelled "evidence, not truth" — so reviewers can triage low-agreement
slices to human review.
