# Claude 5 Fable All-Surfaces, Primitives, And Tools Handoff

Last updated: 2026-07-01

Audience: Claude 5 Fable, Claude Code, Codex, and model/tool lanes that need
to continue AI Done Right surface polish and primitive growth.

Status: operational handoff. This document is not a truth source for generated
state. Recompute surface inventories, catalog counts, model lanes, and current
run metrics from the owning scripts and manifests before acting.

## Why This Exists

The current development tools and model lanes, including Codex, Claude Code,
Kimi, GLM, and Gemma 4, should be treated as non-looping unless an active
process, ledger, stop file, and fresh output prove otherwise. Do not assume a
tool will keep working in the background after one prompt, one command, one
browser session, or one model call.

Claude 5 Fable should use this file as the top-level pass-off for:

- cleaning up the repo and handoff surface;
- improving the product surfaces and shared design system;
- improving tools, primitive cards, primitive groups, and candidate pipelines;
- starting more primitive generation without weakening proof, source, privacy,
  or truth boundaries.

## Read First

Read in this order before editing:

1. `AGENTS.md`
2. `CLAUDE.md`
3. `README.md`
4. `taxonomy/SPEC.md`
5. `docs/BIBLE.md`
6. `docs/DESIGN-BIBLE.md`
7. `docs/INTEGRATION-BIBLE.md`
8. `docs/codex/baltor-always-in-memory-context.md`
9. `docs/codex/no-magic-values.md`
10. `docs/codex/surface-and-development-contract.md`
11. `docs/codex/ai-done-right-family-polish-goal.md`
12. `docs/codex/repo-polish-loop-goal.md`
13. `docs/codex/claude-fable-primitive-database-handoff.md`
14. `docs/codex/claude-fable-compiled-primitive-routes-handoff.md`
15. `docs/codex/primitive-family-expansion-handoff.md`
16. `docs/codex/primitive-variation-dimension-atlas-handoff.md`
17. `docs/codex/primitive-customization-overlays-handoff.md`
18. `docs/codex/primitive-agent-graph-path-mixtures-handoff.md`
19. `docs/codex/primitive-cloud-guardrail-runtime-handoff.md`
20. `docs/codex/high-priority-primitive-opportunity-rankings-handoff.md`
21. `docs/codex/primitive-problem-solution-details-handoff.md`
22. `docs/codex/marketplace-primitive-source-surfaces-handoff.md`
23. `docs/codex/primitive-factory-fable5-handoff.md`
24. `docs/codex/global-multimodel-primitive-foundry.md`
25. `docs/codex/primitive-source-lifecycle.md`
26. `docs/codex/primitive-registry-operational-schema.md`
27. `docs/codex/quality-gates.md`

If these disagree, prefer the more canonical source named in the disagreement.
Do not silently pick an old count, old route, old product name, or old model ID.

## Operating Constraint

Non-looping means every loop must be explicit and observable:

- Use bounded loops first: `--max-cycles 1`, `--max-ticks 1`, `--dry-run`, or
  script self-tests before any open-ended run.
- Use stop files for long loops and check the ledger after every cycle.
- Verify the process is still alive before saying a loop is running.
- Verify the output manifest changed before saying a loop produced work.
- Never report raw model output as promoted primitives.
- Never flip `serves_truth=true` from a model lane.

When a tool blocks, switch lanes. Example: if Gemma browser-context CDP is
blocked, run GLM/Kimi direct lanes through the provider fleet planner, then keep
deterministic verification moving.

## Product Boundaries

Keep the portfolio split clear:

- AI Done Right is the parent and portfolio story.
- OpenHubForAI is the open catalog and registry substrate.
- Teleon governs executable capability, runtime selection, adapters, proof, and
  receipts.
- Baltor governs verified context and truth-serving packs.
- AIDevObserver observes AI-assisted development and recommends reuse routes.
- AIDevObserver's benchmark lab tests primitive-first development against
  baseline AI coding. `aidevexplorer` is a legacy/internal namespace, not a
  branded surface.

Architecture law stays intact:

```text
Baltor -> Teleon -> OpenHubForAI
```

Do not invert this dependency. Open discovery is not trust. Candidate registry
rows are planning evidence until proof and promotion gates pass.

## Surface Workstream

Before changing a surface, recompute what exists. Treat any hand-typed surface
count in prose as a snapshot to verify, not a rule.

Run focused discovery first:

```bash
python3 scripts/check_ai_done_right_surface_family.py --self-test
python3 scripts/check_handoff_docs_freshness.py --self-test
python3 scripts/check_portfolio_dependency_law.py --self-test
```

Read these owning sources when inventory or routes matter:

- `services/registry.yaml`
- `architecture/surface_capability_spec.json`
- `architecture/demo_surface_registry.json`
- `architecture/local_service_registry.json`
- `architecture/identity_realm_registry.json`
- `web/`
- `scripts/showcase/server.py`
- `docs/DESIGN-BIBLE.md`
- `docs/INTEGRATION-BIBLE.md`

The built-out product apps are under `web/`. Serve them through the showcase,
not a skinny replacement server:

```bash
OH_PRODUCT=<product-id> python3 -m scripts.showcase --port <unused-port>
```

Use product IDs from the owning registry or `web/` app roots, and prefer
`scripts/serve_all_sites.sh` when the repo launcher is the better fit. If a port
is busy, pick an unused port and record it. If a backend returns unimplemented
data, wire the same-origin seam or label the state honestly; do not replace the
full app with a static stub.

### Surface Cleanup Priorities

Fix the highest-impact failure first:

1. active surface does not render or routes to the wrong app;
2. primary backend seam errors without an honest disabled state;
3. broken navigation, dead CTA, dead route, or stale share URL;
4. text overlap, horizontal overflow, poor mobile layout, or inaccessible
   controls;
5. design drift from shared kit tokens, components, or product copy;
6. product-boundary confusion between Baltor, Teleon, OpenHubForAI,
   AIDevObserver, and AI Done Right;
7. stale docs or handoff text that would mislead the next agent.

Use the design system in `web/<app>/kit/`. Accent and copy are the per-surface
variables. Do not create a new design language for one app unless the design
bible has changed first.

## Primitive And Tool Workstream

There are two related vocabularies. Keep them distinct:

- The product UI has seven primitives: Input, Knowledge Corpus, If Statement,
  Action, Loop, Stop / End, Output.
- The primitive database stores edge cards and primitive groups, usually shaped
  as `InputEdge -> OutputEdge`, with effects, runtime shapes, proofs, and
  promotion status.

Every tool, harness, adapter, processor, persona, rubric, and benchmark is an
Action when exposed in the seven-primitive UI. Tool manifests must declare side
effects, trust boundary, parameters, returns, examples, and implementation
status. Volatile facts belong in tools or Knowledge Corpus rows, not personas.

Problem and solution details belong in linked detail records, not in every
compact primitive card. Use
`docs/codex/primitive-problem-solution-details-handoff.md` and
`catalog/knowledge-packs/data/primitive-problem-solution-details/` when a
primitive needs problem framing, user triggers, acceptance criteria, proof
plans, failure modes, troubleshooting hooks, and synthetic examples.

High-volume primitive growth belongs in JSONL staging, manifests, candidate
tables, and database load paths. Do not create thousands of hand-written static
catalog files for raw model output.

### Truth Boundary

Default generated state:

```text
candidate=true
serves_truth=false
```

This remains true for model-written rows, source-backed candidate cards, vector
rows, search cards, lifecycle digests, route candidates, and benchmark
decompositions until proof and promotion gates explicitly say otherwise.

Use quality levels when reporting primitive work:

```text
L0 raw observation
L1 model draft row
L2 extracted schema-valid candidate row
L3 source-backed database candidate
L4 tested candidate with fixture/proof receipt
L5 promoted primitive
L6 preferred primitive group route
```

Report level-specific progress. Do not collapse these levels into one
"generated primitives" number.

### Primitive Generation First Cycle

Start with dry runs and self-tests:

```bash
python3 scripts/check_global_multimodel_primitive_foundry.py --self-test
python3 scripts/primitive_source_lifecycle.py --self-test
python3 scripts/check_primitive_factory_5k_lanes.py --self-test
python3 scripts/plan_primitive_provider_fleet.py --target-profile 20k --scale 1 --check-only
python3 scripts/run_primitive_provider_fleet_loop.py --target-profile 20k --scale 1 --max-cycles 1 --dry-run
python3 scripts/run_primitive_verification_loop.py --max-ticks 1
```

Then run one real bounded generation cycle only after the dry run names valid
lanes, source shards, output paths, and stop behavior:

```bash
python3 scripts/plan_primitive_provider_fleet.py --target-profile 20k --scale 1
python3 scripts/run_primitive_provider_fleet_loop.py --target-profile 20k --scale 1 --max-cycles 1
python3 scripts/run_primitive_verification_loop.py --max-ticks 1
python3 scripts/primitive_source_lifecycle.py --limit 100
```

Read the resulting manifests before claiming output. If the scripts write a
command file, inspect it before executing model calls.

### Model Lane Roles

Use the provider planner and config registries for current model IDs. Do not
hard-code model strings into new durable docs, scripts, or primitive records.

Expected lane responsibilities:

| Lane | Use it for | Do not use it for |
| --- | --- | --- |
| Codex | repo edits, validation, deterministic packaging, proofs, docs | promoting model output to truth |
| Claude Code / Fable | surface cleanup, design review, repo polish, primitive implementation planning | bypassing repo checks or source gates |
| Gemma 4 | compact candidate writing and coding-helper passes where the endpoint is healthy | source licensing decisions or truth promotion |
| GLM | broad candidate generation, source triage, contract review | copying raw source into public rows |
| Kimi | long contract expansion, code critique, edge cases, test plans | unreviewed patch merges or proof certification |

Multiple models improve recall. Deterministic gates decide promotion.

## Cleanup Workstream

When the task is "clean things up," start with drift that can mislead future
agents:

- stale handoff counts or route maps;
- docs that say a surface is built when it is fallback-only;
- duplicate source-of-truth lists for surfaces, model IDs, ports, row families,
  thresholds, or paths;
- generated output mixed with promoted source;
- unregistered `--self-test` modules;
- primitive rows without source refs, proof blockers, or truth-boundary fields;
- tool manifests missing side effects, trust boundaries, examples, or runtime
  assumptions;
- UI states that hide failure instead of naming the reason and next action.

Prefer the existing scripts, registries, shared kit, ports, and validation
helpers. Reuse first:

```bash
python3 scripts/check_reinvention_guard.py
python3 scripts/check_substrate_layers.py
python3 scripts/codegraph.py --audit <area>
```

## Validation Contract

Run focused checks for what changed.

For docs-only handoff changes:

```bash
python3 scripts/check_ai_done_right_surface_family.py --self-test
python3 scripts/check_handoff_docs_freshness.py --self-test
```

For surface changes:

```bash
python3 scripts/check_ai_done_right_surface_family.py --self-test
python3 scripts/check_surface_server.py --self-test
```

Also run syntax checks for touched JavaScript files and verify the showcase app
in a browser or with the repo's existing surface verification tools.

For catalog YAML changes:

```bash
python3 scripts/validate.py <changed catalog paths>
python3 scripts/build_component_id_index.py --update <changed catalog paths>
python3 scripts/build_catalog_pages.py --paths <changed catalog paths> --update-index
python3 scripts/build_component_id_index.py --check-fresh
```

For primitive/foundry changes:

```bash
python3 scripts/check_global_multimodel_primitive_foundry.py --self-test
python3 scripts/primitive_source_lifecycle.py --self-test
python3 scripts/check_primitive_factory_5k_lanes.py --self-test
python3 scripts/run_primitive_provider_fleet_loop.py --self-test
python3 scripts/run_primitive_verification_loop.py --self-test
```

For service/auth changes:

```bash
python3 scripts/check_service_auth_consumption_model.py --self-test
```

If a check fails because of environment, network, missing credentials, or a
blocked model endpoint, record the exact blocker and switch to the next safe
gate. Do not mark the work done without a substitute focused check.

## Output Contract For Every Fable Cycle

End each cycle with a concise status note that includes:

- surfaces discovered or inspected;
- files changed;
- primitive/tool rows generated, verified, or packaged by quality level;
- checks run and pass/fail results;
- truth-boundary status for generated rows;
- any blocked lane and the next unblocked lane;
- the next highest-impact gate.

If the cycle generated model output, include manifest paths and rejection
reasons. If the cycle changed UI, include the surface and route verified. If
the cycle changed tools or primitives, include the exact validation command.

## Paste-Ready First Prompt For Claude 5 Fable

```text
Read docs/codex/claude-5-fable-all-surfaces-primitives-tools-handoff.md and
follow it. Treat Codex, Claude Code, Kimi, GLM, and Gemma 4 as non-looping
unless current processes and ledgers prove otherwise. Recompute the current
surface inventory, pick the highest-impact failing surface/design/repo-cleanup
gate, make the smallest durable fix, run focused checks, then start one bounded
primitive/tool generation or verification cycle. Keep all generated rows
candidate=true and serves_truth=false unless a dedicated promotion gate says
otherwise. Report files changed, checks run, manifests written, blockers, and
the next gate.
```
