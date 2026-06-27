# OpenHarnessHub — Page map & purposes

Hash-routed prototype (`OpenHarnessHub Prototype.html`). Marketing pages are
light; app pages dark (overridable). Sidebar = **Build · Explore · Workspace ·
Govern · Connect · Foundry · Account**. Logged-out users get a sidebar-free path.

> **IA note (resolved):** `/browse` → redirects to `/components`; `/marketplace`
> and `/explore` → redirect to `/pipelines` (Marketplace folded into the **Source**
> filter; Explore folded into the two Explore tabs). Stale ⌘K palette entries removed.
> **Tweaks** (text-size · density · intensity) live in the bottom-left theme switcher,
> persisted to `localStorage` (`ohp-tweaks`).

## Marketing / unauthenticated
| Route | Page | Purpose |
|---|---|---|
| `/` | Landing | The one move: paste a hyper-specific task → build. Bare entry box + **modality-tabbed examples** (Text · Image · Audio · Video — placeholder + example chips swap per modality). |
| `/preview` | Build preview (no sidebar) | Logged-out result: shows the flow being built (readable steps + techniques), then **"sign up to run or download."** |
| `/solutions` · `/solutions/:n` | SDG solutions | Marketing-credibility page (browse without signing in). Each of the 17 goals opens a **gallery of hyper-specific pipelines** (input → output). Not in app nav. |
| `/pricing` | Pricing | Four tiers + the **open-spec vs governed-content** boundary (free spec/SDK/export; paid vetted components & live knowledge). |
| `/signin` `/onboarding` `/upgrade` `/checkout` | Auth / onboarding / paywall / checkout | Minimal-shell: sign in → onboarding (sets logged-in) → app; quota paywall; payment. |

## Build (pinned top — dropdown)
| Route | Page | Purpose |
|---|---|---|
| `/build` | New build | Confirm parsed intent + constraints, then assemble. Clarifying question if ambiguous. |
| `/drafts` | Drafts | Saved / in-progress flows to resume. |
| `/results` | Builder results | Three flows for the task, **lift-led**, cost as words (low/medium/high). |
| `/flow` | Flow canvas | The wired pipeline: Conditional → Knowledge → Action → QA/refine → Output, drawn edges, node inspector + swap. |

## Explore
| Route | Page | Purpose |
|---|---|---|
| `/pipelines` | Explore pipelines | Prebuilt governed pipelines (lift shown here). **Modality tabs**: Text (default) · Image · Audio · Video — 4 example pipelines each. Top filter bar: **Source** = Free·OpenHubForAI / Premium·OpenHubForAI / Community free / Community paid. |
| `/components` | Explore components | Reusable building blocks. **No lift** (lift is pipeline-level). Source + Primitive filters at top. |
| `/c/:slug` | Detail | One pipeline/component: description, provenance, cost & portability, deep config (overrides, versions, pinning). Pipelines show lift; components show "where it fits". |
| `/requests` · `/requests/:id` | Capability requests | Demand board (vote) → fulfillment (premium build / community build for credits). |

## Workspace
| Route | Page | Purpose |
|---|---|---|
| `/app` | Dashboard | Resume flows, recent runs, suggested gaps, persistent task box. |
| `/activity` | Activity & notifications | Event feed (version bumps, CDC, revocations, decay, promotions) + email-digest config + watches. |
| `/run` | Run / trace | Replayable audit record: per-step cost/tokens/timing incl. a QA step; simulate banner; error→retry. |
| `/dashboards` | Dashboard composer | Widgets bound to component-generated stores (cost, cache, **lift-over-time decay**, freshness). |

## Govern
| Route | Page | Purpose |
|---|---|---|
| `/registry` | Private registry | Your proprietary components/context (private, never leave). |
| `/publish` | Publish to ecosystem | Share facts / pages / lists / conditions / repos → **immutable, signed, permanently public**; agent-publish config. |
| `/freshness` | Verified feed | Primary-source government scrapers, CDC change feed, freshness-SLA tiers, signing. The recurring-value moat. |
| `/trust` | Trust center | Signatures, verified publishers, canary/watermark, SOC2/GDPR. |
| `/audit-log` · `/roles` | Audit & RBAC | Immutable event log; role/permission matrix. |
| `/attest` · `/p/:id` | Certified export · provenance graph | Auditor-grade signed attestation (valid-through → renew); full source→signature→citation lineage. |

## Connect (bring your world in)
| Route | Page | Purpose |
|---|---|---|
| `/connect` | MCP bridge | Local-first: your agents source locally, call OpenHubForAI over MCP to fill gaps; privacy boundary. |
| `/sources` | GitHub source search | Vectorized search over OSS repos; ingest candidates that clear the gate; not-implemented objects link out. |
| `/improve` | Import & Improve | Upload your existing pipeline → critique → measured before/after (lift, cost, governance). The land wedge. |

## Foundry (how the catalog is made — operator/credibility)
| Route | Page | Purpose |
|---|---|---|
| `/foundry` | Component factory | The evidence funnel (probed → … → **promoted, never generated**); reject log; source yields. |
| `/workers` | Internet workers | Remote sandboxed agents sourcing the live web under the lift & license gate; feed the foundry. |

## Account
| Route | Page | Purpose |
|---|---|---|
| `/pricing` `/settings` `/admin` | Plan · deep config · admin | Providers/keys/deploy/privacy/advanced; users, credits & trials, API usage. |
| `/k/:id` | Knowledge entry | A single fact page: content, per-entry provenance, triggers, cited-in, freshness. |
| `*` | 404 | Offers the entry box + browse. |
