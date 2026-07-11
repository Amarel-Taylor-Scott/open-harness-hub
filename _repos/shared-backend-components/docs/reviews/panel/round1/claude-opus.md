# Panel round 1 - claude-opus seat

> serves_truth=false. A board member's opinion is a governed candidate, not asserted truth. File-citing, no flattery.

## CEO lens
**Strengths:** (1) A genuinely coherent thesis - a "systems layer for executable capability" with four reconciled
filters (`architecture/substrate_layers.json` -> `foundational_law`), not a feature pile. (2) The portfolio is
structurally honest: Baltor -> Teleon -> OpenHubForAI is a real dependency law, enforced in code
(`scripts/check_portfolio_dependency_law.py`), so the narrative maps to the architecture.
**Risks:** (1) Brand sprawl - five display surfaces (AI Done Right, Teleon, Baltor, OpenHubForAI, AIDevObserver)
for what is, in revenue terms, zero proven verticals; the buyer narrative is split across too many nouns. (2) The
single existential risk is unaddressed in-repo: there is no evidence of a paying customer. The whole edifice is
"what must be true" infrastructure ahead of demand.
**Recommendation:** Lead externally with ONE surface (AIDevObserver is the cleanest adoption wedge - it is real,
read-only, and useful day one; `_repos/teleon/backend/src/teleon/observer/`); treat the rest as the engine behind it.

## COO lens
**Strengths:** (1) Exceptional process discipline: every module self-tests, one gate runs them all
(`scripts/run_proofs.py`, 717 green), and changes carry a warrant (`docs/codex/change-verification-contract.md`).
(2) Lossless/move-not-delete + the design-bundle->web port contract mean the repo rarely loses work or drifts.
**Risks:** (1) Green proofs prove the code RUNS, not that anything SHIPS to a user - much of the surface is
verified-rendering scaffolding, not deployed product. (2) Throughput bottleneck: one team maintaining a runtime,
a store of ~240 registries, five surfaces, a service plane, and a review board is breadth no small team sustains.
**Recommendation:** Add a "real usage" signal to the gate's spirit - e.g. a deployed `/demo` with telemetry -
so "done" means "a human used it," not "the self-test passed."

## CTO lens
**Strengths:** (1) Sound seams: registry federation behind one interface, capability descent ladders
(`architecture/capability_ladders.json`, deterministic-first), uniform component `invoke`. (2) The change-impact
tooling is better than most shops (`scripts/codegraph.py --audit`).
**Risks:** (1) Onramp complexity: the showcase + shared-kit + design-bundle + port pipeline is intricate; a new
contributor's path from edit to verified surface is steep and easy to get wrong (the recurring "skinny replacement
server" failure mode is evidence). (2) Build-vs-buy: a multi-model review board, a context-pack system, and a
registry federation are all being built - some are buyable; the reinvention guard should be pointed inward too.
**Recommendation:** Write a one-page "edit a surface" runbook keyed to `docs/INTEGRATION-BIBLE.md` +
`port_full_design_to_web.py` so the intricate-but-correct path is the obvious one.

## CFO lens
**Strengths:** (1) The cost-descent thesis IS the margin story and it is architectural, not aspirational
(make-it-work -> make-it-cheap -> deterministic substitution). (2) Local-first defaults (local Ollama embeddings,
keyless lanes) keep dev burn near zero.
**Risks:** (1) The margin thesis is unmeasured: there is no in-repo unit-economics ledger showing the descent
actually lands as $/task saved. (2) Live LLM spend is real and uncapped by design now (this very panel runs
Kimi-2.7 + GLM-5.2 on the owner key, full context, no token cap) - powerful, but needs a budget guard before it
runs in any loop.
**Recommendation:** Add a cost-to-serve receipt per capability run (extend the evidence ledger) so the
descent's margin shows up as a number, not a claim.

## YC lens
**Strengths:** (1) Real "why now": agents are proliferating and nobody verifies/receipts/governs truth - the
governed-context wedge is timely. (2) AIDevObserver is a "make something people want" shaped product with a
near-zero-friction adoption path (MCP server, editor extension, CLI, hook).
**Risks:** (1) It reads closer to a research platform than a startup: enormous surface, no user, no revenue. (2)
Default-alive is unknown - there is no signal of users or money in the repo.
**Recommendation:** Ship AIDevObserver to 10 real teams this month and instrument accept/dismiss; let that signal,
not the architecture, drive the roadmap.

TOP PRIORITY: Enforce the repo's OWN foundational law #4 (DEPTH BEFORE BREADTH, gated by
`scripts/proposal_backlog.py`): pick ONE vertical and ONE paying (or actively-using) customer, and gate every new
surface/registry/layer behind serving them. The architecture is ahead of demand; the highest-leverage move is to
stop widening and prove one narrow thing with a real user.
