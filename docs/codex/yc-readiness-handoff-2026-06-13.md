# YC-Readiness Handoff — 2026-06-13 (Opus 4.8 session → next agent / owner)

> **Purpose.** A clean handoff so another agent (Codex 5.5 / Claude Code) or the owner can pick up the
> YC-readiness work **without re-deriving this session's context** — the multi-agent audit, the fixes
> already shipped, the source-authority design (now built), and the items that still need an owner call.
> The flywheel (`python3 scripts/baltor_flywheel.py --once`, **468 proofs**) + `scripts/deploy/preflight.py`
> are the safety net: any change is gated. **One agent at a time on the same files** (concurrent edits
> conflict). When this doc and an older goal/runbook disagree on YC-readiness, this doc wins for that scope.

## How we got here
A multi-agent `ultracode` review (34 agents, 6 lenses, adversarially verified → 25 confirmed findings)
produced a prioritized report. The owner then said "do all, fully working, no placeholders, YC-ready."
This session implemented every **safe** finding and the **owner-gated engineering** ones; what remains is
genuinely owner judgment (brand voice) — specced below for a Codex run if desired.

Full delta: `git diff 6c5f27a0~1..HEAD`. Each item below cites its commit.

## DONE — shipped + flywheel-gated (do not redo)

**Tier-1 (the audit's demo-blockers / credibility):**
- **Demo-blocker port drift** `9307→9301` single-sourced from the registry + a `check_demo_control_tower`
  gate that fails CI on any dead demo surface. (`8e4f8eba`)
- **Runtime demo-load robustness**: EventBus lock, bounded SSE queue, `?limit=` guard, honest sandbox
  receipt. (`7507802a`)
- **No-magic single-sourcing** ×4 (embedding model/dim, source-backed ids, recording seam ports). (`52020b77`)
- **Security**: 7 drifted secret-scrubbers → one `scripts/security/response_redaction.py` + a gate. (`f53f93b2`)
- **Doc accuracy**: OFAC overclaim corrected to the proof tier; stale proof count → `⟦computed⟧`; OIPS
  layer signposted. (`d5bcc5a9`)
- (Pre-audit, same session) observable mailbox push + compose-cycle gate. (`6c5f27a0`)

**The "do all" owner-gated engineering:**
- **★ Source authority is now EARNED, not fixture-assigned** — the audit's #1 fundability gap. New
  `architecture/source_authority_registry.json` + `scripts/artifact_graph/source_authority.py`
  classify a source's rank from its **publisher/domain + verified signature** (eCFR=source-of-law,
  CFPB/OFAC/SEC/FDA=official_agency, unlisted=unverified=10, unsigned top-tier=downgraded).
  `reconciliation.py` derives rank from provenance and records the lineage in the receipt's
  `authority_basis`. **Proof (`check_source_authority`): flip the publisher and Reg-E STOPS winning** —
  authority is contingent on provenance. (`b93fe44e`)
- **M&A beneficial-ownership demo + OFAC 50% rule** — `scripts/showcase_pipelines/beneficial_ownership_resolver.py`
  (12th gallery pipeline). Resolves authoritative ownership from conflicting claims via the new classifier
  (SEC filing governs over a press rumor), propagates an SDN block down ≥50% chains (Apex/Meridian blocked
  by inheritance; 40%-owned Beacon not). Answers the owner's "merger-heavy industries (staffing/real-estate)"
  ask. (`569165fb`)
- **Per-node inference secrets + real native adapters** — each node's `secret_ref` resolves to its own key
  (OpenAI+Anthropic/BYOK side-by-side, no single global `OH_LLM_API_KEY`); `ollama_native` +
  `anthropic_messages` styles fully implemented (were stubs). (`d44a6c9e`)
- **Execution-dispatch fail-loud** — the executor is derived from `execution_backend_policy_matrix.json`
  (no hardcoded `_JOB_BACKENDS`/`_POOL_BACKENDS`); an unroutable backend fails loud, never silently runs on
  the function emulator. (`b70aeef1`)
- **Durable-queue crash recovery** — SqliteQueue (`claimed_at` + `reap_stuck` + startup reap) and RedisQueue
  (pull→`:processing` list + `reap_stuck`) both recover orphaned in-flight work; matching semantics. (`0d008098`)

## NOT a bug — the audit was wrong (leave it)
- **"Dead Baltor SPA" (`web/baltor/app.js` + `pages/` + `legacy.html`)** is an **intentional lossless
  preservation**: `scripts/port_full_design_to_web.py:520-523` renames each prior `index.html`→`legacy.html`
  "(lossless — the old front-end stays reachable, never deleted)". `app.js` is loaded ONLY by `legacy.html`;
  no check references it; the served `index.html` already runs the React `ce-*.jsx` app unambiguously.
  **Deleting it would violate the lossless law.** No action.

## REMAINING — owner decisions (specced for a Codex run)
1. **★ Positioning / applying entity (BRAND — owner ratifies the voice).** The audit found 5+ competing
   one-liners across 4 docs. Recommendation (grounded in the locked Baltor=applied-product decision + the
   sharpened wedge below): pick **Baltor, product-first**, ONE sentence —
   *"Baltor continuously verifies your AI's context is CORRECT — not just current — against authoritative
   sources, and proves it with a portable receipt."* Demote Teleon / AI-Done-Right / Open*Hubs to "how it's
   built." Codex spec: reconcile the headline + 50-char line across `docs/strategy/yc-application-draft-2026-06.md`
   + `…/yc-master-…md`; resolve the open owner-decision in the draft. **Do not change `architecture/brand.json`.**
2. **Component-count framing.** `1,045` (6 Action-types) vs `2,655` (all components) are different SCOPES, not
   a simple drift — pick which to lead with, mark it `⟦computed⟧` (the draft's convention). Owner call on scope.
3. **LLM-plane one-statement.** Two docs describe the plane in contradictory states. State it once:
   *"Default runtime is offline + deterministic (stub adapter, is_truth=False); a real cloud-LLM adapter
   (Anthropic Messages / OpenAI-compatible — now implemented, see `d44a6c9e`) lights up behind a key with
   output structurally pinned non-truth."* Safe factual reconciliation; Codex-runnable.
4. **Source-authority claim wording.** Now that authority is REAL (`b93fe44e`), the deck can honestly say
   "establishes which source is authoritative via publisher/provenance" — update the draft's claim to match
   the built capability (it currently under- or over-states it depending on the doc).

## The sharpened wedge (from this session's web sweep — `docs/research/agent-governance-landscape-2026-06-13.md`)
The "receipts" white space is now **contested** (Attested Intelligence, Fetch.ai AEVS, Diagrid, NexArt all
ship tamper-evident *execution* receipts). **None govern TRUTH** (promote/reject a fact + CDC + capability-lift
on a regulated beachhead). Lead with **"we govern what becomes true, not just sign what happened."** Hard
why-now: **EU AI Act full enforcement Aug 2, 2026** (72h incident reconstruction). Name the data-gravity
threat honestly (ClickHouse+Langfuse, Atlan).

## Gates / acceptance
- `python3 scripts/baltor_flywheel.py --once` → **GREEN 468/468** (every fix above is a registered proof).
- `python3 scripts/deploy/preflight.py` → **GO**.
- Container e2e (the discipline that caught the real deploy-blockers): build with `POSTGRES_PASSWORD=x`,
  `docker compose -f deploy/docker-compose.deploy.yml -f deploy/docker-compose.localtest.yml up -d`.
- The remaining gap to "live" is the owner-gated cloud step only (Fly account/billing/login/keys, Cloudflare DNS).
