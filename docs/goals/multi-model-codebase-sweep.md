# GOAL — Multi-model codebase improvement sweep (Claude + Kimi + GLM-5.2)

Long-running loop. Sweep EVERY ASPECT of the platform — planes, wedges, cross-cutting ARCHITECTURE (monolith-avoidance,
thin base classes that get extended, hierarchies, taxonomy, flexibility, abstractions), business/PMF, design,
presentations, demos, integrations, and every code module (its functions/classes/constants) — with Kimi-2.7 + GLM-5.2,
accumulate improvement opportunities, apply the safe ones, and **defer to Kimi + GLM when Claude is stuck.** Tool:
`scripts/multi_model_improvement_loop.py` (~409 targets; resumable via a cursor → runs for hours).

## Per cycle
1. **Sweep a batch:** `PYTHONPATH=. python3 scripts/multi_model_improvement_loop.py --run --limit 8`
   (reviews the next 8 unreviewed targets with Kimi + GLM-5.2; records to `data/improvement-opportunities/findings.jsonl`).
2. **Triage the new findings** (governed candidates, serves_truth=false): keep only those that are (a) concrete, (b)
   corroborated (both models, or Claude verifies against the code), (c) within an existing repo law. Discard generic/
   hallucinated ones (cross-check GLM vs Kimi; verify the cited symbol exists).
3. **Apply the safe, high-leverage improvements** — one proof-backed increment at a time, each with a `--self-test`,
   keeping the regression sweep + dependency law + family green. Lossless; archive-not-delete; no untracking.
4. **When stuck**, defer: `python3 scripts/multi_model_improvement_loop.py --ask "<the blocker>" [--context-file F]`
   → Kimi + GLM insights + next steps. Record the resolution; never paste their output as truth (candidate until verified).
5. Repeat until the cursor reports the sweep complete OR `.agent/STOP_REQUESTED` exists.

## Rules
- **Decide autonomously; minimal stops.** One loop at a time. Anti-slop; no filler.
- **Governance:** findings + model output are CANDIDATES (serves_truth=false) until Claude verifies against the code.
  Match the change-verification, lossless, and no-magic-values laws (CLAUDE.md).
- **Cost:** the sweep runs on the near-zero-cost Ollama lane; `--limit` bounds each cycle. The cursor makes it resumable.
- **Reset** a full re-sweep by deleting `data/improvement-opportunities/_cursor.json`.

## Definition of done (per pass)
- [ ] Every plane + wedge + module reviewed at least once (cursor complete).
- [ ] The high-confidence opportunities applied (or ticketed) with proofs green.
- [ ] A short status note in `docs/status/` summarizing what was found + fixed + deferred.
