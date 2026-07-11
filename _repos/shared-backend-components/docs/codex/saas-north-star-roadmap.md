# SaaS North-Star Roadmap — from local-complete to first revenue

> **Warrant:** owner intent 2026-07-06 — "Lets continue to go towards a north star SaaS system that is
> sellable and actually produces value, has a roadmap, is flexible ... We can get everything working
> locally, and then I can give you credentials, keys, and MCP to setup all of the hosting infrastructure."
> This doc is the ROADMAP layer only. The launch gates live in
> `architecture/aidevobserver_launch_readiness_contract.json` (checked by
> `scripts/check_aidevobserver_launch_readiness.py`); deploy shape lives in
> `architecture/deploy_topology.json` + `scripts/deploy/preflight.py`; product identity lives in the PMF
> docs. If this doc disagrees with a contract, the contract wins.

## The north star (one sentence)

Developers use their LLM tools, harnesses, agents, and loops exactly as they do today; repeatable code is
produced by **composing verified primitives** — the LLM outputs only ordering/integration relationships in
the corpus's standardized edge language, a **deterministic builder** wires and executes the graph with zero
model tokens, and the product charges for the governed registry + the measured token savings.

## What "sellable" requires that "working" does not

A deployed endpoint a stranger can reach · an install path under 10 minutes · telemetry from someone
ELSE's sessions · a price on an invoice. Everything else is supporting evidence.

## Phases (each exits on a RECEIPT, never a claim)

### Phase 0 — LOCAL-COMPLETE (current phase; near-exit)
Everything a developer needs runs from one checkout with no cloud dependency.
- **Exit receipts:**
  - one-command onboarding: `python3 scripts/quickstart_aidevobserver.py --write` → receipt `ok:true`
    with outside-in MCP handshakes, service probe, hook check (**green 2026-07-06**, 0.3s on a warm
    checkout)
  - launch-readiness contract fully green (**green 2026-07-06**, all sub-proofs bare)
  - deploy preflight **GO** (**green 2026-07-06**)
  - proof umbrella green (`scripts/run_proofs.py` — the count is COMPUTED; never hand-type it)
  - real-token receipts exist on the live model lane (**first landed 2026-07-06**: pipeline −44.6%,
    trivial one-shots honestly negative)
- **Still open in Phase 0:** outcome telemetry accruing locally from our own dogfood sessions
  (`/outcome` rows); Code Factory fill-prompt derived from the stage contract (validator currently —
  and correctly — rejects hand-prompted fills); corpus real-embedding batch on local Ollama (teardown
  plan #3).

### Phase 1 — HOSTED (blocked ONLY on owner credentials; hours of work once unblocked)
The same services behind real URLs. **Owner provides:** hosting credentials/keys/MCP (Fly/Cloudflare per
`deploy_topology`), domain decisions. **Agent executes:** `fly deploy` of the observer + web tiers
(images already build; preflight GO), tunnel/DNS cutover, secrets via the SOPS vault chokepoint,
health-gated rollout.
- **Tenancy law (decide before ANY external user):** consented session transcripts stay tenant-local;
  the consent gate (`observer.consent`, default-deny) is load-bearing and never weakened for
  convenience.
- **Exit receipts:** public health probe green from a machine we don't control; the 10 launch-contract
  metric groups publishing from the DEPLOYED service; zero-downtime redeploy demonstrated once.

### Phase 2 — DESIGN PARTNER (the first external human; 2–3 weeks after Phase 1)
One team that uses Claude Code/Cursor heavily runs AIDevObserver free.
- **Owner provides:** the intro (agent can draft outreach from the PMF docs). **Agent executes:** the
  installable package (`pipx`/`npx` one-liner wrapping `quickstart_aidevobserver`), MCP-directory
  listing, a weekly savings report generated from THEIR outcome telemetry.
- **Exit receipts:** ≥1 external team with ≥2 weeks of consented sessions; a token-savings receipt
  computed from THEIR sessions (the sales artifact); ≥1 reinvention catch they confirm was real.

### Phase 3 — PAID PILOT (the wedge, priced)
Sell the slice that is already excellent, not the average: **document extraction** (composition route
rate 1.0 in the domain benchmark) + the reuse/anti-reinvention coach.
- **Owner decides:** price (the $29–49/seat in the PMF docs is illustrative, unvalidated) and pilot
  terms. **Agent executes:** billing integration (per-seat or usage on the existing auth-realm design —
  separate login per product, NO SSO), the pilot's private registry namespace, the case-study receipt.
- **Exit receipt:** one paid invoice. That is the phase gate; nothing else counts.

## Flexibility guarantees (how the roadmap stays cheap to change)

Every capability is a **portfolio row, never a hardwired choice** — retrieval methodologies (the
receipt-raced zoo behind `retrieval_portfolio`), model lanes (`model_route.from_env`: Ollama Cloud /
NVIDIA / OpenWebUI / local, swappable per call), remix-vs-generate (deterministic mutators default, Code
Factory as a raced row), hosting (Fly first per `deploy_topology`, compose-file parity for anywhere
else), and every cache/lane with a proven fallback (cache→recompile-on-drift, factory→flag-only,
real-model→offline-proxy, observer→fail-open). Changing a vendor, model, or strategy is a row swap plus a
re-raced receipt — not a rewrite.

## Standing risks the roadmap must not paper over

1. **Composability is the physical constraint** — mean route rate 0.30 across benchmark domains; the
   product story leads with the domains where it is strong while the unmet-edge producer pipeline
   (`mint_unmet_edge_producers` + Code Factory) closes the rest.
2. **Token-savings claims must stay honest** — one-shot trivial tasks are measured NET-NEGATIVE; sell
   amortized, repeated capability (compile-once break-even receipts), never blanket percentages.
3. **Internal-machinery gravity** — the failure mode of every past month: another benchmark instead of
   a deployed URL. Phase gates are external-facing receipts precisely to resist this.
