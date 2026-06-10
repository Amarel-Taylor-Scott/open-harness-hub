# Baltor design principles

The non-negotiables every change honors. Enforced in practice by the proof-per-increment
discipline (`.claude/commands/baltor-goal-loop.md`) and the flywheel watchdog
(`scripts/baltor_flywheel.py`). Product boundary: **Baltor owns the contract** (context objects,
source handles, verification, enhancement, pack building, receipts, policy, delivery); **backend
tools are swappable infra**.

1. **Warrant before change** — clear user intent / ≥2 agreeing sources / an established repo
   principle, matched to blast radius; recorded; stale artifacts superseded in the SAME change
   (no orphaned contradictions). See `docs/codex/change-verification-contract.md`.
2. **No magic values** — one definition imported everywhere; repo-describing numbers computed,
   not typed; named constants with unit/rationale; drift checks where mirrored. See
   `docs/codex/no-magic-values.md`.
3. **Verify-first** — web-confirm any tool/repo/library/fact before it enters the repo; never
   trust a list. Source of truth: `data/backend-tools.yaml` + `research/backend-tool-verification.md`.
4. **Additive + capability-encapsulated** — new files/functions over edits to proven code; domain
   code depends on a capability port (`*Provider`), never a vendor SDK; every capability has a
   primary + fallback. See [`adapter-contract.md`](./adapter-contract.md).
5. **Real, or a labeled SEAM** — no faked results; absent network/creds → an interface + an offline
   `Canned*` fixture + a `--live` flag (e.g. `scripts/ingest/sanctions_feed_live.py`,
   `scripts/ingest/parser_provider.py`).
6. **Proof per increment** — every change ships a runnable, deterministic, offline self-test
   (`--self-test`) proving the contract; "green" via a real run, not prose.
7. **Decomposition contract** — documents are recursive trees of addressable typed objects with
   `ctx://…#page=…&block=…` fragment handles; claims attach to LEAF nodes; expansion pulls the
   minimal node; re-decompose→diff drives per-node rot. See `docs/backend/document-decomposition.md`.
8. **Storage rule** — canonical state is not text files; see [`table-shape-guidelines.md`](./table-shape-guidelines.md).
9. **Context-rot management** — TTL + content-hash CDC + ACL + supersession → typed signals →
   serve/refresh/block/human-review (`scripts/ingest/context_rot.py`). Freshness ≠ correctness.
10. **Promotion boundary + governance** — candidate-readiness ≠ tenant-visible; hold out would-be
    violations / quarantined / low-confidence / open-review; provenance + receipts on everything served.
11. **Phased + context-rot-conscious** — one coherent proven increment per pass; checkpoint; don't
    hold the whole plan in one context. See [`self-reorientation.md`](./self-reorientation.md).
