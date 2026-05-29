---
description: Polish the Open Harness Hub product app end-to-end — every screen, funnel, gate, endpoint — and make every surface sell its value proposition. Runnable autonomous loop.
---

Run the **app-polish loop**: read and follow `docs/codex/app-polish-loop.md` against the
live product front-end in `web/` (served by `scripts/serve_showcase.sh`; the real backend is
`scripts/showcase/server.py` `/api/*`).

Operate under the **no-stop contract** (same as `.claude/commands/goal.md`): there is no
terminal state — "screen polished" → next screen; "blocked/red" → roll back to green, switch
paths, keep going. **Decide autonomously and never ask** — pick the most defensible option,
record it in `.research-notes/autonomous-session-ledger.md`, proceed.

Every pass must:
1. Pick the **weakest surface** (screen, funnel, gate, or endpoint) by the rubric in the loop doc.
2. Make it sell its value: lead with **measured lift**, **governance/provenance**, and
   **freezable = no recurring cost** — the canonical props in `docs/design/value-propositions.md`.
3. Verify: `node --check` every touched file, walk the funnel end-to-end, confirm the live
   `dist/showcase-share-url.txt` still serves it. Keep `web/` no-build (vanilla, ported CSS only).
4. Loop. Log what you polished and what's next.

$ARGUMENTS
