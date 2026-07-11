# Primitive Experiment — paste-able prompt & command sheet

> Repo-accurate version of the 13-prompt suite. **Most of it is already built** — so these point at the REAL
> modules and say `RUN` (execute what exists) or `GAP` (genuinely missing). Laws already enforced in code:
> `no_proxy_gate.py` (proxy barred from headlines), candidate boundary (`candidate=true`/`serves_truth=false`),
> LLM-proposes/deterministic-disposes. Everything below is executed evidence, not projection.

## Prompt 0 — Global law (already enforced by code, not vibes)
- REAL = executed → `no_proxy_gate.py` classifies every benchmark module (21 audited); proxy modules are labeled and barred.
- Candidate boundary → every generated row is `candidate=true, serves_truth=false`.
- Paired-only savings → `real_savings_report.classify_pair` (a regression NEVER claims savings).

## Prompt 1 — Missing capabilities / accelerators — **BUILT**
```bash
python3 scripts/audit_missing_capabilities.py --run    # keys/tools/runtimes present + what each MISSING one unlocks
```
Headline today: `frontier_present=NO` (the #1 accelerator); docker 29.5.2 / uv / npm / playwright present; kind/kubectl/localstack missing. `GAP`: supervisor/hook framework (Prompt 1's `experiment_supervisors/`) not built — low ROI vs. running the executed lanes.

## Prompt 2 — Aggressive primitive generation — **BUILT (packs) + partial (live gen)**
```bash
python3 scripts/project_coverage_primitive_pack.py --certify   # 15 certified pure primitives (executed gate)
python3 scripts/cloud_function_primitive_pack.py --self-test
```
`GAP`: a multi-endpoint Hy3 generation *wave* runner. The live lane exists via the OpenRouter pool (`primitive_token_savings_ab.live_model`); scaling it needs a frontier key.

## Prompt 3 — Executor proof of generated primitives — **BUILT**
```bash
python3 scripts/saas_buildout_decomposer.py --self-test   # security scan -> determinism probe -> oracle fixtures
python3 scripts/certification_campaign.py --self-test      # security -> sandbox oracle -> determinism (5 lanes)
```

## Prompt 4 — Primitive usage / injection — **BUILT**
`run_large_project_ab.py` injects the certified coverage pack as an importable module; records `package_imported`, reuse, netted input+output tokens.

## Prompt 5 — Real project task bank + harness A/B — **BUILT**
```bash
python3 scripts/project_task_harness.py --self-test        # executed hidden oracle (cloud_function, ml_pipeline)
python3 scripts/project_live_agent_ab.py --live --model openai/gpt-oss-120b:free
```

## Prompt 6 — Large project / SaaS buildout — **BUILT**
```bash
python3 scripts/buildout_forge_large.py --self-test        # 11-module ops-API, 27-check hidden HTTP oracle
python3 scripts/buildout_forge_pipeline.py --self-test      # 10-module ETL DAG, 25-check oracle
python3 scripts/run_large_project_ab.py --live --genome backoffice_ops_api__stdlib_http__v0 --repeats 8
```
Non-insurance genomes (repo law forbids insurance families).

## Prompt 7 — RealAppForge — **BUILT (spine) + GAP (live discovery)**
```bash
python3 scripts/real_app_forge.py --catalog                # A0-A7 evidence ladder; A6/A7 only headline
python3 scripts/real_app_forge.py --promote back_office_ops_saas   # EXECUTES equivalent build -> A6
```
`GAP`: live discovery (find real apps → genomes) needs web/GitHub (token saved) + a frontier model. Only A6/A7 executed runs count.

## Prompt 8 — Harness backend grid — **BUILT (probe)**
```bash
python3 scripts/buildout_agent_backends.py --self-test      # 4 available: codex, aider, opencode, direct_api
```
`GAP`: wiring codex/aider as the *agent* in the A/B (currently direct_api pool). ClawCodex not installed.

## Prompt 9 — Real savings ledger + no-proxy — **BUILT**
```bash
python3 scripts/real_savings_report.py --run               # headline ONLY executed paired passes; distributions
python3 scripts/no_proxy_gate.py
```

## Prompt 10 — Failure mining — `GAP` (the decomposer's two-pass A/failed path is the seed).

## Prompt 11 — Supervised wave runner / DAG — `GAP` (each lane runs standalone today; a DAG wrapper is the next connective tissue, not new capability).

## Prompt 12 — Mega "run everything":
```bash
python3 scripts/audit_missing_capabilities.py --run
python3 scripts/bench_project_to_primitives.py --run       # primitive YIELD per built project
python3 scripts/run_large_project_ab.py --live --repeats 8
python3 scripts/real_savings_report.py --run
python3 scripts/no_proxy_gate.py
```

## Sources & search (Prompt "more sources")
```bash
python3 scripts/source_surface_catalog.py --catalog        # 13 families / 30 surfaces / 13 search methods
```
Includes docs.<domain>, RapidAPI Hub, APIs.guru, StackOverflow dump, textbooks, arXiv, standards, issue→PR repair. API-wrapper primitives reference credentials **by ENV NAME** (user-configurable); keys live in gitignored `.agent/<provider>_keys.txt`.

## The #1 unlock
A **frontier model key** (`ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `NVIDIA_API_KEY` GLM) — it passes the bare lane on LARGE builds, turning capability-lift into a clean token-SAVINGS number (the A7 tier). Free-tier gpt-oss is the current ceiling.
