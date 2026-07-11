# Primitive Benchmark Taxonomy

> A primitive earns promotion by proving **marginal utility**, not absolute performance (SWE-Skills-Bench:
> 39/49 skills gave zero lift). Engine: `scripts/primitive_benchmark_taxonomy.py`. Schema:
> `schemas/benchmark_result.schema.json`. Makes primitive economics publishable and comparable to the
> compiled-AI papers.

## The metrics

| Metric | Meaning | How we get it |
|---|---|---|
| `oracle_pass_rate` / `first_pass_rate` | correctness (no error / no repair) | **measured** on fixtures |
| `semantic_entropy` | output variance over repeated runs; **0 == deterministic** | **measured** (repeat×5, distinct-output entropy) |
| `deterministic_replay_pass` | identical output every run | **measured** |
| `runtime_tokens` | tokens spent at runtime; **0** for a deterministic primitive | **measured** (it executes as code) |
| `token_reduction_factor` | baseline_runtime_tokens / runtime_tokens (denominator floored at 1) | measured runtime ÷ **estimated** baseline |
| `break_even_n` | compile_tokens / per-tx token savings (the paper's ~17) | computed |
| `break_even_n_true` | (compile+validation+security+review+ci) / per-tx savings | computed (the honest break-even) |
| `latency_p50/p95/p99` + `jitter` | latency distribution | **measured** |
| `deterministic_advantage` | (quality/cost)_primitive ÷ (quality/cost)_baseline; **>1 wins** | computed |
| `fallback_rate` / `repair_count` | ops: routed to LLM/human / micro-repairs | measured |
| `security_gate_status` | pass \| fail \| quarantine (from the security gate) | from `primitive_security_gate` |
| `marginal_utility_status` | measured_lift \| unmeasured \| measured_no_lift \| regressed | derived |

## Honesty rule

The **deterministic side is real and measured** — semantic entropy, replay, latency, and `runtime_tokens=0`.
The **baseline** (what a runtime LLM would spend regenerating the logic) and the fixed compile/validation/
security/review costs are **clearly-labelled ESTIMATES** (`cost_note` in every receipt) until a live model is
attached. We never fabricate a baseline: if `baseline_runtime_tokens` is unknown, `token_reduction_factor`
and `break_even_n` return `null`.

## First real receipt (the scalar kernel)

`standardize_scalar` over 14 adversarial fixtures (`5 ft`/`60 in`/`$1.2M`/`(1,234.56)`/`12%`/`50 bps`/`YES`/
`N/A`/…): **semantic_entropy 0** (fully deterministic), **oracle_pass_rate 1.0**, **runtime_tokens 0**,
**token_reduction_factor 1200×** (vs a 1200-token estimated baseline), **break_even_n 8**, security_gate
`pass`. Written to `data/dev-intel/primitive_benchmarks/latest.{json,md,csv}`.

## Run it

```bash
python3 scripts/primitive_benchmark_taxonomy.py --self-test   # metric-calculator + real-receipt proof
python3 scripts/primitive_benchmark_taxonomy.py --bench       # write the scalar-kernel receipt
```

## Promotion integration

`break_even_n_true`, `security_gate_status`, and `marginal_utility_status` feed the lifecycle: a
`benchmark_result` receipt is required for validated→certified (`docs/PRIMITIVE_LIFECYCLE.md`), and a
primitive with `marginal_utility_status == measured_no_lift` should be deprecated, not accumulated.
