# /goal: Improve Baltor Context Control For Hours

You are an autonomous Codex agent working in this repository. Run for hours on
the Baltor admin demo and context-control worker system. Do not stop at
planning. Implement, validate, record, and continue until the human interrupts
you or a real safety/destructive-action blocker prevents progress.

## Read First

1. `AGENTS.md`
2. `README.md`
3. `taxonomy/SPEC.md`
4. `docs/codex/no-magic-values.md`
5. `docs/codex/baltor-context-control-current-state.md`
6. `docs/codex/baltor-context-control-iteration-plan.md`
7. `docs/codex/baltor-context-control-test-plan.md`
8. `docs/codex/baltor-context-control-session-ledger.md`
9. `docs/architecture/document-intelligence-pipeline.md`
10. `docs/architecture/llm-trust-layer.md`
11. `docs/architecture/node-research-and-verification.md`
12. `docs/architecture/baltor-stateless-worker-standard.md`
13. `docs/architecture/baltor-queue-priority-orchestration.md`
14. `docs/architecture/baltor-model-and-document-pipeline.md`
15. `docs/architecture/baltor-mcp-context-gateway.md`
16. `docs/architecture/baltor-context-layer-mvp-roadmap.md`
17. `docs/research/enterprise-context-database-phases.md`
18. `docs/architecture/baltor-event-driven-context-sync.md`
19. `docs/architecture/baltor-context-object-standards.md`
20. `docs/architecture/baltor-context-object-graph-profile.md`
21. `docs/architecture/baltor-context-fabric-product-blueprint.md`
22. `docs/architecture/baltor-model-routing-ladder.md`
23. `docs/architecture/baltor-reranking-and-lora-rerankers.md`
24. `docs/architecture/baltor-local-encrypted-memory-sync.md`
25. `docs/architecture/baltor-complete-system-brief.md`
26. `docs/architecture/baltor-product-market-fit-and-wedge-strategy.md`

## Mission

Make the Baltor context-control demo fully credible:

- upload/connect sources;
- process ZIPs and document sets into hierarchy, pages, components, chunks,
  entities, claims, and graph candidates;
- run deterministic workers before LLMs;
- use Redis/pubsub-style queues and structured JSON logs;
- run local CPU Gemma/Ollama LLM trust workers by default;
- surface every action in `/admin-dashboard/monitor`;
- export manifest, text, RAG, graph, audit, safe-context, and context-pack
  packages;
- expose a controlled local context gateway with bounded search/fetch/status
  APIs and `ctx://baltor/...` handles;
- expose debug heartbeats, connector envelopes, and traceable source handles so
  local and cloud proofs can verify every runtime layer is actually alive;
- keep local deployment and cloud deployment paths aligned.

## Loop

```text
ORIENT   Read current state, changed files, running services, and ledger.
VERIFY   Hit local routes/APIs and inspect worker logs before editing.
BUILD    Make one durable improvement that removes a real gap.
TEST     Use HTTP checks, Python proof scripts, Playwright/Chromium if present,
         Redis/worker logs, export validation, and py_compile.
RECORD   Append to docs/codex/baltor-context-control-session-ledger.md.
REPEAT   Continue to the next highest-value issue without asking.
```

## Priority Order

1. No blank pages. Every six-card route must be clickable and useful.
2. Upload and ZIP ingestion must work and show hierarchy metadata.
3. Redis queue handoff and worker processing must be observable.
4. Local adapter mode must have zero missing/not-configured adapters.
5. Local Gemma/Ollama LLM workers must execute when the local model is present.
6. LLM outputs must remain proposals or reviews until evidence policy promotes
   them.
7. Monitor and run APIs must expose worker records, queue state, LLM status,
   errors, exports, and latest events.
8. Context gateway APIs must expose status, search, fetch, trace, connector
   catalog, and heartbeat contracts.
9. Export packages must be contract-specific and valid JSON.
10. Add tests after each improvement.
11. Keep documentation current as implementation changes.

## Rules

- Do not delete local files unless explicitly asked.
- Do not use git tracked/untracked status as permission to discard local work.
- Do not commit PII, credentials, secrets, or private customer data.
- Do not run external person-level OSINT by default.
- Do not require human approval for local read-only LLM review within policy.
- Do not leave the local happy path unconfigured.
- Prefer additive improvements and focused refactors.
- If Playwright is unavailable, use HTTP and Chromium-compatible checks rather
  than stopping.

## Closeout

A closeout must include:

- local URL and tunnel URL if available;
- tested run ID;
- routes tested;
- upload type tested;
- queue state;
- worker/LLM status;
- export status;
- files changed;
- tests run;
- next recommended action.
