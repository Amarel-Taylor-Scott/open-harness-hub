# DeepRepo GitHub intake + reference-architecture consideration — 2026-06-18

> **Source.** The owner relayed GitHub repos posted to the "DeepRepo" Facebook feed
> (facebook.com/DeepRepo) plus a ChatGPT-authored worker/parser/context-platform architecture essay.
> Facebook itself is NOT scrapeable (login wall + ToS); we worked from the URLs the owner pasted.
> **Governance frame:** DISCOVERY ≠ TRUST. Every external repo here is assessed as a *candidate* from
> public metadata only — nothing was cloned, executed, or pip/cargo/npx-installed. Intake is never
> auto-active. The capability-lift bar (must let the model do something it can't alone AND be structural)
> gates everything; off-thesis items are named, not deep-dived (negative-space discipline).
> Method: an 18-agent workflow (12 repo assessments + 6 architecture-slice gap analyses vs the real code),
> plus 4 repos assessed earlier (IAGA-Sentinel, Kaelio/ktx, AutoScientists, OpenSearch-VL).

## 1. The headline: the receipts rail is now contested by OPEN players — the wedge still holds
Three of the 16 repos are tamper-evident **execution-receipt** layers, two of them open-source:
- **IAGA-Sentinel** (Rust, 152★) — Ed25519+Merkle receipts mapped to EU AI Act Art.12/Annex IV; Dictum
  policy DSL with egress allowlisting + PII detection; `is_authoritative:false` honesty. Closest competitor
  on BOTH the receipt rail AND egress governance. (Recorded in `agent-governance-landscape-2026-06-13.md`.)
- **akmon / AGEF** (Rust, 28★) — offline-verifiable-with-`openssl` signed evidence chain; explicitly
  "proves integrity, not semantic correctness," with a signed full-vs-structural capture level to prevent
  overclaiming completeness.
- (Plus the closed players already tracked: Attested Intelligence, Fetch.ai AEVS, Diagrid, NexArt.)

**They all sign EXECUTION (what an agent DID). None govern TRUTH** (promote/reject/revoke a FACT by earned
source authority + CDC on a regulated beachhead). The wedge is intact but the white space is filling fast —
keep leading with "we govern what becomes true, not just sign what happened," and treat their receipts as a
candidate *evidence input* behind a port, never our truth authority. Convergent honesty (`is_authoritative:
false` ≈ our `serves_truth:false`) validates the category. **Re-verify quarterly.**

## 2. Repo intake table (16 repos; discovery ≠ trust)
| Repo | ★ | License | thesis_fit | Action |
|---|---|---|---|---|
| EdoardoBambini/IAGA-Sentinel | 152 | BSL→Apache | competitor/complement (receipts+egress) | competitive-watch; receipt = candidate evidence input behind a port |
| radotsvetkov/akmon | 28 | Apache-2.0 | complement (provenance) | adopt-pattern; consider offline-verifiable (AGEF-shaped) receipt export behind a port |
| Kaelio/ktx | 1.3k | Apache-2.0 | competitor (analytics context) | already cataloged (3 adapter cards) + deep-dived; refresh |
| adithya-s-k/omniparse | 7.6k | GPL-3.0 (weights cc-by-nc-sa, non-commercial >$5M) | candidate-behind-port (parser) | catalog as candidate parser adapter; LICENSE-GATED; never canonical |
| boringdata/boring-semantic-layer | 454 | MIT | candidate-behind-port (semantic layer) | catalog as candidate; adjacent to ktx — safer aggregation, intent-not-SQL |
| quarqlabs/agent-oss | 257 | Apache-2.0 | candidate-behind-port (memory) | candidate memory/recall provider; recall lift is transient |
| Intina47/context-sync | 175 | MIT | complement (memory) | catalog as candidate memory provider; token-cost saver, not truth |
| rizal72/true-mem | 198 | MIT | complement (memory) | adopt-pattern; agent personalization, off our truth thesis |
| mims-harvard/AutoScientists | 653 | n/s | foil (swarm) | candidate bounded-agent behind a port; evidence-only, never executed |
| shawn0728/OpenSearch-VL | 222 | Apache-2.0 | eval-or-data-candidate (multimodal) | out-of-beachhead; GPU/training-gated; metadata-only |
| 917Dhj/DeepPaperNote | 287 | MIT | off-thesis | adopt-pattern only (grounding-lint ≈ our honesty gates) |
| agent0ai/dox | 904 | MIT | off-thesis | ignore (AGENTS.md convention) |
| dbwls99706/ros2-engineering-skills | 104 | Apache-2.0 | off-thesis | ignore (robotics) |
| dockpeek/dockpeek | 1.8k | MIT | off-thesis | ignore (Docker dashboard) |
| FreeCAD/FreeCAD-library | 1.8k | CC-BY-3.0 | off-thesis | ignore (CAD parts) |
| machalliance/standards | 46 | CC-BY-4.0 | off-thesis | ignore (composable-commerce standard) |

## 3. Architecture consideration — the reference essay vs. what we already build
The essay (saved: `.research-notes/deeprepo-architecture-reference-2026-06-18.md`) describes, in large part,
**what this repo already implements**. Gap analysis across 6 slices (evidence-backed against real files):

- **worker-model** — overwhelmingly BUILT + proof-gated ("stateless compute, durable context state" end-to-end:
  WAL-sqlite event-log + job queue + idempotency table + transactional outbox + DLQ + atomic claim + leases).
- **orchestration-scaling** — BUILT, "more rigorous than the reference essay": orchestration/execution split,
  queue-by-workload taxonomy, KEDA+HPA, lifecycle/batch/circuit-breaker policies, cost controls, single-sourced.
- **reconcile-review-promotion** — one of the most mature slices ("in effect, the product"): content-addressed
  receipts, projection-only anti-bypass gates, the LOSSLESS DISTILLATION law, two consistent promotion pipelines.
- **security-governance** — strong: 5 tenant-isolation modes + write-guard, single-source secret redaction +
  leak scan, KMS-envelope metadata, governed egress.
- **serving-context-packs** — substantially built; the gaps below are the demo-relevant ones.
- **parser-portfolio** — the WEAKEST slice: single-engine path is solid + honestly governed (real ParserProvider
  port, Docling adapter that never fakes a parse, deterministic router), but breadth + multi-engine quality are thin.

### Prioritized gap backlog (NEW findings from the essay; owner prioritizes the build items)
> **BUILT 2026-06-18** (parser-portfolio P1 items 1–3 + the P2 candidate adapter cards): `schemas/ParsedDocument.v1.schema.json`
> (the canonical engine-neutral artifact), `scripts/ingest/parse_quality.py` (deterministic quality-worker),
> `scripts/ingest/parse_adjudicator.py` (lossless multi-engine adjudication), and 5 candidate engine seams
> (MinerU/Tika/MarkItDown/GROBID/OmniParse, license + exec-needs gated) in `scripts/ingest/parser_provider.py` —
> all gated by `scripts/check_parser_portfolio.py`. The remaining P1/P2 items below are still open for owner prioritization.

**P1 (demo / correctness relevant):**
1. **Parser:** publish a `ParsedDocument.v1` JSON schema (today the canonical artifact is a Python dataclass tree,
   not a validated schema) → add to `validate_context_schemas.py`.
2. **Parser:** add a deterministic **parse-quality-worker** (text/page coverage, reading-order, table/figure/formula
   fidelity, OCR confidence) to gate publish — currently absent.
3. **Parser:** add a **parse-adjudicator** (run N engines on high-value docs, score, merge/select, keep all outputs
   as evidence under the lossless law) — currently absent.
4. **worker-model:** enforce the **hard poison-job kill** (per-job timeout / memory limit) *inside* the Python worker
   loop — limits are declared in resource classes / K8s mapping but not enforced at runtime.
5. **orchestration:** render **node-pool placement** (nodeSelector/tolerations/resources incl. `nvidia.com/gpu`)
   into the k8s templates from `worker_resource_classes.json` — the data exists, the generator doesn't emit it.
6. **security:** add a **classification ceiling on egress routes** (public/internal/confidential/restricted) so
   `decide_route()` blocks when an intent's data classification exceeds the route's ceiling — overlaps the egress
   work below; today only the LLM lane + restricted reads are guarded.
7. **serving:** a **serving path that reads already-published artifacts + a hot context-pack cache** instead of
   recomputing decompose→verify→optimize on every serve; add `safe_to_answer` + a structured `contested_claims`
   array to the context pack.

**P2:** canonical `make_idempotency_key()` helper; wire the transactional outbox on the live hot path; stamp
`worker_version` on attempts; exponential backoff/retry-after + per-tenant token bucket; extend the parser router's
signal set; add candidate adapter cards for MinerU/Tika/MarkItDown/GROBID/OmniParse + a cloud-DocAI tier; per-tenant
cost-budget ledger that downgrades model tier on breach.

## 4. Recommended candidate intakes (discovery ≠ trust; all behind existing ports)
- **OmniParse** → candidate adapter in the parser_manager slot behind `ParserProviderPort`, **license-gated**
  (GPL-3.0 vs Apache pyproject mismatch; Marker/Surya weights non-commercial above a revenue threshold) and hardened
  (disable Gradio UI, restrict CORS, internal-only, file-size/page/timeout limits, sandbox web crawl). NOT the
  canonical context layer — it produces parsed text/tables/assets; WE own claims/conflict/graph/compression/review.
- **boring-semantic-layer** → candidate behind a semantic-layer port (adjacent to Kaelio/ktx); "intent, not SQL
  correctness" — safer LLM aggregation via validated joins/measures. Metadata-only.
- **context-sync / agent-oss / true-mem** → candidate memory providers (alongside the existing mem0/letta/supermemory
  slots); memory is what an agent BELIEVES, never our verified truth — they ride the memory_provider port, output
  stays candidate context.
- **akmon/AGEF** → consider an offline-`openssl`-verifiable receipt EXPORT format behind the receipt port (we already
  adopt PROV/OpenLineage/WebAnnotation/JSONPatch); their receipt is a strong PROPOSAL our rail can consume, never the
  disposing authority.
- **Google OKF (Open Knowledge Format) v0.1** (added 2026-06-18; surfaced separately by the owner) → candidate
  export/ingest format behind the native-format-preservation port. A hyperscaler standardizing portable,
  git-shippable, markdown+YAML context **validates our TAM** and is a tailwind, not a threat: OKF is the
  *transport*, Baltor/Teleon are the *assurance* on top (OKF has no verification/source-authority/CDC/truth-
  promotion). Ship a governed context pack AS an OKF bundle with our receipts/lineage as the sidecar. Full read:
  the "Format standardization" section of `agent-governance-landscape-2026-06-13.md`.

**Not done here (by design):** no repo was cloned/run; no JSON catalog was force-edited blind (schema-gated — the
OmniParse adapter card is added separately, verified against its proof). Brand/strategy claims unchanged (owner-gated).
