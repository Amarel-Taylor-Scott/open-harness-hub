# Handoff: AIDR Platform Productionization (Passes 1–12, CURRENT)

**For Claude Code, working in the real AI Done Right repo.** This bundle is the
complete, current output of twelve productionization passes. It supersedes all earlier
handoff copies. Entry point: **`START-HERE-CLAUDE-CODE.md`** (the paste-in prompt with
the hours-long operating loop) → then **`production/CLAUDE-CODE-BACKLOG.md`** (the
canonical 9-phase task queue, every task with its proof and prompt).

## Read this first

1. **Your identity service is canonical.** `scripts/identity_local_service.py`
   (12 separate per-product realms, `/api/identity/<realm>/*`, port 9410, no SSO,
   hash-only raw-once keys, audit JSONL with `X-AIDR-Request-Id`). Nothing here
   replaces it. `production/core/` (Node) is a reference sketch for the events/A-B
   and LLM planes ONLY — do not duplicate identity in Node.
2. **The HTML files are design references** (single-file React-via-Babel, run in any
   browser). Recreate their flows in the real codebase using its patterns; don't ship
   the HTML. They are hi-fi for layout/copy/behavior.
3. **Honesty rules are part of the spec:** Mode Protocol (live/simulated, never
   silently fake), PROPOSED contracts say so, no fake secrets/providers, every claim
   names its proof, gap ledger stays current.

## Bundle map

```
design_handoff_platform_productionization/
├── README.md                     ← this file
├── START-HERE-CLAUDE-CODE.md     ← paste-in prompt: /goal, reading order, operating
│                                   loop, self-troubleshooting playbook, cloud path
├── shared/
│   ├── oh-identity.js            realm-aware identity client (ENDPOINTS map = the seam)
│   └── oh-service-auth.js        service↔service dev tokens (PROPOSED /service/* contract)
├── reference-designs/            all viewable docs + consoles (tokens bundled)
│   ├── Identity Wiring — Account Flow Prototype.html      (golden-path auth UI)
│   ├── Service Connections — Dev Console.html             (handshake/verify/revoke)
│   ├── Productionization Pass 1 — Audit and Plan.html
│   ├── AIDR Standards — Production Handbook.html          (S1–S13 visual index)
│   ├── CICD Options Review — S5 Decision.html
│   ├── One-Click Local Platform — Runbook.html
│   ├── Platform and Business Review — Pass 9.html
│   ├── Expansion Scenarios — Pass 10.html
│   ├── Ops, Pro-Forma and GTM — Pass 11.html
│   └── LLM Economics and Backlog — Pass 12.html
└── production/                   the runnable scaffold + all canonical docs
    ├── CLAUDE-CODE-BACKLOG.md    ★ THE QUEUE: phases 0–8, ~35 tasks w/ proofs+prompts
    ├── services.json · justfile · docker-compose.yaml · Caddyfile · .env.example
    ├── scripts/  deploy.py (self-orienting) · gen_caddy.py · latency_probe.py · tunnel.sh
    ├── core/     platform-core reference (events sink, LLM plane, receipts, handshake)
    ├── contracts/  SERVICE-CONNECTIONS.md · EVENTS.md · BUSINESS-PLANE.md
    ├── standards/STANDARDS.md    S1–S13 (incl. S5a/S5b pipeline, S11 economics,
    │                             S12 anti-fragility, S13 business plane)
    ├── cloud/    GRADUATION.md (L0–L3) · SCENARIOS.md (S-A…S-J) · PLATFORM-REVIEW.md ·
    │             LLM-ECONOMICS.md (five lanes, self-host triggers)
    ├── business/ PRO-FORMA.md (staged burn + revenue scenarios) · MARKETING.md (GTM)
    ├── OPERATIONS.md             ops index: cadences + runbooks
    ├── ci/github-actions.yaml    refactor to thin `just` calls (S5a) when landing
    ├── vault/README.md           SOPS+age flow
    ├── terraform/main.tf         named tunnels + DNS skeleton (never applied, G-5)
    └── README.md                 run instructions · gap ledger G-1…G-10 · pass log
```

## How to start (the whole thing in four lines)

1. Paste the prompt block from `START-HERE-CLAUDE-CODE.md` into Claude Code.
2. It reads the listed docs, then works `production/CLAUDE-CODE-BACKLOG.md` top-down:
   Phase 0 = `just plan` → `just up` → `just tunnel` (first proof: deploy receipt +
   green /health through a trycloudflare URL).
3. One proof-backed task per pass; pass log + G-ledger updated every pass; loop runs
   unattended (stuck protocol: 3 different attempts → record gap → next task).
4. Cloud later is a relocation, not a rewrite: ladder L0–L3, scenario triggers, and
   spend ceilings are pre-decided in `cloud/`.

## Decisions already taken (don't re-litigate without new facts)

| Decision | Where |
|---|---|
| Realm isolation, no SSO, raw-once hash-only keys | backend + S3 |
| Mode Protocol live/simulated/unknown | S2; both clients implement it |
| GitHub Actions orchestrates; logic in `just` (S5a); pull-based deploy (S5b) | S5 + CICD review |
| One `/api/<plane>/*` namespace local=tunnel=prod; routes/compose generated from services.json | Pass 6 runbook |
| Vault = SOPS+age now; OpenBao at runtime-rotation need | vault/README.md |
| K8s-ready-not-K8s-run; GKE Autopilot first at S-F triggers; managed only | S12 + SCENARIOS S-F |
| L2 = one VM (Hetzner CPX22 ≈$9.49/mo); Cloud Run for L3 stateless planes; Lambda/Render pass | PLATFORM-REVIEW + GRADUATION |
| LLM spend: five lanes, model classes not names, batch lane for verification rail, self-host triple-gated | LLM-ECONOMICS.md |
| Billing: ledger-only adapter first; receipts reconcile Stripe, never vice versa | BUSINESS-PLANE.md |
| Email: console adapter → Resend → Postmark/SES; no silent sends | BUSINESS-PLANE.md |
| Hubs = subdomains until each earns its .io at launch | PRO-FORMA.md |

## Design system (binding for any UI work)
Tokens only (`oh-tokens.css` is the single color source) · one accent per brand
(`products.js`) · Hanken Grotesk display + IBM Plex Mono · `.oh-card` physics ·
zero overflow, light+dark clean. The reference designs are the styling spec.

## Gap ledger snapshot (full ledger: production/README.md)
G-1 partial (auth/keys wired in reference; kit promotion = backlog 1.3) · G-2 registry
CRUD (Phase 5) · G-3 HMAC receipts (Sigstore-compatible shape) · G-4 LLM quotas/
streaming (4.5) · G-5 terraform never applied (7.2) · G-6 no SSO by design · G-7
JSON-file persistence (Postgres+JSONB policy ready) · G-8 the design workspace never
executes — all runs happen on your machine · G-9 deploy.py unexecuted (Phase 0.1) ·
G-10 vault needs sops+age, honest .env fallback.
