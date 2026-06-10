# Baltor Perpetual Parallel Improvement Runbook

Use this runbook with:

```text
.codex/prompts/baltor-perpetual-parallel-improvement-goal.md
```

The intent is continuous improvement without artificial stop conditions. The
work should proceed through parallel threads with disjoint ownership and regular
integration.

## Startup Checklist

```text
1. Read .codex/prompts/baltor-perpetual-parallel-improvement-goal.md.
2. Read docs/codex/baltor-database-backed-context-current-state.md.
3. Check git status for changed files.
4. Check existing subagent outputs before spawning duplicate work.
5. Start 3-6 independent agents with disjoint write scopes.
6. Work locally on the critical path while agents run.
```

## First Wave

Start these agents:

```text
A. database bridge / import-export
B. object governance seed packages
C. archive candidate ledger
D. hard-coded settings registry
E. validation gates
F. admin demo visibility
```

## Standard Commands

Use targeted commands first:

```bash
python3 -m py_compile scripts/audit_context_storage.py
python3 scripts/audit_context_storage.py --markdown --rotted-only
python3 scripts/audit_context_storage.py --archive-ledger
python3 scripts/validate.py catalog/rubrics/baltor-business-object-governance-quality.yaml
python3 scripts/db/catalog_manifest_bridge.py --self-test
```

Use full validation when catalog manifests or global schema behavior changes:

```bash
python3 scripts/validate.py
```

## Integration Rules

```text
Do not wait for every agent before making local progress.
Do not duplicate an agent's assigned work locally.
When an agent completes, inspect changed files and commands run.
Integrate non-conflicting work.
If two agents touch the same file, preserve both intentions manually.
Record decisions in current-state docs.
```

## Current Active Workstreams

```text
database-backed catalog bridge
rotted-context archive readiness
hard-coded settings registry
business/database object governance packages
validation drift gates
admin demo visibility
```

## Completion Standard

This goal is not complete after one patch. It is complete only when the user
explicitly ends it or when a separate release goal defines a bounded milestone.

