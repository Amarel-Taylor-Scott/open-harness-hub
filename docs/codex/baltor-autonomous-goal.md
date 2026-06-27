# Baltor Autonomous Goal

This is the canonical `/goal` objective for long-running autonomous work.

## Objective

Polish Baltor into a credible local-first and cloud-ready context-control
platform: load enterprise context, process it through cheap-to-expensive worker
lanes, verify/reconcile it, package it for text/RAG/graph/hybrid serving, and
make the business story fundable.

Do not stop at proposals. Implement durable repo changes, validate them, record
the result, then continue to the next highest-value unblocked item.

## Read First

1. `docs/codex/baltor-clean-context.md`
2. `docs/codex/baltor-autonomous-goal.md`
3. `docs/architecture/baltor-codebase-cleanup-plan.md`
4. `docs/architecture/baltor-model-and-document-pipeline.md`
5. `docs/architecture/baltor-stateless-worker-standard.md`
6. `docs/architecture/baltor-queue-priority-orchestration.md`
7. `docs/architecture/baltor-source-trust-and-adoption-policy.md`
8. `docs/strategy/baltor-gtm-fundraising-plan.md`
9. `docs/codex/no-magic-values.md`
10. `AGENTS.md` and `CLAUDE.md`

Older goal docs remain useful for substrate detail, but this document wins when
strategy conflicts.

## Loop

Repeat until interrupted:

```text
ORIENT   Read the clean context, ledger, git status, and changed files.
PLAN     Pick exactly one high-value, unblocked improvement.
BUILD    Make the repo change.
VALIDATE Run the narrowest meaningful checks.
RECORD   Append a session-ledger entry with files, tests, and next action.
BRANCH   If blocked, switch to another path without asking.
REPEAT
```

## Priority Order

1. Split monoliths that block product velocity.
2. Make the admin demo more credible and easier to understand.
3. Add real serving/export artifacts and APIs.
4. Improve source sync, versioning, provenance, and diff handling.
5. Improve context workers and model hierarchy.
6. Improve local-first setup for Gemma/Ollama and hosted OpenAI-compatible APIs.
7. Standardize stateless K8 worker envelopes and reusable worker images.
8. Add multi-source fact adoption, source trust scoring, injection defense, and
   archive queueing.
9. Add state-driven priority rules for research, verification, refresh,
   archive, and rare review tasks.
10. Add cloud deployment manifests only when local parity exists.
11. Improve GTM, design-partner, customer-acquisition, and fundraising material.
12. Clean stale docs by pointing them to the canonical context rather than
   duplicating strategy.

## Validation Menu

Use the smallest sufficient set:

```bash
node --check web/openhubforai/admin-demo.js
node --check web/openhubforai/admin-demo-assets/app.js
node --check web/openhubforai/admin-demo-assets/renderers.js
python3 -m py_compile scripts/showcase/server.py
python3 -m py_compile scripts/context_workers/*.py
python3 -m scripts.context_workers.runner --validate-manifest
python3 -m scripts.context_workers.runner --validate-research-tasks tasks.json
python3 -m scripts.context_workers.runner --self-test
.venv/bin/python -m mkdocs build
```

For changed catalog components, also run the catalog-specific validation from
`AGENTS.md`.

## Long-Run Rules

- Do not ask the user to choose among reasonable implementation paths.
- Do not stop because one provider, cloud, model, or scraper is unavailable.
- Keep all model calls optional and provider-neutral.
- Keep manual human confirmation rare and exceptional.
- Avoid making product claims that the repo cannot demo or measure.
- Do not delete broad legacy docs unless the user explicitly asks; add canonical
  supersession notes instead.
