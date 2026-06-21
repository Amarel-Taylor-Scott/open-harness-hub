# GOAL — Finalize the Teleon THIN CONTROL / METADATA / ORCHESTRATION plane (YC MVP)

Long-running, minimal-stops loop. Mission: make Teleon a **working, demonstrable thin control plane** for the YC app —
it SELECTS + GOVERNS + LEARNS; **compute runs on the client's infrastructure (Cloudflare Workers + Workers AI via a
BYO API key)**, not ours. Our own compute (K8s / cloud functions / images) is EXPLICITLY future scope. Canonical
positioning: `docs/architecture/teleon-control-plane-vs-compute.md`.

## Operating rules
- **Decide autonomously; do not stop to ask.** Sequence the work yourself; make ONE proof-backed increment per cycle.
- **Stop only** when `.agent/STOP_REQUESTED` exists OR the MVP acceptance checklist below is all-green.
- Every increment lands with a `--self-test` (the repo idiom) and must keep the regression sweep green
  (see "Proof gates"). serves_truth=false for all model/run output; lossless (the brain is append-only).
- Match the change-verification + lossless + no-magic-values laws (CLAUDE.md). Archive-not-delete; never untrack.
- Anti-slop prose; no filler; reuse existing seams — do NOT build a parallel runtime.

## Compute flexibility (NON-NEGOTIABLE — Cloudflare is a default, not a lock-in)
Cloudflare Workers is the MVP **default** because it's the easiest to run/integrate — but Teleon must NEVER be
hardwired to it. ALL compute goes through `ExecutionProviderPort` (`architecture/execution_backend_policy_matrix.json`
`backends_enum` already lists k8s_deployment_worker, k8s_job, aws_lambda, gcp_cloud_run_function, azure_function,
cloudflare_workers, openfaas_knative, cloud_run_job, gpu_pool, sandbox_worker — all `@candidate`). Adding OUR OWN
compute (K8s / cloud functions / container images / GPU pools) later is a **config + one adapter**, not a rewrite, and
runs SIDE BY SIDE with Cloudflare, selected by policy/pricebook/health. The `compute_ownership` dimension keeps all
three loci open (provider_operated = our infra · customer_account = BYO key like Cloudflare · customer_managed = their
cluster). Every cycle must preserve this: no Cloudflare-specific assumption leaks above the port. A drift check should
fail if any backend becomes non-swappable.

## Scope guardrails (MVP = client compute)
- **IN:** the control plane — selection (model_index / search / step catalog / objective), governance (receipts,
  promotion boundary, serves_truth), the descent brain (`descent_attempt_store` + `external_outcomes`), and dispatch to
  EXTERNAL compute via `ExecutionProviderPort` → `CloudflareWorkersProvider` (BYO customer key) + Cloudflare Workers AI lane.
- **OUT (future):** our own compute fleet (K8s / cloud functions / container images / GPU pools). Keep them as
  `@candidate` behind the port — do not build them now.
- Teleon need NOT run the final unit or the improvement runs — it tracks results+metadata to guide improvement.

## Per-cycle increment (pick the highest-leverage next step toward the checklist)
1. End-to-end thin-control-plane path: a CapabilityTask → resolve the PER-FUNCTION medium
   (`src/teleon/config/medium_resolver.py` over `architecture/medium_config.json` — Cloudflare-preferred when a token
   is present, else the configured/fallback lane) → COMPILE the unit (`src/teleon/compiler`) → dispatch to the chosen
   compute (BYO Cloudflare key; offline → local_function_emulator) → record receipt + a DescentAttempt
   (`external_outcomes.record_external_outcome`) → `guide_next` recommends the next move. Mediums (compute/llm/search)
   are UI-configurable per function (`dist/teleon-config/index.html`) — different mediums for different functions.
2. Wire the live Cloudflare path (a real Worker deploy/dispatch with a test token) behind the existing offline-safe seam.
3. Make the demo dashboard show the control-plane loop (selected config, where it ran, receipt, brain guidance).
4. Tighten governance/receipts + the BYO onboarding (paste a Cloudflare token → ready).
5. YC-facing polish: the one-screen story (select → run-on-their-Cloudflare → receipt → learns).

## Proof gates (run each cycle; all must pass)
```bash
PYTHONPATH=. python3 scripts/check_teleon_control_plane.py --self-test
PYTHONPATH=. python3 scripts/check_medium_config.py --self-test
PYTHONPATH=. python3 scripts/check_execution_provider_factory.py --self-test
PYTHONPATH=. python3 scripts/build_config_ui.py --self-test
PYTHONPATH=. python3 scripts/config_ui_server.py --self-test
PYTHONPATH=. python3 scripts/check_byo_compute.py --self-test
PYTHONPATH=. python3 scripts/check_surface_map.py --self-test
PYTHONPATH=. python3 scripts/check_teleon_example_descents.py --self-test
PYTHONPATH=. python3 scripts/check_dag_pipeline.py --self-test
PYTHONPATH=. python3 scripts/run_teleon_demos_live.py --self-test
PYTHONPATH=. python3 scripts/check_portfolio_dependency_law.py --self-test
python3 scripts/check_ai_done_right_surface_family.py --self-test
```

## MVP acceptance checklist (definition of done)
- [ ] A customer can supply a Cloudflare API key (SecretRef) and a capability unit runs on THEIR account (BYO).
- [ ] Teleon does NOT execute the final unit; it selects + dispatches + records (receipt + brain).
- [ ] The descent brain records external runs + `guide_next` returns an improvement recommendation from them.
- [ ] Improvement LLMs can run on Cloudflare Workers AI (the lane is wired).
- [ ] The demo dashboard shows the control-plane loop end-to-end with real numbers.
- [ ] All proof gates green; dependency law + family green; serves_truth=false; lossless; nothing untracked/deleted.
- [ ] A one-screen YC story: "paste a key → your capability runs bounded on your Cloudflare → receipt → it gets cheaper."

When all boxes are green, write a short status note to `docs/status/` and stop.
