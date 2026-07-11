# AIDevObserver Current State Summary

**Date:** 2026-06-29  
**Status:** alpha-grade product and architecture summary  
**Truth boundary:** all findings, registry matches, primitive drafts, and reuse cards are candidate evidence by default. `serves_truth=false` until proof, promotion, and production governance gates pass.

## One-Line Product

AIDevObserver is the review and reuse layer for AI coding sessions.

It watches or reviews what AI coding agents do, finds when they are reinventing code, workflows, templates, or generated components the primitive database already knows, and gives developers a cheaper reusable route before they spend more model tokens rebuilding the same thing.

## Product-Market Fit Thesis

The current wedge is not "AI commands can be risky." Developers and managers already know that.

The stronger wedge is:

```text
AI coding agents are repeatedly rebuilding solved work.
That wastes developer time, model tokens, review time, and team memory.
```

AIDevObserver should be positioned as a speed and reuse product:

- developers ship faster because they get pointed to existing helpers, templates, routes, and primitives;
- agents use fewer tokens because they can plan over compact edge records instead of reading or rewriting full source;
- teams build shared memory from accepted/reused/dismissed findings;
- managers can see where AI coding spend is becoming reusable capability.

The most direct user-facing promise:

```text
Stop AI coding agents from reinventing code the primitive database already knows.
```

## What Works Today

The current repo has a working alpha stack:

| Area | State |
| --- | --- |
| Post-session review | Working. `review_session()` delegates to the observer router in review-only mode. |
| Live advisory | Working. Claude Code PreToolUse hook emits non-blocking suggestions and never blocks tool execution. |
| MCP server | Working. Stdio JSON-RPC/MCP server exposes session listing, post-session review, and live review. |
| Local service | Working. HTTP service exposes `/review`, `/live`, `/agentic`, `/outcome`, `/outcomes`, `/registry/search`. |
| Web app | Working demo/alpha surface with Review, Sessions, Findings, Agentic, Examples, Reports, Developer, Settings. |
| Example sessions | Working. Replay/upload examples exist across scraping, enrichment, documents, ML, backend, frontend, workflows, and bugfix loops. |
| Local registry connector | Working seed. Indexes repo-relative Python callables, constants, docs, scripts, Claude skills/commands/hooks, MCP docs. |
| Outcome memory | Working seed. Accept/Reuse/Dismiss stores metadata-only outcomes and hashed source-ref keys. |
| Primitive candidates | Working seed. Local repo records can become `primitive_draft` candidates with contracts, effects, proof requirements, and `serves_truth=false`. |
| Reuse cards | In progress / newly wired. Local registry hits and enriched review findings can now expose compact `reuse_card` edge records. |
| Deterministic build demand surface | Proposed / registered. `DeterministicBuilds.io` is a request, vote, bounty, and proof-backlog surface for moving repeated LLM/agent behavior into deterministic primitive/template routes. |
| Global primitive lifecycle | Working seed. `_repos/shared-backend-components/scripts/primitive_source_lifecycle.py` packages source candidates and primitive opportunities into digests, implementation backlog rows, search cards, summaries, and deterministic staging vectors. |
| Global multi-model primitive foundry | Design contract + offline proof. Codex, Ollama-hosted GLM/Kimi lanes, browser capture, and deterministic gates cooperate from source discovery to primitive proof without letting model output become truth. Defaults are `glm-5.2` for research/planning and `kimi-k2.7-code` for code critique. |

Recent proof commands passing:

```bash
python3 _repos/shared-backend-components/scripts/check_observer_review.py --self-test
python3 _repos/shared-backend-components/scripts/check_aidevobserver_local_registry_connector.py --self-test
python3 _repos/shared-backend-components/scripts/check_observer_local_service.py --self-test
python3 _repos/shared-backend-components/scripts/aidevobserver_hook.py --self-test
python3 _repos/shared-backend-components/scripts/aidevobserver_mcp_server.py --self-test
python3 _repos/shared-backend-components/scripts/check_aidevobserver_vscode_ext.py --self-test
python3 _repos/shared-backend-components/scripts/check_aidevobserver_example_sessions.py --self-test
python3 _repos/shared-backend-components/scripts/check_aidevobserver_launch_readiness.py --self-test
python3 _repos/shared-backend-components/scripts/check_global_multimodel_primitive_foundry.py --self-test
```

## What The Review Detects

Primary categories:

| Finding Type | Meaning |
| --- | --- |
| Reinvention | Agent is rebuilding a helper, workflow, parser, integration, model pipeline, or product surface that likely already exists. |
| Stack reinvention | Agent is rebuilding behavior already covered by an existing dependency stack. |
| Wasted context | Agent reads, pastes, or resends too much context when a compact search/summary primitive would work. |
| Missed cheaper path | Agent uses model reasoning where deterministic search, registry lookup, or a known tool is cheaper. |
| Agentic loop | Autonomous agent repeats failed work, stalls, drifts from goal, or overruns budget. |
| Missing proof | Agent changes code without expected tests, replay, contract report, or validation. |
| Safety signal | Destructive command, secret exposure, or policy-sensitive operation. Useful, but not the main adoption wedge. |

## Reuse Card Shape

The important next product object is the `reuse_card`.

A reuse card is a compact object/edge that lets a human or LLM agent understand what to reuse without reading all the code.

Target shape:

```json
{
  "kind": "reuse_card",
  "primitive_id": "prim:candidate:local-repo:...",
  "label": "scripts.ingest.csv.read_rows",
  "record_type": "primitive_draft",
  "source_kind": "first_party_repo_record",
  "contract": {
    "input": "Args[text:str,required_headers:Iterable[str]]",
    "output": "list[dict[str,str]]"
  },
  "effects": [],
  "memory": "inline",
  "cache": "content_hash",
  "readiness": "R3_contract_known",
  "trust": "candidate",
  "source_ref": {
    "registry": "local_repo",
    "kind": "python_function",
    "name": "read_rows",
    "path": "utils/csv.py",
    "line": 12
  },
  "match_reason": {
    "finding_type": "reinvention",
    "matched_terms": ["csv", "parser", "read"],
    "score": 9
  },
  "proof_requirements": [
    "source_ref_exists",
    "source_fingerprint_review",
    "contract_review",
    "unit_or_usage_proof",
    "privacy_boundary_review",
    "promotion_review"
  ],
  "candidate": true,
  "serves_truth": false
}
```

This is the bridge between:

```text
"This looks inefficient"
```

and:

```text
"Use this existing object: input X -> output Y, effects Z, proof still required."
```

## Solutioning Model

AIDevObserver has two modes.

### Mode A: Observer Review Mode

This is the current product wedge.

```text
session transcript or live tool event
  -> deterministic review/router modules
  -> optional local registry enrichment
  -> ranked candidate findings
  -> reuse cards and source refs
  -> human Accept / Reuse / Dismiss
  -> hashed outcome memory
```

Mode A is lightweight, useful immediately, and does not require the user to understand Teleon internals.

### Mode B: Teleon Route Mode

This is the deeper infrastructure path.

```text
accepted finding or normalized intent
  -> primitive/template search
  -> CandidateBundle
  -> compact PlanDelta or deterministic route
  -> compiler validation
  -> RemixSurface / VariationRecord when needed
  -> PlanLock
  -> runtime ledger
  -> proof/promotion
```

Mode B should remain behind the technical drill-down until the user understands the value of Mode A.

## Python Setup And Project Compatibility

AIDevObserver is designed to fit ordinary Python and Claude Code style projects without forcing a new framework.

Important Python surfaces:

| Surface | Role |
| --- | --- |
| Python functions/classes/constants | Indexed as local repo source refs and primitive draft candidates. |
| Function annotations | Used to infer compact input/output contracts when available. |
| AST fingerprints | Used as source evidence so callable identity is not just path/name. |
| `pyproject.toml` scripts | Indexed as command/entrypoint source refs. |
| `package.json` scripts | Indexed for mixed JS/Python repos. |
| `CLAUDE.md` | Project-level agent instructions and reusable context. |
| `skills/*/SKILL.md` | Capability procedures agents can reuse. |
| `commands/*.md` | Slash-command workflow templates. |
| `hooks/*.md` | Hook policy and integration docs. |
| `mcp/*.md` | MCP connector documentation. |
| `session-log.md` | Private session memory surface. |

Scaffold command:

```bash
python3 _repos/shared-backend-components/scripts/aidevobserver_project_scaffold.py --framework python --write
```

Local review service:

```bash
python3 _repos/shared-backend-components/scripts/observer_local_service.py --serve
```

Claude Code MCP:

```bash
claude mcp add aidevobserver -- python3 _repos/shared-backend-components/scripts/aidevobserver_mcp_server.py
```

Claude Code PreToolUse hook:

```bash
python3 _repos/shared-backend-components/scripts/aidevobserver_hook.py --install
```

Local registry search is opt-in. Public demos should not expose local paths or local sessions.

## Deterministic Rules And Governance

Core deterministic rules:

- All findings are candidate advice, not truth.
- Every finding and reuse card carries `serves_truth=false`.
- The local registry connector emits repo-relative paths, not absolute paths.
- Outcome memory stores metadata and hashed source-ref keys, not transcript text.
- Public demos disable local session discovery and local registry exposure by default.
- Live hook is non-blocking and fail-open.
- MCP server is read-only.
- Review reports are ranked by deterministic confidence scores.
- Source refs and contracts are compact views; full source should not be required for the first planning step.
- Primitive drafts require proof before promotion.

Compiler/proof concepts inherited from Teleon:

- Python objects/functions are authoring handles.
- Canonical records are registry truth.
- Compact generated views are LLM/search boundaries.
- PlanDelta is candidate intent.
- PlanLock is execution truth.
- Ledger records observed runtime reality.
- Proof/promotion decides what can serve truth.

## Current Architecture

```text
web / editor / CLI / MCP / hook
  -> observer local service
  -> review_session / route_session
  -> deterministic modules:
       reinvention
       stack reinvention
       wasted context
       duplicate context
       footgun
       guidance
       alternative
       agentic loop
  -> optional local registry connector
  -> source refs + reuse cards
  -> outcomes / memory
  -> reports
```

Important implementation files:

| File | Role |
| --- | --- |
| `_repos/teleon/backend/src/teleon/observer/router.py` | Core review/live router and intervention modules. |
| `_repos/teleon/backend/src/teleon/observer/review.py` | Post-session review wrapper over router. |
| `_repos/teleon/backend/src/teleon/observer/local_registry_connector.py` | Local repo indexing, search, primitive candidate generation. |
| `_repos/shared-backend-components/scripts/observer_local_service.py` | HTTP service over observer engine. |
| `_repos/shared-backend-components/scripts/aidevobserver_hook.py` | Claude Code PreToolUse live coaching hook. |
| `_repos/shared-backend-components/scripts/aidevobserver_mcp_server.py` | MCP stdio server. |
| `_repos/aidevobserver/frontend/aidevobserver-main.jsx` | App routes, review UI, findings UI, examples, reports. |
| `_repos/aidevobserver/frontend/examples/manifest.json` | Replay/upload example manifest. |

## Current Demos And Example Families

The demo session library currently covers:

- web scraper for regulatory rates;
- company/entity enrichment;
- document-to-JSON schema extraction;
- support ticket classification;
- revenue regression pipeline;
- Kaggle-style tabular baseline;
- Kaggle-style image classification baseline;
- Kaggle-style text classification baseline;
- safe pyprefix migration;
- workflow replay debugger;
- n8n workflow distillation;
- frontend component quality gate;
- backend policy API;
- data engineering CSV ingestion;
- RAG docs search app;
- CI workflow generation;
- bugfix repeated test loop.

These should be expanded with real-source-derived sessions rather than purely synthetic examples.

## Launch Readiness

Current status:

```text
demo-ready / alpha-grade
not yet public commercial launch-ready
```

Ready enough for:

- controlled demos;
- external technical feedback;
- private alpha planning;
- local dogfooding;
- review-engine benchmarks;
- primitive/reuse-card iteration.

Not ready for:

- broad public SaaS launch;
- paid team onboarding without hands-on support;
- claims of broad registry precision;
- automated promotion/truth serving;
- fully packaged VS Code/Cursor marketplace distribution.

## Main Gaps

Highest-priority gaps:

1. Reuse cards need to be shown consistently in the UI and returned consistently across API/MCP/editor surfaces.
2. Registry search needs broader real-source coverage beyond local Python/docs/scripts.
3. Source-ref precision needs benchmark targets and clean-session false-positive controls.
4. The setup path needs one excellent packaged alpha route: probably scaffold + CLI/MCP first.
5. The product needs persistent workspace/team outcome memory for real alpha customers.
6. The public demo needs a stable deployment path, not only temporary quick tunnels.
7. Browser/editor extension path needs packaging and install docs.
8. Launch copy should keep safety secondary and lead with speed, reuse, and token savings.

## Best Next Steps

Recommended next loop:

1. Finish and prove reuse cards in `/registry/search`, `/review`, MCP, and UI.
2. Add a fixture where an agent writes a CSV parser and the review returns a reuse card with `input -> output`.
3. Add a cloud-function/Kubernetes fixture from the checklist research.
4. Expand local registry connector to detect YAML/IaC/workflow files.
5. Add benchmark assertions for top-1 and top-3 source-ref accuracy on reuse cards.
6. Package the Claude scaffold + MCP + hook path into a single documented alpha setup.
7. Keep generating source-backed primitive drafts from real public surfaces and accepted local findings.
8. Use the DeterministicBuilds.io-style leaderboard to prioritize which repeated LLM/agent workflows should become deterministic primitives next.

Important architecture correction: primitive digesting and vectorization are not
AIDevObserver-specific. AIDevObserver is a review/signal surface. The global
primitive lifecycle belongs to the broader OpenHubForAI/Teleon infrastructure so
all systems can benefit from the same primitive database.

## Summary Verdict

AIDevObserver has the right product shape and the first working technical spine:

```text
review session
  -> find reinvention/waste
  -> attach source refs
  -> expose compact reuse edges
  -> collect human outcomes
  -> improve registry memory
```

The next milestone is not more abstract architecture. It is making every high-confidence finding produce a clear, test-covered, LLM-readable reuse card so a developer or agent can reuse the object immediately without rereading or rewriting the source.
