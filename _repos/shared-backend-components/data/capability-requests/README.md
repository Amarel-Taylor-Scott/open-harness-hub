# Capability requests (demand capture)

A **capability-request** is a typed empty slot for something the catalog does
**not yet provide** — the demand-capture object behind build-on-demand. It is
**not** an eighth primitive and **not** a catalog component type; it is an
operational object like a review-ticket. Schema:
`schemas/capability-request.schema.json`. Concept:
`docs/concepts/component-taxonomy-and-stages.md` → "Not an eighth primitive".

- **Typed slot:** carries the `target_type` it will become (one of the 14
  component types), so it stays inside the seven-primitive model. The primitive
  is derived from `target_type` (never stored — avoids drift).
- **Maturity `abstract`:** the only pre-component tier
  (`vocabularies/lifecycle.yaml`). Never tenant-visible as a component.
- **Promotion only via the lift gate:** `requested → … → built → verifying →`
  **two-axis lift gate (lift AND durability,
  `scripts/eval/durable_gap_harness.py`)** `→ promoted` (mints a real component
  at `experimental`). This is the guard that stops a build-agent from
  manufacturing junk.
- **Fulfillment:** `agent_build` (premium hosted build-on-demand) or
  `community` (a contributor earns credits when the shared component passes the
  lift gate).
- **Seed material:** candidate repos from `data/repo-catalog/`; gap ranking
  reuses `data/research-queue/areas.jsonl`.

`requests.jsonl` — one JSON object per line, validated against the schema.
