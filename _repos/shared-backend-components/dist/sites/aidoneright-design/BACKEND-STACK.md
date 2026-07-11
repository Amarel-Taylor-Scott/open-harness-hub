# Backend Building Blocks — open-source that could power the OpenHarness family

A research-backed map (June 2026) of **what existing open-source projects could power the
backend of each site**, so the prototypes have a credible, implementable substrate instead of a
from-scratch build. Companion to `POSITIONING-AUDIT.md` (§5 Baltor, §6 Teleon competitive maps)
and `CLAUDE-CODE.md` (handoff).

> **The big insight.** The prototypes' invented vocabulary maps onto *real, mature open
> standards* — which is both a credibility boost and an implementation path:
>
> | Prototype term | Real open standard / project |
> |---|---|
> | **receipt** (signed, append-only) | **Sigstore** — Cosign signing + **Rekor** transparency log (keyless, OIDC-tied) |
> | **AIBOM** (already in Baltor copy) | **OWASP CycloneDX AI-BOM** (v1.6) / SPDX — bill of materials for AI artifacts |
> | **provenance / source handle** | **SLSA** provenance + **in-toto** attestations (DSSE envelopes) |
> | hub **risk score** | **OpenSSF Scorecard** (scorecard.dev) — automated artifact/repo risk scoring |
> | backend **RepoIntelClassifier** | Scorecard-style signals — *discovery ≠ trust, stars ≠ proof* |
> | **related artifacts** graph | **GUAC** (OpenSSF) — graph DB aggregating SBOM + provenance |
>
> Net: the OpenHarness hubs are essentially **"the software-supply-chain-security model (SLSA +
> Sigstore + SBOM/AI-BOM + Scorecard) applied to AI artifacts"** — context packs, skills, tools,
> MCP servers, benchmarks, harnesses. That's a strong, defensible frame and a buildable backend.

---

## Shared substrate (every site)

| Backend component | Open-source building blocks | Notes |
|---|---|---|
| **Signing + receipts** | **Sigstore** (Cosign / Fulcio / Rekor) | Keyless signing; Rekor is the append-only, publicly auditable transparency log = the "receipt" ledger. |
| **Provenance / attestation** | **SLSA** (v1.1), **in-toto**, DSSE | Verifiable "how this artifact was produced"; policy-enforceable. |
| **Bill of materials** | **CycloneDX** (AI-BOM / ML-BOM), **SPDX**, **Syft** | CycloneDX v1.6 has native AI-BOM — the standard behind Baltor's "AIBOM / EU AI Act dossiers". |
| **Risk scoring** | **OpenSSF Scorecard**, CodeQL, Dependabot | Powers every hub's risk score + the RepoIntelClassifier; vendor-neutral. |
| **Artifact registry / storage** | **OCI + ORAS**, **Harbor**, the **Hugging Face Hub** pattern | Store versioned artifacts + metadata; ORAS pushes arbitrary artifacts to any OCI registry. |
| **Schema + validation** | **JSON Schema**, **Pydantic**, OpenAPI | The ObjectShell / artifact schemas validate here. |
| **Search** | **Meilisearch**, **Typesense**, **OpenSearch** | Registry browse/search across artifacts. |
| **Identity / access** | **Keycloak**, **Ory** (Hydra/Kratos), OIDC | SSO/SAML, the visibility-policy enforcement point. |
| **Experiments / analytics** | (already shipped) `OHExp` → `dataLayer`; wire **GA4 / PostHog / Segment** | The prototypes already emit events; this is the real-analytics sink. |

---

## Per-site backend map

### OpenContextHub — context packs
- **Storage/registry:** OCI+ORAS or HF-Hub-style; **CycloneDX AI-BOM** per pack.
- **Provenance:** SLSA + in-toto so each pack's origin is verifiable; **Sigstore** signs it.
- **Memory/graph neighbors** (if packs carry relationships): **Graphiti**, **Cognee**.
- Boundary: *reference context is not served truth* — Baltor governs before consumption.

### OpenSkillsHub — skills / SKILL.md
- **Risk/scan:** the agentic-skills supply-chain problem is real and measured — a 2026 study
  scanned **42,447 skills and found ~26% vulnerable** (SkillScan). Use **OpenSSF Scorecard** +
  skill-specific scanners; *discovery is not trust*.
- **Signing:** Sigstore per skill version; **SLSA** provenance.
- **Distribution:** the emerging skills directories (skills.sh-style index) as the public catalog.

### OpenToolsHub — executable tools
- **Runtime security / gating:** **Microsoft Agent Governance Toolkit** (open-source, April 2026)
  — maps the **OWASP Agentic AI Top-10** to controls; exposes `ToolCallInterceptor` /
  `PolicyProviderInterface` for the "executable access is gated" rule.
- **Scanning:** **Snyk agent-scan** (acquired Invariant Labs) — LLM-as-judge + heuristics.
- Boundary: *public listing ≠ public execution.*

### OpenMCPHub — MCP server intelligence
- **Registry:** the official **Model Context Protocol registry** + MCP SDKs as the substrate.
- **Risk/conformance:** **MCPTox** (tool-poisoning benchmark) + the Agent Governance Toolkit for
  MCP risk and install profiles; *MCP discovery is not trust — conformance + risk required.*

### OpenCompressionHub — compression & budget intelligence
- **Compressors:** **LLMLingua / LongLLMLingua** (Microsoft) and similar prompt-compression libs.
- **Fidelity benchmarks:** run via the eval stack below; *token reduction is not success unless
  fidelity (source handles + held-out warnings) survives* — assert that as a conformance test.

### OpenBenchmarkHub — benchmark intelligence
- **Eval engines:** **EleutherAI lm-evaluation-harness**, **UK AISI Inspect**, **Stanford HELM**,
  **RAGAS**, **promptfoo**, **DeepEval**.
- **Result records:** signed (Sigstore) + attested (in-toto) so a benchmark *result* is evidence
  with provenance; *evidence, not authority — a result cannot promote a candidate alone.*

### OpenHubForAI — harnesses & evals
- **Harness/eval runners:** the eval engines above + fixtures/rubrics as versioned artifacts.
- **Conformance packs:** in-toto attestations that a harness ran and what it proved.

---

## Products (cross-ref the competitive maps)

- **Baltor backend** — composes with the memory/observability/eval/catalog OSS in
  `POSITIONING-AUDIT.md §5`; its receipts = **Sigstore/Rekor**, its AIBOM = **CycloneDX AI-BOM**,
  its lineage = **OpenLineage/Marquez** (catalog-ingestable). Verification-vs-authority is the
  bespoke layer no OSS provides.
- **Teleon backend** — composes with orchestration/durable-execution/optimizer/eval/sandbox OSS
  in `POSITIONING-AUDIT.md §6` (LangGraph/Temporal as execution backends, DSPy-style candidate
  generation, E2B/Daytona sandboxes, LangSmith/Arize sinks). Eval-gated promotion + bounded
  self-adaptation is the bespoke layer.

---

## Why this matters
1. **Credibility:** the family isn't inventing receipts/provenance/risk from nothing — it's
   applying the **Linux Foundation / OpenSSF / OWASP** supply-chain stack to AI artifacts.
2. **Buildability:** every hub backend has a vendor-neutral OSS substrate; the bespoke value is
   the *governance layer on top*, not re-building registries or signing.
3. **Positioning reinforcement:** "discovery is not trust", "conformance", "evidence not
   authority", "AIBOM" are not marketing inventions — they're the established language of
   software supply-chain security, which buyers in regulated industries already trust.

## Built — "Built on open standards" section (shipped)
The `makeHub` template now renders a **"Built on the open supply-chain stack."** section on
every hub landing, driven by an optional `standards` config (with an accurate shared default).
Tailored per hub where the backend differs: **OpenMCPHub** (MCP registry · MCPTox · install
profiles), **OpenBenchmarkHub** (lm-evaluation-harness · Inspect · in-toto), **OpenCompressionHub**
(LLMLingua · fidelity eval packs). The other hubs use the default (Sigstore · SLSA+in-toto ·
CycloneDX AI-BOM · OpenSSF Scorecard · JSON Schema · SemVer). One edit, all seven hubs.


---

## Per-registry backend contract (prototype → production)

The prototypes mock all of this. Production must provide, **per registry** (on the shared
open supply-chain stack — Sigstore·Rekor / in-toto·SLSA / CycloneDX AI-BOM / OpenSSF Scorecard /
JSON Schema / SemVer):

| Registry | Backend it needs beyond the common registry CRUD + search + signing |
|---|---|
| **All OpenHubForAI registries** (common) | Entry CRUD + facet search, JSON-Schema validation per entry, semver + changelog, cosign signature + Rekor log, in-toto/SLSA provenance, CycloneDX AI-BOM, OpenSSF-Scorecard risk score, account layer (auth/keys/team/billing/usage/audit). |
| **OpenSkillToTool** | The convert pipeline: skill-spec → typed JSON-Schema I/O **contract inference**, least-privilege **scope binding**, a **determinism harness** (N runs → identical shape) + **eval-pack replay** with a parity gate, then sign + publish. Plus the tool **runtime** over MCP **and** HTTP with scope enforcement at call time. (`os2t-pages.jsx` is the UI spec.) |
| **OpenReviewHub** | A **review runner**: clean-clone build, re-run released evals, reproduce reported metrics; produce the claim→evidence→verdict ledger + axis scorecard. Signed, scoped review records. (`orh-pages.jsx` is the UI spec.) |
| **OpenEndpointHub** | Endpoint probing + a **data-class × jurisdiction eligibility** policy engine; gateway routing that emits the `ModelInvocationReceipt` (see Shared Inference Gateway); quarantine of shared-key/bypass endpoints. |
| **OpenSandboxHub** | A **conformance + escape-test** runner per sandbox image (isolation class, egress policy); risk scoring; quarantine on a failed test. |
| **OpenEnvHub** | An **environment runner** (task world + state + tools) and a **reward-spec** evaluator producing reproducible, pinned eval records. |
| **OpenAgentHub** | **Bounded runtime adapters** (declared loop, step/timeout caps) over the common frameworks, emitting a signed **run receipt per step**; scope enforcement at the tool boundary. |
| **OpenReceiptHub** | The **receipt store + verification API**: cosign signing, Rekor transparency log, chained provenance, C2PA portability; `verify` returns the verified chain. The other registries' receipts land here. |
| **OpenStateHub** | A **durable state store** (event-sourced / CRDT) with provenance on every write, scoped read/write, and **snapshot pin + fork + replay**. |
| **OpenTemplatesHub** | A **template instantiation engine** (schema/runtime/resource/API-UI/inference/PurposeTask families) emitting signed instantiation receipts. |

**Private-first enforcement:** the prototype only hides the "Private preview" banner client-side.
Production must enforce `status:'private'` **server-side** (no public read until the
`openTrigger` fires and the entity flips to `status:'live'`).
