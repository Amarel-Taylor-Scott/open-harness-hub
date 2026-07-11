"""adapters/source — local-fixture SourceAdapters (markdown vault, local folder batch).

These adapters satisfy the EXISTING ``scripts.ingest.source_adapters.SourceAdapter`` Protocol
(attrs ``source_type`` / ``parser_provider``; method ``ingest(payload, *, tenant_id, source_id,
scope, authority) -> dict``) and reuse its governed artifact helpers (``_artifact`` /
``_base_handle`` / ``_decompose_field``) so every fetched object becomes a governed source
artifact on the SAME ledger path — no raw source becomes truth, no second runtime. See the
layer README + _repos/shared-backend-components/architecture/project_spine.json for what belongs here.
"""
