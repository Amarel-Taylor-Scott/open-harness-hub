# PMF / Market / Wedge / Lift / SWOT — grounded in executed evidence

> Research brief for owner decision — NOT a locked strategy (design/pricing/brand is never a unilateral agent
> call; this is analysis to decide from). **Two evidence classes are kept separate:** (A) *our executed internal
> evidence* (receipts this repo produced) and (B) *reported market figures* (from owner-provided briefs / public
> surveys, **not independently verified in this session** — treat as directional). `serves_truth=false`.

## 0. One-line thesis (grounded)
Not "a database of primitives." The product is a **primitive supply-chain + real-project A/B lab**: decompose
real work into deterministic primitives, **certify by execution**, inject into coding/agent harnesses, and
**prove tokens-to-pass / cost-per-pass lift on real projects** — with a no-proxy gate that makes the number
trustworthy. *"CI/CD for AI-generated reusable work."*

## 1. What we have ACTUALLY proven (executed receipts, this session)
| Claim | Evidence | Status |
|---|---|---|
| Building a large project surfaces many reusable primitives | `bench_project_to_primitives`: **28–34 candidates/project** (ops-API 34, ETL DAG 28), deterministic | **PROVEN** |
| Decompose→certify by execution works | `saas_buildout_decomposer` + coverage pack: 15 primitives certify oracle_correct via executed gate | **PROVEN** |
| Real projects build + pass hidden oracles | `buildout_forge_large` (11-module, 27 checks), `_pipeline` (10-module, 25 checks) boot/run + oracle | **PROVEN** |
| The measurement is honest | `no_proxy_gate` (22 modules) bars proxy from headlines; `real_savings_report` headlines only executed paired passes | **PROVEN** |
| **Primitives reduce tokens on real projects** | n=4 buildout A/B: mean **+9.5%**, range **−9.6%…+20.9%, 1 negative** at single-primitive coverage | **NOT ROBUST YET** |
| A capable model passes the large bare lane | frontier lanes now wired + probed (qwen3-coder-480b, codestral, gpt-4o via free GitHub Models); A/Bs running | **IN TEST** |

**The honest gap = the whole PMF risk:** project-level savings are real but *noisy and small* until (a) a
frontier model passes the bare lane and (b) **macro/coverage** primitives (auth/billing/worker/CRUD modules),
not one micro-primitive, are injected. Everything else is built.

## 2. Market pull (reported — directional, not verified here)
AI coding is mainstream and spend is rising: reported figures include ~84% of developers using/planning AI
tools, Copilot ~20M users, Gartner "75% of enterprise engineers by 2028," and a Gartner warning that AI coding
*cost* could overtake developer salary by 2028. **If even directionally true, the wedge is "make agent coding
cheaper + more reliable with proof"** — exactly what deterministic zero-runtime-token primitives target. (I did
not re-verify these numbers this session; cite them as reported.)

## 3. The gap (grounded)
The market **generates, orchestrates, connects** (Copilot/Cursor/Codex; Replit/Lovable/Bolt; Zapier/n8n/UiPath;
Postman/RapidAPI/MCP; Claude/Codex Skills). It largely does **not certify, package, measure, and reuse
deterministic work units with executed proof.** Skills/docs/APIs/repos/buildouts are *source material*; the open
lane is **converting them into certified deterministic primitives with receipts** — which is precisely the loop
we built (source_surface_catalog → decomposer → certify → run_large_project_ab → real_savings_report).

## 4. Wedge — recommendation: **Real-project A/B for AI coding spend** (Wedge A)
Closest to proven, clearest buyer pain, and we already hold the machinery.
- Pitch: *"Benchmark your coding agents on your real project tasks; cut cost-per-pass + repair turns by injecting certified primitives — with executed receipts."*
- We have: `run_large_project_ab` (bare vs certified-primitives, netted tokens, distributions), genomes, coverage packs, `real_savings_report`, 8-provider + free harness lanes.
- Secondary wedges (built cores, ordered by scalability of source): **DocsDomainForge** (`docs_api_forge`: OpenAPI→user-keyed mock-proven wrappers) · **InstructionFileForge** (`instruction_file_miner`: SKILL.md/CLAUDE.md/AGENTS.md→deterministic capabilities + CI gates) · **RealAppForge** (`real_app_forge`: real apps→equivalent buildouts, A6/A7). Each rides a standard surface (OpenAPI/AGENTS.md/app-builders).

## 5. Lift metric (what "lift" must mean)
Not tokens alone → **quality-adjusted cost-per-passing-project**:
`cost_per_pass = (model_cost + harness_runtime + amortized_primitive_gen + validation + human_review) / oracle_pass_count`.
Track the deltas we already capture (pass-rate, input+output tokens-to-pass, repair turns) + add cost + wall-time.
A primitive earns its place only if it improves ≥1 of: pass rate · tokens-to-pass · repair turns · latency ·
safety · reproducibility · human-review reduction. (`real_savings_report` already enforces paired-both-pass +
no-proxy; extend it to cost-per-pass.)

## 6. Capability map → what's BUILT vs GAP
| Pillar | Built this session | Gap |
|---|---|---|
| Source ingestion | `source_surface_catalog` (13 families/30 surfaces), auditor | live crawlers (token-gated) |
| Decomposition | `saas_buildout_decomposer`, `bench_project_to_primitives` (28–34/proj) | — |
| Generation | coverage/cf packs; multi-provider `live_model` (8 providers + free GitHub Models) | scaled gen wave |
| Certification | executed security→determinism→oracle gate | stateful/fitted cert (task #21) |
| Injection | `run_large_project_ab` (bare vs coverage pack) | macro-primitive lane, more lanes (skills/scaffold/compiled-route) |
| Measurement | `real_savings_report` (paired, netted, distribution) | cost-per-pass; n≥8 across families |
| Governance | `no_proxy_gate`, candidate/truth boundary, credential env-name discipline | — |
| Macro-primitives | (micro coverage pack only) | **auth/billing/worker/CRUD module primitives = the savings lever** |
| Failure mining | decomposer two-pass seed | failure→primitive queue |

## 7. SWOT (grounded)
- **Strengths:** no-proxy discipline *enforced in code*; executed decompose→certify→A/B loop *built*; 28–34 yield *proven*; cross-harness/cross-provider *built*; "LLM proposes, deterministic disposes" is a clean, defensible thesis.
- **Weaknesses:** project savings **not robustly proven** (noisy, sometimes negative at micro coverage); **macro-primitive coverage thin**; system complexity high; convincing runs need capable models (now unblocked) + quota.
- **Opportunities:** rising AI-coding spend; skills/AGENTS.md standardizing (portable source); API-docs surface is enormous; app-builders repeat the same SaaS scaffolds (macro-primitive ore).
- **Threats:** incumbents (Cursor/GitHub/Anthropic/OpenAI) could add reuse/caching/skill registries; **benchmark skepticism** if any claim ever leans on proxy (our gate is the defense); a security incident from public ingestion (mitigated: candidate-only, mock-first, env-name creds, security scan).

## 8. The strongest objection + answer
*"Why won't Cursor/GitHub/OpenAI/Anthropic/Replit just build this?"* → They sell model/runtime usage or a
single coding surface; their incentive is *more* tokens, not fewer. The neutral, **cross-harness proof +
primitive supply-chain** layer (source→deterministic conversion→executed certification→no-proxy A/B→provenance→
reuse) is orthogonal to any one vendor. Moat = the **executed real-project A/B dataset + certified corpus +
source→primitive pipelines + failure-to-primitive flywheel**, not "we have lots of cards."

## 9. Best next experiment (the PMF test — mostly built, needs runs)
30 paired A/B runs across 3 families (API-service-with-DB · K8s/data worker · SaaS buildout), lanes =
harness_alone / +cards / +certified-primitives / **+macro-primitives**, on a **frontier model** (qwen3-coder-480b
/ codestral / free gpt-4o), reporting pass-rate + input+output tokens-to-pass + repair turns + **cost-per-pass**,
no-proxy green. **Threshold for PMF signal:** ≥10% cost-per-pass reduction OR ≥10% pass-rate lift OR ≥20%
repair-turn reduction on ≥1 family, robust at n≥8.

## 10. What to avoid (from our own laws)
Don't sell "1M primitives" (sell certified lift). Don't headline tokens-only (sell cost-per-pass + auditability).
Don't start with regulated truth-serving (start with dev productivity/buildouts). Don't let candidate tiers into
production search. Don't benchmark only function-level (degenerate — proven this session). Keep the no-proxy gate.
