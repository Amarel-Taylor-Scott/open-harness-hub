"""Baltor Pipeline Runtime — versioned, swappable, durable processing pipelines.

CFPB ingestion is no longer "the architecture"; it is the first registered pipeline
(`cfpb_structured_ingest@v1`). Pipelines are manifests, processors are swappable plugins, runs are
durable ledger records, artifacts are content-addressed. See `docs/architecture/pipeline-runtime.md`.
"""
