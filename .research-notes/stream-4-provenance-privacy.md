# Stream 4 — Provenance, lineage, privacy & license (research notes)

## Headline recommendations — PROVENANCE / LINEAGE
1. **Emit OpenLineage events** from every pipeline + benchmark run (covers reproducibility, attribution, dataset→model edges in one shot).
2. **Adopt CycloneDX-ML 1.6 (ECMA-424)** as AIBOM format on `harness` + `adapter` + release bundles; pair with Sigstore → SLSA L2 essentially free.
3. **Reframe `attribution` + `provenance` as JSON-LD using PROV-O** (`prov:Entity`/`prov:Activity`/`prov:Agent`, `wasGeneratedBy`, `wasDerivedFrom`, `wasAttributedTo`).

## Headline recommendations — PRIVACY / COMPLIANCE
1. **Replace free-form `privacy_boundaries` with W3C DPV IRIs** (`PersonalDataCategory`, `Purpose`, `LegalBasis`) — unlocks auto-RoPA and AI-Act docs.
2. **Add `eu_ai_act_risk` field** to harness/pipeline schemas (enum: prohibited / high_risk / limited / minimal / gpai). Aug-2026 deadline is imminent.
3. **Codify HIPAA Safe Harbor 18 categories** as a controlled vocab (`hsh:01..hsh:18`) referenced from healthcare `dataset` / `knowledge-pack` / `harness` privacy boundaries.

## Standards table

| Standard | URL | Adoption | Hub mapping | Decision |
|---|---|---|---|---|
| SPDX (v3 incl. AI + Dataset profiles) | spdx.dev | high (ISO 5962, GitHub native) | `license` (already conforms); emit SPDX 3.0 doc per release | already aligned; emit on releases |
| C2PA (v2.1) | c2pa.org | growing fast (Adobe, MS, OpenAI, Sony, Meta) | image/audio/video generation primitives | **emit C2PA manifest** with `c2pa.actions` AI-generated assertion |
| SLSA (v1.0) | slsa.dev | high in OSS supply chain | CI build attestations | emit L2+ in-toto attestations; Sigstore signing |
| CycloneDX (v1.6, ECMA-424) | cyclonedx.org | high; OWASP-backed | cross-cuts harness+adapter+dataset on release | **choose CycloneDX-ML over SPDX-AI** for AIBOM today (tooling maturity) |
| AIBOM convergence | CycloneDX-ML / SPDX 3.0 AI / FSCT | mixed | release bundles | ship CycloneDX-ML now; SPDX 3.0 AI later |
| W3C PROV-O | w3.org/TR/prov-o (2013 Rec) | moderate (research/gov) | `attribution`, `provenance` | use vocabulary in JSON-LD context (low cost, high semantic payoff) |
| MLMD (TFX) | github.com/google/ml-metadata | low; superseded by MLflow/OpenLineage | n/a | skip |
| MLflow | mlflow.org | very high de-facto | `benchmark.run` table 1:1 | emit MLflow runs alongside OpenLineage |
| OpenLineage (v2.0, LF AI&Data) | openlineage.io | high (Airflow/dbt/Spark/Dagster native) | dataset→pipeline→benchmark edges | **emit from every run** (cross-system lineage) |
| DataHub | datahubproject.io | moderate-high enterprise | catalog discovery consumer | not emit, but absorbs OpenLineage + SPDX |
| W3C ODRL (v2.2) | w3.org/TR/odrl-model (2018 Rec) | moderate (IPTC RightsML, EU data spaces, Gaia-X) | `license`+`trust_boundary` policies | SPDX = *what license*; ODRL = *what you may do* — combine |
| W3C DPV (v2.0, 2024) | w3c.github.io/dpv | growing (EU policy / EDPB) | `privacy_boundaries`, dataset anonymization | **replace free-form with DPV IRIs** |
| HIPAA Safe Harbor 18 identifiers | 45 CFR 164.514(b)(2) | mandatory healthcare | healthcare dataset/knowledge-pack/harness | define `hsh:01..hsh:18` controlled vocab |
| GDPR Art. 30 RoPA | EU 2016/679 (no format mandated) | mandatory EU controllers | hub-level export | DPV-annotated catalog auto-generates RoPA |
| NIST Privacy Framework (v1.0; v1.1 draft) | nist.gov/privacy-framework | high US enterprise | governance overlay | map controls to artifacts; no schema |
| ISO/IEC 27701 | iso.org | high enterprise/regulated | org-level | certification, not schema; DPV+RoPA feed evidence |
| EU AI Act (Reg 2024/1689) | eur-lex | law, phased | high-risk dossier | `eu_ai_act_risk` field; Annex IV bundle renderer |
