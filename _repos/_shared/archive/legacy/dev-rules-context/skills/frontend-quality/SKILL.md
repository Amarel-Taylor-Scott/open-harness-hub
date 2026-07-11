# Frontend Quality

Purpose:
Help the agent reuse existing helpers, templates, workflows, and primitive routes before creating new code.

Use when:
- a new helper, adapter, parser, workflow, component, data pipeline, or eval harness is requested;
- the agent appears to be rebuilding a common capability;
- a proof or quality gate should exist before handoff.

Required behavior:
1. Search local repo and registry surfaces first.
2. Prefer an existing primitive or route when confidence is high.
3. If no route exists, describe the primitive candidate and required proof.
4. Treat findings as candidate advice, not automatic truth.
