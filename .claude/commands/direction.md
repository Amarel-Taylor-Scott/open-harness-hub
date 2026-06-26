---
description: Resilient operating loop for OpenHubForAI — never stop early, branch on every block
---

Load the resilience engine and apply it to the current autonomous run. Read and
follow `.codex/prompts/direction.md` (paired with `.codex/prompts/goal.md` and
`docs/codex/master-goal.md`).

Operate under the **no-stop contract**: there is no terminal state. "Task done"
→ next menu item. "Phase complete" → next phase. "Blocked / error / red
validation" → roll back to green, switch paths, keep going. "Waiting on
something external" → do other work now, check back later. **Decide
autonomously and never ask me questions** — pick the most defensible option,
record the assumption in `.research-notes/autonomous-session-ledger.md`, and
proceed. Safety gates (no PII, no `_reference` republish, no faked embeddings,
promotion boundary, validate-before-commit) are honored by doing the safe thing
and continuing — never by stopping.

$ARGUMENTS
