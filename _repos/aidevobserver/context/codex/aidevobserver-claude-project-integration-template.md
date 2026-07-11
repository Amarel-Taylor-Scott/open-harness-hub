# AIDevObserver Claude Project Integration Template

Date: 2026-06-28

This guide shows how to make AIDevObserver compatible with common Claude Code, Cursor, VS Code, and agentic development project layouts.

The goal is not to force every team into one framework. The goal is to make the common project artifacts that AI agents already read - `CLAUDE.md`, skills, slash commands, hooks, MCP servers, package scripts, framework config, tests, workflows, and docs - visible to AIDevObserver as reusable context and primitive evidence.

The product rule stays the same:

```text
AIDevObserver reviews sessions and source surfaces.
It produces candidate findings and candidate primitive records.
It does not promote truth by itself.
Every generated candidate defaults to serves_truth=false.
```

## Recommended Project Layout

Use this shape for a project that wants Claude-style ergonomics and AIDevObserver compatibility:

```text
.
├── CLAUDE.md
├── session-log.md
├── hooks.md
├── skills/
│   ├── project-reviewer/
│   │   └── SKILL.md
│   ├── data-ingestion/
│   │   └── SKILL.md
│   ├── frontend-quality/
│   │   └── SKILL.md
│   └── release-proof/
│       └── SKILL.md
├── commands/
│   ├── review-session.md
│   ├── find-reuse.md
│   ├── refresh-primitives.md
│   └── review-output.md
├── hooks/
│   ├── pretooluse-aidevobserver.md
│   ├── posttooluse-session-note.md
│   └── stop-session-summary.md
├── mcp/
│   ├── connections.md
│   └── aidevobserver.md
└── .claude/
    └── settings.json
```

This mirrors typical Claude project setups without making the repo depend on Claude only. The same files also help Cursor, VS Code, CLI users, CI jobs, and future OpenHubForAI registry ingestion.

To generate this layout in a project, run a dry run first:

```bash
python3 _repos/shared-backend-components/scripts/aidevobserver_project_scaffold.py --framework python
```

Then write the files when the target looks right:

```bash
python3 _repos/shared-backend-components/scripts/aidevobserver_project_scaffold.py --framework python --write
```

Supported framework profiles:

```text
generic
frontend
python
data
workflow
media
```

## How AIDevObserver Reads The Layout

| Project surface | AIDevObserver role | Registry output |
| --- | --- | --- |
| `CLAUDE.md` | Project instruction pack and reusable development policy | Context-pack candidate |
| `session-log.md` | Human-maintained session memory summary | Digest-backed session memory candidate |
| `hooks.md` | Hook policy overview | Integration documentation candidate |
| `skills/*/SKILL.md` | Repeatable capability definition | Skill / primitive-family candidate |
| `commands/*.md` | Slash-command workflow | Template / workflow candidate |
| `hooks/*.md` | Live review policy and hook install notes | Hook integration candidate |
| `mcp/*.md` | MCP connection documentation | Tool connector candidate |
| `.claude/settings.json` | Local Claude Code hook/MCP wiring | Private integration evidence only |
| `package.json`, `pyproject.toml`, `Makefile` | Build/test/review commands | Script primitive candidates |
| `src/`, `app/`, `pages/`, `api/` | Application code | Function/class primitive candidates |
| `tests/`, `fixtures/`, `evals/` | Proof evidence | Proof and benchmark candidates |
| `.github/workflows/` | CI workflows | Workflow primitive candidates |
| `n8n/`, `workflows/`, `dags/` | Automation workflows | Pipeline/template candidates |
| `notebooks/`, `kaggle/` | Data/ML experiments | Data-science session and primitive candidates |

The current local registry connector extracts repo-relative source refs, annotation-derived contracts for Python callables, compact callable surfaces, source/contract/record fingerprints, and candidate-only primitive rows. It intentionally avoids raw private transcript text, absolute local paths, and proof-free truth claims.

## CLAUDE.md Section To Add

Add a short AIDevObserver section to the project `CLAUDE.md`:

```md
## AIDevObserver

Before building a new helper, workflow, parser, scraper, API adapter, data pipeline, UI quality gate, or model/eval harness:

1. Search existing repo helpers and registry primitives first.
2. Prefer an existing route over recreating a utility.
3. If a new helper is needed, keep the contract explicit and testable.
4. Run a session review before shipping substantial AI-generated work.
5. Treat AIDevObserver findings as candidate advice, not automatic truth.

Useful commands:

- `/find-reuse` before writing a new utility.
- `/review-session` at the end of an AI coding session.
- `/review-output` before merging generated code.
```

This is the sentence that should steer the agent:

```text
Do not reinvent code or workflows the primitive database already knows.
```

That is broader than "your team already has it." The source might be your repo, another team, prior generated code, OpenHubForAI, n8n workflow distillation, Kaggle-derived patterns, public examples, or a promoted primitive record.

## Slash Command Templates

Create `commands/review-session.md`:

````md
# /review-session

Review the latest explicit or discoverable AI coding session with AIDevObserver.

Use the local CLI when available:

```bash
python3 -m src.teleon.observer.cli review --latest --json
```

Return:

- top findings;
- likely reused component or primitive route;
- estimated context/model waste when available;
- candidate status;
- next action: accept, reuse, dismiss, or open proof path.
````

Create `commands/find-reuse.md`:

````md
# /find-reuse

Before implementing a new helper or workflow, search local repo surfaces and registry primitives for a reusable route.

Look for:

- same input/output contract;
- same package/framework role;
- existing tests or proof evidence;
- known-good workflow templates;
- dismissed negative-memory matches to avoid repeating bad suggestions.

If there is a plausible match, cite the source ref and explain the reuse path.
If there is no match, say what primitive should be created and what proof is needed.
````

Create `commands/refresh-primitives.md`:

````md
# /refresh-primitives

Refresh local source-backed primitive candidates for this repository.

Suggested command:

```bash
python3 _repos/shared-backend-components/scripts/aidevobserver_context_foundry_loop.py --once --local-repo-root . --local-repo-limit 40
```

Expected output:

- candidate primitive drafts;
- source refs;
- contracts;
- fingerprints;
- proof requirements;
- serves_truth=false.
````

Create `commands/review-output.md`:

````md
# /review-output

Review the final generated work before merge or handoff.

Check:

- did the agent recreate a known helper, adapter, workflow, or primitive?
- did it paste or reread avoidable context?
- did it create code that should be a reusable primitive?
- are tests, proof logs, and output contracts present?
- are secrets and local paths absent from public artifacts?
````

## MCP Setup For Claude Code

AIDevObserver already has a stdlib-only MCP server:

```bash
claude mcp add aidevobserver -- python3 _repos/shared-backend-components/scripts/aidevobserver_mcp_server.py
```

Document that in `mcp/aidevobserver.md`:

````md
# AIDevObserver MCP

Purpose:
Expose AIDevObserver review tools to Claude Code through MCP.

Tools:

- `list_sessions`: discover Claude Code sessions for a project cwd.
- `review_session`: post-session reinvention and waste report.
- `live_review`: prospective non-blocking live findings.

Trust:

- read-only;
- candidate findings only;
- serves_truth=false;
- no promotion without proof.

Setup:

```bash
claude mcp add aidevobserver -- python3 _repos/shared-backend-components/scripts/aidevobserver_mcp_server.py
```
````

## Claude Code Hook Setup

AIDevObserver also has a Claude Code PreToolUse hook:

```bash
python3 _repos/shared-backend-components/scripts/aidevobserver_hook.py --install
```

To merge it into `./.claude/settings.json`:

```bash
python3 _repos/shared-backend-components/scripts/aidevobserver_hook.py --install --write
```

The hook is intentionally non-blocking. It prints advisory notes when a pending tool call looks like reinvention, waste, or a cheaper registry route. It should not be framed as command policing.

Document it in `hooks/pretooluse-aidevobserver.md`:

```md
# AIDevObserver PreToolUse Hook

Mode:
Non-blocking advisory.

When it speaks:

- the agent starts recreating a common parser, adapter, workflow, scraper, retry helper, schema extractor, or eval harness;
- the agent is about to read/paste excessive context;
- the agent appears to be missing a cheaper existing registry route.

When it stays quiet:

- normal reads and searches;
- low-confidence matches;
- failures in the observer itself, because hooks fail open.
```

## Setup Modes

Use one or more modes depending on team maturity.

| Mode | Best for | Setup |
| --- | --- | --- |
| Project scaffold | Teams adopting the Claude-style layout | `python3 _repos/shared-backend-components/scripts/aidevobserver_project_scaffold.py --framework python --write` |
| Manual review | First demo, no installation | Paste/upload a transcript in the web app |
| CLI | Developers who prefer terminal review | `python3 -m src.teleon.observer.cli review --latest --json` |
| MCP | Claude Code users | `claude mcp add aidevobserver -- python3 _repos/shared-backend-components/scripts/aidevobserver_mcp_server.py` |
| Hook | Live in-session nudges | `python3 _repos/shared-backend-components/scripts/aidevobserver_hook.py --install --write` |
| Local primitive refresh | Creating source-backed primitive candidates | `python3 _repos/shared-backend-components/scripts/aidevobserver_context_foundry_loop.py --once --local-repo-root . --local-repo-limit 40` |
| Public demo | Sharing a read-only app externally | Serve via the showcase (`OH_PRODUCT=aidevobserver`); front it with an ephemeral tunnel for external sharing only |

The app should explain these as one review surface, not separate products:

```text
One review, wherever your team already works.
```

## Framework Compatibility

AIDevObserver should adapt to the development framework by looking at common files and conventions.

### React / Next.js / Vite

Useful surfaces:

- `package.json` scripts;
- `src/components`, `app/`, `pages/`, `routes/`;
- design-token config;
- Playwright, Vitest, Jest, Storybook, and accessibility checks;
- generated component transcripts.

Likely primitives:

- component quality gate;
- accessibility check;
- design-token compliance;
- route/page scaffold;
- visual snapshot comparison;
- form validation component;
- API client adapter.

### Python / FastAPI / Django / Flask

Useful surfaces:

- `pyproject.toml`;
- `src/`, package modules, routers, schemas, migrations;
- Pydantic models, Django models, serializers;
- pytest fixtures and tests.

Likely primitives:

- request validator;
- policy route;
- database repository;
- schema extractor;
- CSV/JSON parser;
- retry/cache wrapper;
- contract report;
- proof runner.

### Data Engineering

Useful surfaces:

- ingestion scripts;
- schema files;
- SQL models;
- Airflow/Dagster/dbt assets;
- fixtures and data dictionaries.

Likely primitives:

- acquire -> parse -> validate -> normalize -> write artifact;
- schema validation gate;
- column rename;
- type casting;
- quarantine bad rows;
- metadata publish.

### Data Science / Kaggle / Notebooks

Useful surfaces:

- notebooks;
- `kaggle.json` metadata when present;
- training scripts;
- metrics reports;
- feature definitions;
- submission files.

Likely primitives:

- load dataset;
- build baseline features;
- train/evaluate/register;
- leakage check;
- metric gate;
- deterministic split.

### Workflow Automation / n8n / CI

Useful surfaces:

- n8n workflow JSON;
- GitHub Actions;
- Zapier/Make-style exported workflows when available;
- Airflow/Dagster/Temporal workflows;
- CI scripts.

Likely primitives:

- trigger -> fetch -> transform -> gate -> notify;
- idempotency wrapper;
- retry wrapper;
- secret-ref validation;
- receipt logging.

### Media / Image / Audio / Video

Useful surfaces:

- ComfyUI workflow JSON;
- FFmpeg scripts;
- prompt/asset manifests;
- model routing configs;
- QC reports.

Likely primitives:

- image safety gate;
- image describe;
- motion plan;
- image-to-video generation route;
- temporal stabilization;
- encode/transcode;
- media QC gate.

## Privacy And Launch Rules

For public demos and external feedback:

- do not publish raw Claude/Codex transcripts;
- do not publish absolute local paths;
- do not publish local evidence snippets;
- use content digests and repo-relative source refs;
- keep findings and primitive drafts candidate-only;
- default to `serves_truth=false`;
- make hooks non-blocking and read-only;
- serve the app via the showcase; use an ephemeral tunnel only when sharing it externally.

For private team use:

- local path inclusion can be enabled only when the team explicitly accepts it;
- raw transcripts should stay local unless uploaded intentionally;
- accepted findings become team memory;
- dismissed findings become negative memory.

## What To Show In The Product

The setup page should not make users understand Teleon internals first. It should say:

```text
Install AIDevObserver where your AI coding work happens:

- paste/upload a session;
- review latest Claude Code session from the CLI;
- add the MCP server for Claude Code;
- add the PreToolUse hook for non-blocking live reuse hints;
- refresh local primitive candidates from your repo.
```

Then show technical drill-down:

```text
OpenHubForAI stores reusable components.
Teleon compiles trusted routes.
Baltor governs verified context.
AIDevObserver reviews sessions and points agents back to what the primitive database already knows.
```

## Launch Checklist For A Claude-Style Project

1. Scaffold or manually add the Claude-style project pack:

```bash
python3 _repos/shared-backend-components/scripts/aidevobserver_project_scaffold.py --framework python --write
```

2. Confirm the `CLAUDE.md` AIDevObserver section matches the project.
3. Confirm `/review-session`, `/find-reuse`, `/refresh-primitives`, and `/review-output` command docs exist.
4. Add `mcp/aidevobserver.md` with the MCP setup command.
5. Add `hooks/pretooluse-aidevobserver.md` and install the hook if live advice is desired.
6. Run a local primitive refresh:

```bash
python3 _repos/shared-backend-components/scripts/aidevobserver_context_foundry_loop.py --once --local-repo-root . --local-repo-limit 40
```

7. Run focused proofs:

```bash
python3 _repos/shared-backend-components/scripts/aidevobserver_project_scaffold.py --self-test
python3 _repos/shared-backend-components/scripts/check_aidevobserver_local_registry_connector.py --self-test
python3 _repos/shared-backend-components/scripts/aidevobserver_context_foundry_loop.py --self-test
python3 _repos/shared-backend-components/scripts/check_observer_review.py --self-test
```

8. Share the review/demo app only through a current ephemeral tunnel (the app itself is served by the showcase; a tunnel host is transient).
