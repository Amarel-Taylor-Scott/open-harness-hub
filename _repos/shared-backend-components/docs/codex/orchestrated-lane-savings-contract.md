# The orchestrated-lane savings contract (owner-canonized 2026-07-07)

> Owner: *"Lets memorialize this because this is what actually matters, this is the comparison that would
> capture real world savings."*

## The canonical comparison

**Real-world savings are measured as `bare` vs `orchestrated` on real cloud models, executed and
cross-tested** — `scripts/real_buildout_ab_harness.py`:

- **bare** — the LLM writes ALL the code for the buildout turn.
- **orchestrated** — the compiler thesis made measurable: the LLM is ONLY the designer/orchestrator. Its
  entire output is `{"use_primitives": [A, B, C]}` plus thin glue (a `main.py` that imports from
  `primitives_lib` and wires the chain, plus tests). The VERIFIED implementations are injected verbatim
  from the registry at **zero generated tokens**.
- Both lanes' programs are **executed in the sandbox** (compile, own pytest) and **cross-tested** (lane A's
  tests against lane B's implementation and vice versa) so a smaller token bill can never hide broken
  behavior.
- Receipts report `generation_avoided_completion_tokens`, `n_primitives_reused`, `reused_code_chars`,
  compile/self-test rates, and cross-test agreement — under `data/dev-intel/real_buildout_ab/`.

This is the difference between *an LLM writing all of the code* and *an LLM saying primitive A → primitive
B → primitive C*. The self-test proves the differential end-to-end (orchestrated ~120 tokens and passing;
bare ~700 tokens with a seeded bug and failing; cross-test catching it) and is mutation-gated.

## What the number means (and what must accompany it)

1. **Generation-side savings (this contract's headline):** bare completion tokens − orchestrated completion
   tokens, valid only for turns where the orchestrated program's runtime quality is ≥ the bare program's
   (self-tests + cross-tests). Token deltas with worse runtime outcomes are NOT savings.
2. **Input-side savings (complementary, measured elsewhere):** retrieval replacing repo-reading/context
   tokens — the realistic session benchmarks (proxy lane, labelled as such) and the real-session redundancy
   measurement (`session_redundancy.py` on actual Claude Code logs).
3. **Coverage honesty:** the orchestrated lane's reach is bounded by the verified executable library. Report
   the reused-vs-glue fraction per turn; where glue dominates, the measurement is a MINTING TARGET for the
   buildout orchestrator, not a savings claim.

## Guardrails (all encoded in the harness, not prose)

- Cloud lanes only — Ollama Cloud GLM 5.2 / Kimi K2.7-code (large context), OpenWebUI-CDP gemma-4-coding,
  NVIDIA GLM. **Local gemma4 is refused by construction** (8GB GPU understates baselines).
- **Continuation protocol** on `finish_reason=length` (provider output caps must not silently truncate
  long-form baselines — the first NVIDIA run measured exactly that failure mode).
- Real token accounting from API usage payloads; approximate lanes labelled `token_source=approx_chars`.
- Scenarios/code-states shared with the proxy benchmark (greenfield → brownfield; SaaS/ML/Kaggle/monolith)
  so both lanes measure the same projects.
- candidate=true, serves_truth=false on every receipt; no promotion by assertion.

## The flywheel this creates

Grow the verified executable library → the orchestrated lane's reused fraction rises → measured
generation-avoided tokens rise → the gaps (glue-dominated turns) name the next primitives to mint and
verify. Savings proof and registry growth are the same loop.
