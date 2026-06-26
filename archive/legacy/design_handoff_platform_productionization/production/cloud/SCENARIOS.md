# Expansion Scenarios — triggers, responses, costs, reversals (Pass 10)

Companion to PLATFORM-REVIEW.md and GRADUATION.md. Each scenario names: the TRIGGER
(a measurement, never a mood), the RESPONSE (smallest architecture change), the COST
(verified Jun 2026 — re-verify at adoption), and the REVERSAL. The ladder discipline
holds: never enter a scenario speculatively.

## S-A · Now: solo operator, design-partner traffic
- **Trigger:** — (current state)
- **Response:** L0/L1 — laptop + `just up` + tunnel; named tunnel when URL churn hurts.
- **Cost:** $0.
- **Reversal:** —

## S-B · First real users (~100 signups, <100k events/mo)
- **Trigger:** any external user depends on uptime beyond laptop hours.
- **Response:** L2 — one Hetzner CPX22 (2 vCPU/4GB, ~€7.99 ≈ $9.49/mo post-Apr-2026,
  20TB EU bandwidth) or DO Basic ($24/mo, 4TB) if US-first + managed-UX preferred.
  Cloudflare in front (CDN/DDoS, $0). Same `just up`; uptime-kuma added.
- **Cost:** $10–25/mo, inside the $15 L2 ceiling at Hetzner.
- **Reversal:** point tunnel back at laptop; `compose down`.

## S-C · One product takes off (e.g. Baltor signups spike)
- **Trigger:** p95 budget breach or sustained CPU >70% on the VM, attributable to one plane.
- **Response:** split THAT plane to Cloud Run (scale-to-zero, per-request); the
  manifest entry changes kind, routes stay identical behind the gateway. Static
  surfaces go CDN (Cloudflare Pages, $0) at the same moment.
- **Cost:** Cloud Run free tier then usage; egress ~$0.12/GB is the line to watch.
- **Reversal:** the container is unchanged — `kind: container` again, one deploy.

## S-D · Hubs go viral (bursty public registry traffic)
- **Trigger:** uptime-kuma shows sustained spikes; bandwidth bill or VM saturation.
- **Response:** registries' read paths are static-first by design — CDN absorbs reads;
  only publish/verify APIs scale on Cloud Run.
- **Cost:** near-$0 for reads (CDN); usage for writes.
- **Reversal:** trivial — CDN is additive.

## S-E · Enterprise / self-host customers
- **Trigger:** a customer wants AIDR inside their network.
- **Response:** none on our infra — this is the container thesis paying out: signed
  images + compose bundle + vault seam ARE the product. Verified-deployment handshake
  (I-3) gives them the badge, us the heartbeat.
- **Cost:** $0 infra; packaging work only.
- **Reversal:** n/a.

## S-F · K8s entry (the real one)
- **Trigger (all three):** >1 host AND >10 containers AND a measured orchestration
  pain (placement, rollouts, autoscaling) that compose + deploy.py can't express.
- **Response:** **GKE Autopilot first** — per-pod billing (~$0.0445/vCPU-hr +
  $0.0049/GiB-hr) means zero bin-packing waste and no node ops; the $74.40/mo free
  tier covers one cluster's management fee. AKS is the cost alternative (free control
  plane; cheapest at 50–200 nodes). EKS only if the stack is already AWS — flat
  $73/mo/cluster and a 6× fee jump ($438/mo) for clusters outgrowing the 14-month
  support window. K8s manifests are GENERATED from services.json (same pattern as
  gen_caddy.py) — written at entry, not before.
- **Cost reality check:** a 3-node production cluster runs $450–650/mo all-in; a
  4-pod Autopilot workload ~$78–80/mo. That's the entry fee — hence trigger-gated.
- **Reversal:** images and manifest unchanged; compose remains the dev topology forever.
- **Provider-migration rule (adopted):** if the cost gap between K8s providers is
  under $5k/mo, do not migrate — optimize in place.

## S-G · GPU / self-hosted inference
- **Trigger:** LLM-plane receipts show provider spend > the cost of owned capacity,
  or a customer demands on-prem models.
- **Response:** the LLM plane's router is the seam — add a self-hosted adapter
  (vLLM/Ollama) on a GPU box: Hetzner GEX44 (RTX 4000, 20GB) ~€184/mo for inference.
  Callers never know.
- **Cost:** €184/mo+ — needs receipts showing ≥ that in monthly provider spend.
- **Reversal:** route models back to providers; the adapter is config.

## S-H · EU data residency / GDPR posture
- **Trigger:** first EU enterprise customer or regulator question.
- **Response:** realm isolation already gives per-product data boundaries; pin EU
  realms' volumes to Hetzner DE/FI (GDPR-friendly, EU-owned). Events stay anon-id-only
  (S7) — that's most of the GDPR surface pre-handled.
- **Cost:** ~$10/mo for a second region VM.
- **Reversal:** volumes snapshot + restore; manifest region tag.

## S-I · Repatriation insurance (standing posture, not a scenario)
The 2026 pattern is real: large-scale moves OFF hyperscalers to cut cost (37signals,
Dropbox-class examples; surveys put cloud waste at 27–32% of spend). Our posture:
every level keeps the exit open — compose is the canonical topology, the manifest is
the architecture, adapters hold the vendors. **Re-run the cost math at every level
change; moving DOWN the ladder is success, not failure.**

## S-J · Rebrand / spin-out / acquisition of a hub
- **Trigger:** business event.
- **Response:** S12 naming standard pays out: stable internal ids everywhere means a
  rebrand touches `products.js` + docs; a spin-out is a realm + its volumes + its
  manifest entries + its secrets — a bounded, listable set.
- **Cost:** ~0 engineering.
- **Reversal:** n/a.

## Spend-threshold cheat sheet
| Monthly infra spend | Posture |
|---|---|
| <$50 | One VM. Anything more is ceremony. |
| $50–500 | VM + Cloud Run for the hot plane + CDN. Re-verify budgets quarterly. |
| $500–2k | Consider K8s ONLY if the S-F triggers are all true; else second VM. |
| >$2k | Full review pass; CUDs/commitments (28% 1-yr / 46% 3-yr flex) once usage is proven stable. |
