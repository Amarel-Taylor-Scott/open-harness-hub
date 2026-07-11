# OpenRoutingHub.io (private preview)

**Kind:** Model-routing policy · **Status:** private-first candidate (owner-proposed 2026-06-09) ·
**Accent:** muted `#69728a` → future `#4c6ef5` on open · **Glyph:** ⇉

Open abstracts for model-routing **policy** — the cards Teleon's inference gateway consumes:
portable preference specs (OIPS), numeric provider-selection graphs, lane policies (dev · agent ·
interactive · batch · self-host), governed fallback chains, and the `ModelInvocationReceipt` of
which model actually served. **Policy, not endpoints; cards, not a runtime.**

- **Distinct from OpenEndpointHub** — endpoints catalog *where* a model lives; this catalogs *how*
  to choose and fall back among them.
- **Teleon's inference gateway is the runtime** that consumes these cards; the hub is the open
  registry of the cards (candidate ≠ active; serves no keys and no truth).
- **Substrate (real, already built):** `src/teleon/inference` (gateway + OIPS), the numeric
  provider-selection graph, the design bundle's five-lane LLM-ECONOMICS, and `scripts/billing_ledger`'s
  model-CLASS→rate map.

Built the branded-house way: a `makeHub({…})` config in `openroutinghub-main.jsx` + one accent +
the `openRoutingHub` entity in `shared/products.js`. Opening it to the public is a one-line
`status: 'private' → 'live'` flip (accent saturates, banner clears) **after** owner domain/trademark
clearance + its open trigger (a routing-policy registry competitor appears, or the inference-gateway
public release).
