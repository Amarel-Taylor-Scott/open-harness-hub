# Context-layer openness: OKF + the hyperscaler knowledge/metadata layers — 2026-06-19

> Deep-research sweep (102-agent harness, adversarially verified, all findings `high` confidence) for
> Baltor/Teleon competitive positioning. Question: how open vs. closed are the "context layer" offerings of
> Google/AWS/Databricks/Azure, who is standardizing the FORMAT vs. hoarding the data gravity, and what that
> means for a provider-neutral assurance layer that rides ABOVE them. Fast-moving space — re-verify quarterly.

## 1. Google Open Knowledge Format (OKF) — the format play
- **What/when/who:** Google Cloud, **2026-06-12, OKF v0.1, Apache-2.0**, by data leads Sam McVeety & Amir
  Hormati. A deliberately minimal, vendor-neutral **FORMAT** (explicitly "not another knowledge service"):
  a directory of plain UTF-8 **markdown files with YAML frontmatter**, one concept per file (table/dataset/
  API/metric/runbook), cross-linked via markdown links into a knowledge graph. Only `type` is **required**;
  `title`/`description`/`resource`/`tags`/`timestamp` are recommended/queryable; arbitrary keys allowed.
  Reserved files: optional `index.md` (progressive disclosure) + `log.md` (change history). *"If you can `cat`
  a file, you can read OKF; if you can `git clone` a repo, you can ship it."*
- **Motivation (anti-lock-in, in Google's words):** agent knowledge is fragmented across "metadata catalogs
  with their own APIs, wikis, code comments, and the heads of a few senior engineers," and "many incompatible
  conventions are emerging." Google's stated rationale: *"the value of a knowledge format comes from how many
  parties speak it, not from who owns it."* Design principle #3 is literally **"Format, not platform."**
- **Reference implementations (Apache-2.0, on GitHub):** a **BigQuery Enrichment Agent** (built on Google's
  Agent Development Kit + Gemini, two-pass: BQ-metadata → OKF, then refinement) and a **static HTML visualizer**.
- **Adoption (the strategic tell):** Google updated its own **Knowledge Catalog (Dataplex / Data Cloud) to
  natively ingest OKF** the same day — i.e. Google open-sourced the *format* and kept the paid *consumption/
  serving* layer. **Unsettled:** no neutral foundation/registry, **no second catalog vendor adopting OKF yet**,
  and it is an explicitly-labeled **v0.1 DRAFT** — "single-vendor invitation," not yet a governed industry standard.
- Source: `GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md`, cloud.google.com/blog/.../open-knowledge-format.

## 2. Openness matrix — FORMAT axis vs DATA-GRAVITY axis
The consistent pattern: **open at the FORMAT/edges, proprietary at the consumption/serving/identity layer** (where the moat + monetization live).

| Platform | Open at the FORMAT layer? | Open standards adopted | Where the lock-in lives |
|---|---|---|---|
| **Google Cloud** | **YES — uniquely** (OKF, Apache-2.0, vendor-neutral) | OKF; MCP | Knowledge Catalog/Dataplex is the native ingest+serving product + monetization; only Google reads OKF (mid-June 2026) |
| **AWS** (Bedrock Knowledge Bases) | **NO — most closed on format** (a managed RAG *service* to ground AI on "your proprietary data"; no open knowledge format) | MCP (tool access); choice of vector store (Pinecone/pgvector/OpenSearch/S3 Vectors) | proprietary ingestion/parsing/config + managed retrieval (embeddings, re-rank, vector store) — non-portable |
| **Databricks** | **most open on the TABLE/CATALOG axis** | **Unity Catalog OSS (Apache-2.0) + Open APIs**; **Delta "catalog commits"** (open protocol, delta-io #4381); cross-engine writes from Spark/Flink/DuckDB | core-open/managed-proprietary split (managed lineage, Catalog Explorer, Predictive Optimization, credential vending stay proprietary); **UC remains the brokering AUTHORITY** (data gravity); external-write-to-managed-Delta is BETA; managed-Iceberg more locked |
| **Microsoft Azure** (Fabric/OneLake + Purview) | **open at multiple edges, proprietary at the control plane** | **MCP** (OneLake transport — MS calls it "an open standard"); **Delta Parquet** at rest; **OpenLineage → Apache Atlas REST** (Purview Data Map model+API *are* Atlas) | Entra ID identity/RBAC; Fabric Core MCP server (closed-source preview); Purview catalog/governance control plane; Import-mode/VertiPaq + native KQL storage proprietary by default |

## 3. Strategic synthesis — the white space ABOVE all of them
1. **Only Google is standardizing a knowledge FORMAT in the open (OKF). ALL FOUR hoard the data gravity** at the
   consumption/serving/identity layer (Knowledge Catalog · managed RAG · UC brokering authority · Entra/Purview).
2. Each adopts open standards **only where it does not threaten the serving moat** — MCP (transport, everywhere),
   OpenLineage+Atlas (Azure lineage), Delta catalog-commits + UC-OSS (Databricks tables), Delta Parquet at rest.
3. **NONE of these open standards or platform catalogs provide continuous VERIFICATION, portable RECEIPTS, or
   governed truth-PROMOTION.** OKF standardizes the *container*, not whether the content is true/current/provable.
4. **The positioning, sharpened:** *"They standardize (or hoard) where context LIVES; Baltor governs whether
   it's TRUE."* A provider-neutral assurance layer should **consume** the open inputs (OKF, OpenLineage, Apache
   Iceberg/Atlas, Delta catalog-commits, Unity Catalog OSS, MCP) as portable substrate, and **differentiate
   precisely where every platform is weakest — continuous verification, earned source authority, CDC/revocation,
   portable receipts, and governed truth-promotion — riding ABOVE any one platform** rather than competing on
   data movement, catalogs, or serving. (This is also why **adopting OKF as a Baltor export/ingest format** —
   already flagged — is pure upside: it rides the one open format while we own the assurance the format lacks.)

## Sources
- OKF: `github.com/GoogleCloudPlatform/knowledge-catalog/.../okf/SPEC.md` · cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/
- AWS: aws.amazon.com/bedrock/knowledge-bases/ · Databricks: databricks.com/blog/expanded-interoperability-unity-catalog-open-apis · github.com/unitycatalog/unitycatalog · delta.io
- Azure: learn.microsoft.com/.../onelake-local-mcp · openlineage.io/blog/openlineage-microsoft-purview/ · github.com/microsoft/Purview-ADB-Lineage-Solution-Accelerator
- Cross-checked against `archive/legacy/docs/research/agent-governance-landscape-2026-06-13.md` + `deeprepo-github-intake-2026-06-18.md` (OKF intake). Full verified findings: deep-research run wf_55104597.
