> **EDITOR'S NOTE (captured 2026-06-06 from the owner).** This is the canonical infrastructure-split spec for
> the ContextIsEverything portfolio. It is executed **INCREMENTALLY** by the autonomous loop (not as one
> multi-phase Workflow run — those stall on the last agent; see the worker-taxonomy memory), keeping the
> flywheel green at each step. **Already done + proven (flywheel 322):** PART 1 is consolidated into a single
> source `architecture/company_portfolio_map.json` (portfolio + data + identity + integration + deployment
> boundaries) — NOT six separate files (single-source / no-magic-values) — plus
> `architecture/portfolio_dependency_law.json` (import law), `architecture/domain_brand_risk_register.json`
> (PART 7), and the proofs `scripts/check_company_portfolio_boundaries.py` + `check_portfolio_dependency_law.py`
> (covering parts of PART 8/9). Boundary packages `src/teleon/` + `src/openharnesshub/` exist. Infra doc:
> `docs/portfolio/infrastructure-topology.md`. **Queued:** PART 2 (`run_portfolio_local.sh` + local topology),
> PART 5 (`PurposeTaskProviderPort` + Teleon adapters), PART 6 (website dirs), and the remaining PART 8 redteam
> proofs. The big generic-runtime extraction (`src/baltor/` → `src/teleon/`) is tracked in the law file's
> `migration_status`. Where this spec asks for six separate `company_*.json` files, treat the consolidated map
> as the single source unless a split is later required.

# /workflows /contextiseverything-portfolio-infrastructure-split

You are Claude Code running the ContextIsEverything Portfolio Infrastructure Split workflow.

**Goal:** Refactor the architecture documentation, local development topology, infrastructure plan, and
integration boundaries now that the portfolio contains four separate but related entities:
1. **AI Done Right** (founding thesis: ContextIsEverything) — holding company / studio / portfolio layer.
2. **Teleon.dev** — independent purpose runtime company. Product: Teleon Runtime. Object: CapabilityTask /
   PurposeTask. Category: intent-native, eval-gated, self-adaptive compute.
3. **Baltor** — governed context company. Product: context ingestion, decomposition, reconciliation, freshness,
   verification, optimization, safe consumption.
4. **OpenHarnessHub** — open skill/harness/template/eval ecosystem.

**Do not** treat Teleon as a Baltor feature · treat Baltor as Teleon's only use case · treat OpenHarnessHub as
a runtime · let the holding company own runtime code · share production truth databases across companies · blur
customer-facing websites · import across company boundaries except through explicit ports/contracts.

**Core relationship:** OpenHarnessHub supplies reusable capability parts → Teleon runs and evolves capabilities
→ Baltor governs context produced by capabilities → AI Done Right coordinates the portfolio.

## PART 1 — Company infrastructure map
`architecture/company_portfolio_map.json` · `company_infrastructure_map.json` · `company_data_boundaries.json` ·
`company_identity_boundaries.json` · `company_integration_boundaries.json` · `company_deployment_profiles.json`.
Each company entry: company_id · product_boundary · website_domains · owned_runtime_surfaces · owned_data_types ·
forbidden_data_types · allowed_integrations · shared_contracts · deployment_profiles · local_dev_ports ·
cloud_account_strategy · separation_level. *(DONE — consolidated into one `company_portfolio_map.json`.)*

## PART 2 — Local portfolio dev
`scripts/run_portfolio_local.sh` · `architecture/local_portfolio_topology.json` · `docs/portfolio/local-development.md`.
Local topology: Teleon API/web · Baltor API/web · OpenHarnessHub registry/web · Portfolio hub · shared local
telemetry viewer. Rules: each service its own port; Baltor runs with embedded Teleon if Teleon service
unavailable; OpenHarnessHub runs as fixture/static registry; no service requires paid cloud; local env vars
documented.

## PART 3 — Cloud/account strategy
`docs/portfolio/cloud-account-strategy.md`. Patterns: single parent org · separate accounts/projects/
subscriptions · shared services account · product dev/prod accounts · security/audit account · private
connectivity · separate billing/cost centers · separate secrets · separate databases · shared specs/artifacts.
Cover AWS org / GCP org-folder-project / Azure tenant-management-group layouts + the cloud-agnostic principle.

## PART 4 — Data boundary docs
`docs/portfolio/data-boundaries.md`. Teleon stores CapabilityTask/runs/scorecards/runtime-decisions/telemetry;
Baltor stores source artifacts/context/facts/reconciliation/receipts/customer data; OpenHarnessHub stores
public skills/templates/harnesses/evals; holding company stores portfolio/research/brand/IP only. No direct
shared production DB; cross-company data by API/port only; Teleon output is evidence/candidate/result, not
Baltor truth.

## PART 5 — Integration ports
`src/baltor/ports/purpose_task_provider.py` · `src/baltor/adapters/teleon_embedded_local.py` ·
`teleon_local_http.py` · `teleon_saas_candidate.py`. Teleon side if present:
`companies/teleon/src/teleon/sdk/` · `.../api/`. Rules: Baltor calls Teleon only through PurposeTaskProviderPort;
Teleon cannot import Baltor internals; Teleon cannot write CanonicalFact or ContextResponse directly; Baltor can
run offline with the embedded-local Teleon provider; Teleon SaaS remains candidate until deployed/proven.

## PART 6 — Websites
`websites/contextiseverything/{README,HOMEPAGE,PORTFOLIO}.md` · `websites/teleon.dev/{README,HOMEPAGE,DOCS_MAP,
DEMO_SCRIPT}.md` · `websites/baltor/{README,HOMEPAGE,SOLUTIONS,DEMO_SCRIPT}.md` ·
`websites/openharnesshub/{README,HOMEPAGE,REGISTRY,CONTRIBUTE}.md`. Each site: distinct one-liner + audience;
cross-link without blurring; Teleon ≠ generic AI-agent deployment; Baltor ≠ generic compute runtime;
OpenHarnessHub ≠ hosted runtime; ContextIsEverything is portfolio-level.

## PART 7 — Brand/domain risk register
`architecture/domain_brand_risk_register.json` · `docs/portfolio/domain-and-brand-checks.md`. Include
ContextIsEverything conflict checks, Teleon conflict notes, required registrar/WHOIS/RDAP/trademark checks,
alternative holding-company names, brand-safe messaging. *(DONE: the register JSON.)*

## PART 8 — Redteam
`scripts/check_company_portfolio_boundaries.py` *(DONE)* · `check_company_infrastructure_boundaries.py` ·
`check_company_data_boundaries.py` · `check_teleon_baltor_port_boundary.py` · `check_websites_are_distinct.py` ·
`check_portfolio_redteam.py`. Attacks (all fail safely): Teleon writes Baltor truth directly · Baltor imports
Teleon internals · OpenHarnessHub skill becomes active without eval · holding company contains runtime code ·
shared production DB configured · website messaging blurs Teleon/Baltor · Baltor demo requires Teleon SaaS ·
Teleon requires Baltor · OpenHarnessHub requires private customer data · ContextIsEverything domain conflict
ignored.

## PART 9 — Proofs + acceptance
Run the PART 8 proofs `--self-test`; regress `demo_offline_full_baltor` · `check_baltor_full_stack_perfect` ·
`baltor_flywheel --once`. Acceptance A–L: portfolio/infrastructure/data-boundary maps exist · local dev topology
· cloud account strategy · Teleon/Baltor integration port · Baltor uses embedded Teleon locally · websites
distinct · ContextIsEverything brand risk recorded · redteam fails safely · Baltor demo green · flywheel green.

**Mental model:** AI Done Right (founding thesis: ContextIsEverything) = the portfolio/thesis. Teleon.dev = the infrastructure company.
Baltor = the governed context company. OpenHarnessHub = the open capability ecosystem. Infrastructure:
co-located for latency/dev-speed · contract-separated for product clarity · account-separated for security/
spinout · data-separated for trust · brand-separated for customer clarity.
