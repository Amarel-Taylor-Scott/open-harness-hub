# AIDevObserver Launch Readiness And Alpha Plan

**Date:** 2026-06-28  
**Status:** candidate planning artifact  
**Truth boundary:** `serves_truth=false`; proof, promotion, and production launch remain separate gates.

## Current Read

AIDevObserver is **demo-ready / alpha-grade**, not public-launch-ready.

The strongest wedge is now clear:

```text
AIDevObserver reviews AI coding sessions and routes agents toward code,
workflows, templates, media pipelines, data-science patterns, and generated
components the primitive database already knows.
```

This is a speed, reuse, and token-savings product first. Safety signals remain
useful for managers, but they should not be the lead adoption story.

## What Is Working

The current repo has real, test-covered pieces:

| Area | Current State | Evidence |
| --- | --- | --- |
| Review engine | Post-session reviewer over the observer router | `python3 _repos/shared-backend-components/scripts/check_observer_review.py --self-test` |
| Replay examples | Synthetic AIDevObserver examples and upload/download files | `python3 _repos/shared-backend-components/scripts/check_aidevobserver_example_sessions.py --self-test` |
| Project scaffold | Claude-compatible `CLAUDE.md` / skills / commands / hooks / MCP setup pack | `python3 _repos/shared-backend-components/scripts/aidevobserver_project_scaffold.py --self-test` |
| MCP integration | Claude Code MCP server plus CLI bridge | `python3 _repos/shared-backend-components/scripts/check_aidevobserver_mcp.py --self-test` |
| Editor path | VS Code extension scaffold with review command/config | `python3 _repos/shared-backend-components/scripts/check_aidevobserver_vscode_ext.py --self-test` |
| Local service | HTTP service over the existing observer engine | `python3 _repos/shared-backend-components/scripts/check_observer_local_service.py --self-test` |
| Live coaching | Claude Code PreToolUse hook, non-blocking and read-only | `python3 _repos/shared-backend-components/scripts/aidevobserver_hook.py --self-test` |
| Outcome memory | Append-only Accept / Reuse / Dismiss metadata, no transcript text | `python3 _repos/shared-backend-components/scripts/check_observer_capture_store.py --self-test` and `python3 _repos/shared-backend-components/scripts/check_observer_local_service.py --self-test` |
| Local registry connector seed | Repo-relative symbol, docs, and script candidate source refs, plus opt-in review enrichment | `python3 _repos/shared-backend-components/scripts/check_aidevobserver_local_registry_connector.py --self-test` and `python3 _repos/shared-backend-components/scripts/check_observer_local_service.py --self-test` |
| Benchmark seed | Kaggle-style synthetic public-project session fixtures with source-ref coverage/top-1/top-3 metrics | `python3 _repos/shared-backend-components/scripts/check_aidevobserver_session_benchmark.py --self-test` |
| Context foundry | Candidate source records, session specs, primitive drafts | `python3 _repos/shared-backend-components/scripts/aidevobserver_context_foundry_loop.py --self-test` |
| Public demo UI | Review page supports paste/upload, replay picker, and setup paths | visual check on the showcase-served app (or an active ephemeral tunnel) |

The Review page now explains the first-use path better:

```text
paste or upload
choose replay
review session
then connect the same review to editor, MCP, CLI, hook, or discovery paths
```

## Launch Phase Gates

### 1. Demo-Ready

**Status:** mostly ready.

Required gates:

- Review page loads from a public demo URL.
- Manual paste/upload is visible and understandable.
- Replay examples are available without private data.
- Findings remain candidate-only.
- The observer review and example-session checks pass.
- No user-facing loopback URL is presented.

Current risk:

- `trycloudflare.com` tunnels are temporary. They are acceptable for demos but
  not as a launch deployment.

### 2. Private Alpha

**Status:** not ready.

Private alpha should require:

- one install path packaged end to end, preferably scaffold + MCP or CLI first;
- setup docs that a technical user can follow without repo archaeology;
- persistent Accept / Reuse / Dismiss outcomes;
- minimum viable registry connector over local repo helpers, docs, scripts, and
  template records;
- source-backed primitive candidates or opportunity rows, never trusted
  synthetic-only primitive records;
- privacy/redaction policy for transcript handling;
- first benchmark pack passing with source-ref expectations;
- known false-positive traps and clean-session controls.

The first alpha should not require all surfaces to be equally mature. It should
make one path excellent, then expand.

Current partial progress:

- the observer local service exposes metadata-only `/outcome` and `/outcomes`;
- the Review UI sends outcome metadata and structured source refs when a finding
  has server-stamped ids; the backend stores hashed source-ref memory keys, not
  raw transcript text;
- session-store and local-service proofs cover append-only latest-wins behavior
  plus accepted/reused boost and dismissed/ignored suppression for future local
  registry hits.
- the local registry connector indexes repo-relative Python symbols, constants,
  docs snippets, package/pyproject scripts, and Claude-style project surfaces as
  candidate-only source refs;
- the project scaffold can generate `CLAUDE.md`, command docs, skill docs, hook
  docs, MCP docs, and session-memory docs, then prove those surfaces index into
  structured primitive candidates;
- `/review` can now attach those local source refs to findings when the caller
  provides `registry_cwd` and explicitly opts in to local registry search; the
  attached refs carry outcome-memory score hints when prior triage exists.
- the first Kaggle-style session benchmark reports source-ref coverage plus
  top-1/top-3 source-ref accuracy for the expected primitive routes.

Recommended first alpha path:

```text
manual upload / replay examples
  -> project scaffold
  -> CLI review
  -> Claude Code MCP server
  -> live hook
  -> editor extension
```

### 3. Public / Commercial Launch

**Status:** not ready.

Public launch needs:

- stable domain and deployed static app;
- deployed/proxied observer backend with health checks and rollback;
- auth, workspace, team, billing, and persistence wired for real use;
- packaged extension or signed/sideloadable distribution;
- benchmark metrics published with estimate basis;
- source-ref precision targets met;
- privacy/legal/terms review;
- support and onboarding docs;
- clear registry connector setup for internal code, generated primitives, and
  OpenHubForAI surfaces.

## Minimum Alpha Product

The minimum useful private alpha is:

```text
session transcript
  -> deterministic extraction of actions/files/code blocks/commands
  -> local repo/helper/template search
  -> optional LLM ranking or summary
  -> ranked candidate findings
  -> human Accept / Reuse / Dismiss
  -> hashed source-ref memory
  -> reuse boosts and negative-memory suppression
```

Teleon route mode can remain advanced:

```text
accepted finding
  -> primitive/template search
  -> CandidateBundle
  -> compact PlanDelta or deterministic route
  -> compiler/proof path
```

Do not require first users to understand CandidateBundle, PlanDelta, PlanLock,
or promotion before they understand the reuse report.

## Required Metrics

Launch credibility depends on measured reuse, not claims.

Track:

- finding precision by category;
- top-1 and top-3 source-ref accuracy;
- accepted reuse rate;
- outcome-memory ranking effect;
- dismissed/wrong-match rate;
- clean-session false positive rate;
- prompt tokens avoided, with estimate basis;
- model calls avoided;
- review latency;
- redaction success;
- registry hit coverage by source family.

Token estimates must declare their basis:

```text
exact_model_log_tokens
tokenizer_estimate_from_transcript
deterministic_proxy_from_recreated_helper_count
```

## Required User-Facing Setup Paths

The app should explain all paths, but launch should prove one path deeply.

| Surface | Launch Role |
| --- | --- |
| Manual upload / paste | Zero-install fallback and demo path |
| Replay examples | Public demo and sales/support path |
| Claude project scaffold | Fastest way to create `CLAUDE.md`, skills, commands, hooks, and MCP setup docs |
| CLI | Fastest real technical alpha path |
| Claude Code MCP | Best agent-native path |
| Live PreToolUse hook | Optional non-blocking coaching |
| VS Code / Cursor extension | Productized editor path after CLI/MCP proof |
| Local session discovery | Power-user path; privacy-sensitive, opt-in |

## Registry Connector Requirement

The product becomes differentiated when findings point to exact existing
components:

```text
The agent wrote parse_csv().
Existing route: utils.csv.read_rows or registry.csv.read_rows
Evidence: same input/output shape, same delimiter/header behavior, proof passing
```

Minimum connector coverage:

- repo symbol/function/class search; seeded by
  `_repos/teleon/backend/src/teleon/observer/local_registry_connector.py`;
- docs/README snippets; seeded by the local connector;
- Claude-style `CLAUDE.md`, `skills/*/SKILL.md`, `commands/*.md`, `hooks/*.md`,
  and `mcp/*.md` surfaces; seeded by the local connector and project scaffold;
- _repos/shared-backend-components/scripts/package commands; seeded by the local connector;
- review-time source-ref enrichment; seeded behind the opt-in local registry
  flag in `_repos/shared-backend-components/scripts/observer_local_service.py`;
- accepted/reused and dismissed/ignored outcome memory influencing future
  local source-ref ranking;
- source-backed primitive opportunity and primitive draft records;
- example sessions and fixtures;
- primitive draft registry;
- workflow/template records;
- accepted finding memory;
- dismissed finding negative memory.

## Privacy And Candidate-Only Rules

Hard rules:

- no raw private transcript text in public examples;
- no raw local filesystem paths in public examples;
- no secrets or PII in fixtures;
- public demos hide local session paths;
- local discovery is opt-in;
- findings default to `candidate=true` and `serves_truth=false`;
- accepted findings become evidence, not served truth.

## Immediate Next Steps

1. Package a single end-to-end install path, starting with project scaffold + CLI or Claude Code MCP.
2. Harden persistent triage memory across reloads and workspace boundaries.
3. Extend the local registry connector from symbol/doc/script matching into
   primitive drafts, examples, workflows, accepted memory, and dismissed
   negative memory.
4. Split generated capability rows into source-backed `primitive_draft` and
   unsourced `primitive_opportunity` records.
5. Expand the session-review benchmark beyond the initial Kaggle-style cases
   while preserving source-ref coverage and top-k accuracy thresholds.
6. Extend accepted/dismissed outcome memory beyond the local registry slice into
   OpenHubForAI/Teleon candidate ranking and benchmark reporting.
7. Make setup docs copy-paste-safe for a fresh user and keep
   `_repos/shared-backend-components/scripts/aidevobserver_project_scaffold.py --self-test` green.
8. Move public demos from transient tunnels to a stable deployment path.

## Proof Contract

The machine-readable launch contract lives at:

```text
_repos/shared-backend-components/architecture/aidevobserver_launch_readiness_contract.json
```

The proof checker lives at:

```text
_repos/shared-backend-components/scripts/check_aidevobserver_launch_readiness.py
```

This document and contract are launch planning artifacts only. They do not mark
AIDevObserver as production-ready.
