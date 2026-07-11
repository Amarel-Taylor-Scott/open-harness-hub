# Baltor full-app — quickstart

**Baltor is a governed Context Engine.** Any agent asks for context; Baltor returns the smallest
safe, source-linked, policy-compliant **context pack** for the task — with evidence, relationships,
history, lineage, and a portable **receipt** — instead of a raw source dump. This page is the
1-minute tour of the working demo and how it's proven.

## See it work (1 command, free/local, offline)

```bash
cd _repos/baltor/frontend && python3 -m http.server 8000
# open http://localhost:8000/demo-console.html   (pick a corpus, hit ▶ Run)
# open http://localhost:8000/reviews.html          (the human review queue)
```

Serve over HTTP (browsers block `file://` fetch). It's a **deterministic replay of a real run** —
not a mock. Two synthetic corpora: **Acme Billing** (retry ceiling 5 vs a stale runbook's 3) and
**CFPB sample** (Reg E's 10 business days vs a stale FAQ's 30). Click a graph node for object detail,
claims, version timeline, and a policy-gated source expansion. Full guide:
[`docs/deployment/demo-console.md`](deployment/demo-console.md).

## What runs (the engines, all composed by the demo)

| Stage | Module | What it does |
|---|---|---|
| Interrogate the graph | `scripts/context_graph.py` | traverse, find contradictions, pick the authority (never averages), cite `ctx://` |
| Compress (deterministic, non-LLM) | `scripts/context_compress.py` | token budget → boilerplate → near-dup collapse → keyphrases → rank → extractive; handles preserved |
| Lineage + raw expansion | `scripts/source_expansion.py` + `schemas/context/{source-locator,lineage-manifest}` | digest up front; raw expansion only through a fail-closed policy gate |
| Swarm-verify an object | `scripts/context_swarm.py` | bounded agents → routes a steward review; PROPOSES (never applies) a fix |
| Measured lift (with/without context, with/without harness, × models) | `scripts/eval/context_lift_matrix.py` | extends the paired separate-judge protocol; raw dump *underperforms* the governed pack |
| Unify + export | `scripts/demo_full_app.py`, `scripts/demo_run_export.py` | run records + review queue + version timeline (drift-checked) |

Model use is a **seam**: deterministic by default; a local/free `model_gateway` route only *phrases*
answers, never changes facts.

## Keep improving it (the loop)

`/baltor-full-app-goal` is the long-running build loop (`.claude/commands/baltor-full-app-goal.md`):
ORIENT → AUDIT → RESEARCH/VERIFY → DESIGN → IMPLEMENT → WIRE → PROVE → RECORD → REPEAT, one batch of
proven increments per firing. It **extends** existing anchors (model routing, lift harness, review
schemas) rather than duplicating them.

## Prove it

```bash
python3 scripts/baltor_flywheel.py --once       # the always-on watchdog: every proof module's self-test
python3 scripts/ci_check.py                      # the CI gate: full proof suite + dashboard drift-check
python3 scripts/check_prelaunch.py               # read-only private→public readiness report
```

Every shipped module carries a deterministic offline `--self-test` registered in
`baltor_flywheel.PROOF_MODULES` (the single source); CI (`.github/workflows/baltor-proofs.yml`) gates
PRs on the same suite. Discipline: proof-per-increment, real-or-labeled-SEAM, no-magic-values,
verify-first, no canonical mutation. Synthetic data only.
